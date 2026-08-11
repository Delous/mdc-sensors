import asyncio

import asyncpg

from config import load_settings
from db_repository import MeasurementRepository
from db_schema import init_db
from sender import send_http_periodically
from serial_reader import read_serial_periodically


async def create_pool_with_retry(settings):
    while True:
        try:
            return await asyncpg.create_pool(
                dsn=settings.database_url,
                min_size=settings.db_pool_min_size,
                max_size=settings.db_pool_max_size,
            )
        except Exception as exc:
            print(f"PostgreSQL is unavailable: {exc}")
            await asyncio.sleep(3)


async def serial_to_http() -> None:
    settings = load_settings()
    pool = await create_pool_with_retry(settings)

    async with pool:
        await init_db(pool)
        repository = MeasurementRepository(pool, settings.max_queue_rows)

        await asyncio.gather(
            read_serial_periodically(settings, repository),
            send_http_periodically(settings, repository),
        )


if __name__ == "__main__":
    asyncio.run(serial_to_http())
