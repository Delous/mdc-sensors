import asyncio
import serial_asyncio

from datetime import UTC, datetime

from config import Settings
from db.repository import MeasurementRepository

PRUNE_EVERY_SAVED_ROWS = 100


def parse_serial_line(raw_line: bytes) -> tuple[datetime, list[str]]:
    ts = datetime.now(UTC)
    payload: list[str] = []

    lines = raw_line.strip(b"\r\n").decode(errors="replace").split("\r")
    for line in lines:
        if line.startswith("addrSens"):
            payload.append(line.replace("addrSens ", ""))

    return ts, payload


async def read_serial_periodically(
    settings: Settings,
    repository: MeasurementRepository,
) -> None:
    while True:
        try:
            reader, writer = await serial_asyncio.open_serial_connection(
                url=settings.serial_port,
                baudrate=settings.serial_baudrate,
            )
            print(f"Connected to serial port {settings.serial_port}")
        except Exception as exc:
            print(f"Serial port {settings.serial_port} is unavailable: {exc}")
            await asyncio.sleep(5)
            continue

        saved_rows = 0

        try:
            while True:
                try:
                    line = await reader.readline()
                    if not line:
                        print("Serial connection closed")
                        break

                    ts, payload = parse_serial_line(line)
                    if not payload:
                        continue

                    await repository.save_measurement(ts, payload)
                    saved_rows += 1
                    if saved_rows >= PRUNE_EVERY_SAVED_ROWS:
                        await repository.prune_old_measurements()
                        saved_rows = 0

                    print(f"Saved measurement: ts={ts.isoformat()}, values={payload}")
                except Exception as exc:
                    print(f"Serial read error: {exc}")
                    break
        finally:
            try:
                writer.close()
                await asyncio.wait_for(writer.wait_closed(), timeout=5)
            except AttributeError:
                pass
            except Exception as exc:
                print(f"Serial close error: {exc}")

        await asyncio.sleep(5)
