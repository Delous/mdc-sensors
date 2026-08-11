import asyncio

from config import load_settings
from db.repository import MeasurementRepository
from db.schema import init_db
from db.session import close_db_engine, engine
from sender import send_http_periodically
from serial_reader import read_serial_periodically


async def init_db_with_retry() -> None:
    while True:
        try:
            await init_db(engine)
            return
        except Exception as exc:
            print(f"PostgreSQL is unavailable: {exc}")
            await asyncio.sleep(3)


async def serial_to_http() -> None:
    settings = load_settings()
    await init_db_with_retry()
    repository = MeasurementRepository(settings.max_queue_rows)

    try:
        await asyncio.gather(
            read_serial_periodically(settings, repository),
            send_http_periodically(settings, repository),
        )
    finally:
        await close_db_engine()


if __name__ == "__main__":
    asyncio.run(serial_to_http())
