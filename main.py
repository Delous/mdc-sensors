import asyncio
import json
import aiohttp
import aiosqlite
import serial_asyncio
from datetime import datetime, UTC


PORT = '/dev/ttyUSB0'
# API_URL = "https://proka-bel.ru/api/v1/values"
API_URL = "https://proka-bel.ru/api/v1/values"
DB_PATH = "measurements.db"

SEND_INTERVAL_SECONDS = 5
HTTP_TIMEOUT_SECONDS = 10


def parse_serial_line(raw_line: bytes) -> tuple[int, list[str]]:
    """
    Возвращает:
    ts — timestamp в секундах UTC
    payload — список значений после addrSens
    """
    ts = int(datetime.now(UTC).timestamp())

    payload = []
    lines = raw_line.strip(b'\r\n').decode().split('\r')

    for line in lines:
        if not line.startswith("addrSens"):
            continue

        payload.append(line.replace('addrSens ', ''))

    return ts, payload


async def init_db(db: aiosqlite.Connection):
    await db.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            ts INTEGER PRIMARY KEY,
            payload TEXT NOT NULL
        );
    """)

    # WAL обычно лучше для сценария "одна корутина пишет, другая периодически читает/удаляет".
    await db.execute("PRAGMA journal_mode=WAL;")

    await db.commit()


async def save_measurement(
    db: aiosqlite.Connection,
    ts: int,
    payload: list[str],
):
    """
    Записывает измерение в SQLite.

    Если запись с таким ts уже есть, она будет перезаписана.
    payload храним как JSON-строку.
    """

    payload_json = json.dumps(payload, ensure_ascii=False)

    await db.execute(
        """
        INSERT INTO measurements (ts, payload)
        VALUES (?, ?)
        ON CONFLICT(ts) DO UPDATE SET
            payload = excluded.payload;
        """,
        (ts, payload_json)
    )

    await db.commit()


async def read_serial(db: aiosqlite.Connection):
    """
    Постоянно читает serial-порт и сразу сохраняет данные в SQLite.
    HTTP-запросами эта корутина не занимается.
    """

    while True:
        try:
            reader, _ = await serial_asyncio.open_serial_connection(
                url=PORT,
                baudrate=115200
            )

            print(f'Подключились к порту {PORT}')

        except Exception:
            print(f'К порту {PORT} ничего не подключено')
            await asyncio.sleep(5)
            continue

        while True:
            try:
                line = await reader.readline()

                if not line:
                    print('Пришла пустая строка')
                    continue

                ts, payload = parse_serial_line(line)

                print(ts, payload)

                await save_measurement(db, ts, payload)

            except Exception as e:
                print(f"Ошибка чтения serial: {e}")
                break


async def load_measurements_for_send(
    db: aiosqlite.Connection,
) -> list[tuple[int, str]]:
    """
    Загружает все накопленные записи.

    Возвращаем именно список пар (ts, payload_json), потому что после успешной
    отправки будем удалять только те строки, которые реально отправили.
    """

    cursor = await db.execute(
        """
        SELECT ts, payload
        FROM measurements
        ORDER BY ts;
        """
    )

    rows = await cursor.fetchall()
    await cursor.close()

    return rows


async def delete_sent_measurements(
    db: aiosqlite.Connection,
    rows: list[tuple[int, str]],
):
    """
    Удаляет успешно отправленные записи.

    Важно: удаляем по ts И payload.

    Почему не только по ts:
    пока POST-запрос выполнялся, могла прийти новая строка с тем же ts,
    и она могла перезаписать старую запись. Если удалить только по ts,
    можно случайно удалить более новую запись.
    """

    await db.executemany(
        """
        DELETE FROM measurements
        WHERE ts = ? AND payload = ?;
        """,
        rows
    )

    await db.commit()


async def send_http_periodically(db: aiosqlite.Connection):
    """
    Каждые SEND_INTERVAL_SECONDS секунд берёт данные из SQLite,
    отправляет их на сервер и после успешной отправки удаляет.
    """

    async with aiohttp.ClientSession() as session:
        while True:
            await asyncio.sleep(SEND_INTERVAL_SECONDS)

            rows = await load_measurements_for_send(db)

            if not rows:
                continue

            data_for_request = {
                ts: json.loads(payload_json)
                for ts, payload_json in rows
            }

            try:
                async with session.post(
                    API_URL,
                    json=data_for_request,
                    timeout=HTTP_TIMEOUT_SECONDS
                ) as response:
                    status = response.status
                    result_text = await response.text()

                    if status == 200:
                        print(
                            f"POST отправлен. "
                            f"Записей: {len(data_for_request)}"
                        )

                        await delete_sent_measurements(db, rows)

                    else:
                        print(
                            f"Ошибка запроса. "
                            f"Статус: {status}, "
                            f"Текст ответа: {result_text}"
                        )

            except Exception as e:
                print(f"Ошибка POST: {e}")


async def serial_to_http():
    async with aiosqlite.connect(DB_PATH) as db:
        await init_db(db)

        await asyncio.gather(
            read_serial(db),
            send_http_periodically(db),
        )


if __name__ == "__main__":
    asyncio.run(serial_to_http())
