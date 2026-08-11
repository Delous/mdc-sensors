import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    serial_port: str
    serial_baudrate: int
    api_url: str
    database_url: str
    send_interval_seconds: float
    http_timeout_seconds: float
    send_batch_size: int
    failed_send_max_delay_seconds: float
    max_queue_rows: int
    db_pool_min_size: int
    db_pool_max_size: int


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value is None else int(value)


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return default if value is None else float(value)


def load_settings() -> Settings:
    return Settings(
        serial_port=os.getenv("SERIAL_PORT", "/dev/ttyUSB0"),
        serial_baudrate=_get_int("SERIAL_BAUDRATE", 115200),
        api_url=os.getenv("API_URL", "https://proka-bel.ru/api/v1/values"),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql://mdc:mdc@postgres:5432/mdc_sensors",
        ),
        send_interval_seconds=_get_float("SEND_INTERVAL_SECONDS", 5),
        http_timeout_seconds=_get_float("HTTP_TIMEOUT_SECONDS", 10),
        send_batch_size=_get_int("SEND_BATCH_SIZE", 500),
        failed_send_max_delay_seconds=_get_float(
            "FAILED_SEND_MAX_DELAY_SECONDS",
            60,
        ),
        max_queue_rows=_get_int("MAX_QUEUE_ROWS", 100000),
        db_pool_min_size=_get_int("DB_POOL_MIN_SIZE", 1),
        db_pool_max_size=_get_int("DB_POOL_MAX_SIZE", 5),
    )
