import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    api_url: str
    database_url: str

    serial_port: str
    serial_baudrate: int

    send_batch_size: int
    max_queue_rows: int

    send_interval_seconds: float
    http_timeout_seconds: float
    failed_send_max_delay_seconds: float


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} environment variable is required")
    return value


def load_settings() -> Settings:
    return Settings(
        api_url=_require_env("API_URL"),
        database_url="sqlite+aiosqlite:////data/measurements.db",

        serial_port="/dev/ttyUSB0",
        serial_baudrate=115200,

        send_batch_size=500,
        max_queue_rows=100000,

        send_interval_seconds=5,
        http_timeout_seconds=10,
        failed_send_max_delay_seconds=60
    )


@lru_cache
def get_settings() -> Settings:
    return load_settings()
