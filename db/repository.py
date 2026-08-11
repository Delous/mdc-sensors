from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import delete, desc, select

from db.schema import MeasurementRecord
from db.session import session_context


@dataclass(frozen=True)
class Measurement:
    id: int
    ts: datetime
    payload: list[str]


class MeasurementRepository:
    def __init__(self, max_queue_rows: int):
        self._max_queue_rows = max_queue_rows

    async def save_measurement(self, ts: datetime, payload: list[str]) -> None:
        async with session_context() as session:
            session.add(MeasurementRecord(ts=ts, payload=payload))

    async def prune_old_measurements(self) -> None:
        if self._max_queue_rows <= 0:
            return

        ids_to_delete = (
            select(MeasurementRecord.id)
            .order_by(desc(MeasurementRecord.id))
            .offset(self._max_queue_rows)
        )

        async with session_context() as session:
            await session.execute(
                delete(MeasurementRecord).where(
                    MeasurementRecord.id.in_(ids_to_delete),
                )
            )

    async def load_batch_for_send(self, batch_size: int) -> list[Measurement]:
        query = (
            select(MeasurementRecord)
            .order_by(MeasurementRecord.id)
            .limit(batch_size)
        )

        async with session_context() as session:
            records = (await session.scalars(query)).all()

        return [
            Measurement(
                id=record.id,
                ts=record.ts,
                payload=record.payload,
            )
            for record in records
        ]

    async def delete_sent_measurements(self, ids: list[int]) -> None:
        if not ids:
            return

        async with session_context() as session:
            await session.execute(
                delete(MeasurementRecord).where(MeasurementRecord.id.in_(ids))
            )
