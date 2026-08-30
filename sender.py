import asyncio

import aiohttp

from config import Settings
from db.repository import Measurement, MeasurementRepository


def prepare_request(
    measurements: list[Measurement],
) -> tuple[dict[str, list[str]], list[Measurement]]:
    payload: dict[str, list[str]] = {}
    sent_rows: list[Measurement] = []

    for measurement in measurements:
        ts_key = str(int(measurement.ts.timestamp()))
        if ts_key in payload:
            continue

        payload[ts_key] = measurement.payload
        sent_rows.append(measurement)

    return payload, sent_rows


async def send_http_periodically(
    settings: Settings,
    repository: MeasurementRepository,
) -> None:
    delay = settings.send_interval_seconds
    timeout = aiohttp.ClientTimeout(total=settings.http_timeout_seconds)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        while True:
            await asyncio.sleep(delay)

            rows = await repository.load_batch_for_send(settings.send_batch_size)
            if not rows:
                delay = settings.send_interval_seconds
                continue

            data_for_request, sent_rows = prepare_request(rows)

            try:
                async with session.post(
                    settings.api_url,
                    json=data_for_request,
                ) as response:
                    response_text = await response.text()

                    if 200 <= response.status < 300:
                        await repository.delete_sent_measurements(
                            [row.id for row in sent_rows],
                        )
                        delay = settings.send_interval_seconds
                        print(f"POST sent. Records: {len(sent_rows)}")
                        continue

                    print(
                        "POST failed. "
                        f"Status: {response.status}, response: {response_text}"
                    )
            except Exception as exc:
                print(f"POST error: {exc}")

            await asyncio.sleep(delay)
            delay = min(
                delay * 2,
                settings.failed_send_max_delay_seconds,
            )
