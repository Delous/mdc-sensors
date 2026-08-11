import asyncpg


async def init_db(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as connection:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS measurements (
                id BIGSERIAL PRIMARY KEY,
                ts TIMESTAMPTZ NOT NULL,
                payload JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );

            CREATE INDEX IF NOT EXISTS idx_measurements_id
                ON measurements (id);

            CREATE INDEX IF NOT EXISTS idx_measurements_created_at
                ON measurements (created_at);
            """
        )
