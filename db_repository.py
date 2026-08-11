from dataclasses import dataclass
from datetime import datetime
import json

import asyncpg


@dataclass(frozen=True)
class Measurement:
    id: int
    ts: datetime
    payload: list[str]


class MeasurementRepository:
    def __init__(self, pool: asyncpg.Pool, max_queue_rows: int):
        self._pool = pool
        self._max_queue_rows = max_queue_rows

    async def save_measurement(self, ts: datetime, payload: list[str]) -> None:
        payload_json = json.dumps(payload, ensure_ascii=False)

        async with self._pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO measurements (ts, payload)
                VALUES ($1, $2::jsonb);
                """,
                ts,
                payload_json,
            )

    async def prune_old_measurements(self) -> None:
        if self._max_queue_rows <= 0:
            return

        async with self._pool.acquire() as connection:
            await connection.execute(
                """
                DELETE FROM measurements
                WHERE id IN (
                    SELECT id
                    FROM measurements
                    ORDER BY id DESC
                    OFFSET $1
                );
                """,
                self._max_queue_rows,
            )

    async def load_batch_for_send(self, batch_size: int) -> list[Measurement]:
        async with self._pool.acquire() as connection:
            rows = await connection.fetch(
                """
                SELECT id, ts, payload
                FROM measurements
                ORDER BY id
                LIMIT $1;
                """,
                batch_size,
            )

        return [
            Measurement(
                id=row["id"],
                ts=row["ts"],
                payload=json.loads(row["payload"]),
            )
            for row in rows
        ]

    async def delete_sent_measurements(self, ids: list[int]) -> None:
        if not ids:
            return

        async with self._pool.acquire() as connection:
            await connection.execute(
                """
                DELETE FROM measurements
                WHERE id = ANY($1::bigint[]);
                """,
                ids,
            )
