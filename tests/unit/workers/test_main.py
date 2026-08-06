import asyncio
import signal
from collections.abc import Callable, Iterator
from types import FrameType

import pytest
from pydantic import ValidationError

from agent_platform.config.settings import WorkerSettings
from agent_platform.workers import main as worker_main

SignalHandler = Callable[[int, FrameType | None], None] | int


@pytest.fixture
def worker_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    values = {
        "AGENT_APPLICATION__NAME": "relay-test-worker",
        "AGENT_APPLICATION__ENVIRONMENT": "test",
        "AGENT_APPLICATION__DEPLOYMENT_ID": "worker-unit-tests",
        "AGENT_BUILD__VERSION": "0.1.0-test",
        "AGENT_BUILD__COMMIT_SHA": "abc123",
        "AGENT_BUILD__IMAGE_DIGEST": "sha256:test",
        "AGENT_DATABASE__URL": "postgresql+psycopg://relay:secret@localhost:5432/relay",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)

    yield


def test_worker_runs_until_shutdown_is_requested(worker_environment: None) -> None:
    async def scenario() -> None:
        stop_event = asyncio.Event()
        task = asyncio.create_task(
            worker_main.run_worker(
                WorkerSettings(),
                stop_event,
                register_signals=False,
            )
        )
        await asyncio.sleep(0)

        assert not task.done()

        stop_event.set()
        await task

        assert task.done()

    asyncio.run(scenario())


def test_worker_fails_fast_when_configuration_is_missing(
    worker_environment: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AGENT_DATABASE__URL")

    async def scenario() -> None:
        with pytest.raises(ValidationError):
            await worker_main.run_worker(register_signals=False)

    asyncio.run(scenario())


def test_shutdown_signal_requests_graceful_stop(monkeypatch: pytest.MonkeyPatch) -> None:
    handlers: dict[signal.Signals, SignalHandler] = {}

    def capture_handler(signum: signal.Signals, handler: SignalHandler) -> SignalHandler:
        handlers[signum] = handler
        return signal.SIG_DFL

    monkeypatch.setattr(signal, "getsignal", lambda _signum: signal.SIG_DFL)
    monkeypatch.setattr(signal, "signal", capture_handler)
    stop_event = asyncio.Event()

    with worker_main.shutdown_signals(stop_event):
        handler = handlers[signal.SIGTERM]
        assert callable(handler)
        handler(signal.SIGTERM, None)

    assert stop_event.is_set()


def test_main_starts_async_worker(monkeypatch: pytest.MonkeyPatch) -> None:
    started = False

    async def fake_run_worker(
        settings: WorkerSettings | None = None,
        shutdown_event: asyncio.Event | None = None,
        *,
        register_signals: bool = True,
    ) -> None:
        del settings, shutdown_event, register_signals
        nonlocal started
        started = True

    monkeypatch.setattr(worker_main, "run_worker", fake_run_worker)

    worker_main.main()

    assert started
