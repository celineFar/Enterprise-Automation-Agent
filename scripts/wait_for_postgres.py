import argparse
import time

import psycopg

from agent_platform.config.settings import MigrationSettings


def wait_for_postgres(
    database_url: str,
    *,
    timeout_seconds: float = 30,
    interval_seconds: float = 1,
) -> None:
    """Wait until PostgreSQL accepts a connection or the timeout expires."""

    connection_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    deadline = time.monotonic() + timeout_seconds

    while True:
        try:
            with psycopg.connect(connection_url, connect_timeout=3):
                return
        except psycopg.OperationalError:
            if time.monotonic() >= deadline:
                message = f"PostgreSQL did not become ready within {timeout_seconds:g} seconds"
                raise TimeoutError(message) from None
            time.sleep(interval_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wait for the configured PostgreSQL instance")
    parser.add_argument("--timeout-seconds", type=float, default=30)
    parser.add_argument("--interval-seconds", type=float, default=1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = MigrationSettings()
    wait_for_postgres(
        settings.database.url.get_secret_value(),
        timeout_seconds=args.timeout_seconds,
        interval_seconds=args.interval_seconds,
    )


if __name__ == "__main__":
    main()
