from types import TracebackType
from typing import Self

import psycopg
import pytest
from scripts import wait_for_postgres as waiter


class ConnectionContext:
    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exception_type, exception, traceback


def test_wait_retries_until_postgres_accepts_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection_urls: list[str] = []

    def connect(database_url: str, *, connect_timeout: int) -> ConnectionContext:
        assert connect_timeout == 3
        connection_urls.append(database_url)
        if len(connection_urls) == 1:
            raise psycopg.OperationalError
        return ConnectionContext()

    monkeypatch.setattr("scripts.wait_for_postgres.psycopg.connect", connect)
    monkeypatch.setattr("scripts.wait_for_postgres.time.sleep", lambda _seconds: None)

    waiter.wait_for_postgres(
        "postgresql+psycopg://relay:secret@localhost:5432/relay",
        timeout_seconds=5,
    )

    assert connection_urls == [
        "postgresql://relay:secret@localhost:5432/relay",
        "postgresql://relay:secret@localhost:5432/relay",
    ]


def test_wait_times_out_without_exposing_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    def reject_connection(_database_url: str, *, connect_timeout: int) -> None:
        assert connect_timeout == 3
        raise psycopg.OperationalError

    monotonic_values = iter((0.0, 2.0))
    monkeypatch.setattr("scripts.wait_for_postgres.psycopg.connect", reject_connection)
    monkeypatch.setattr(
        "scripts.wait_for_postgres.time.monotonic",
        lambda: next(monotonic_values),
    )

    with pytest.raises(TimeoutError, match="within 1 seconds") as error:
        waiter.wait_for_postgres(
            "postgresql+psycopg://relay:secret@localhost:5432/relay",
            timeout_seconds=1,
        )

    assert "secret" not in str(error.value)
