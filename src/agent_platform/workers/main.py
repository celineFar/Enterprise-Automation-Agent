import asyncio
import signal
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from types import FrameType

from agent_platform.config.settings import WorkerSettings

_SHUTDOWN_SIGNALS = (signal.SIGINT, signal.SIGTERM)


@asynccontextmanager
async def worker_lifespan(_settings: WorkerSettings) -> AsyncIterator[None]:
    """Own resources whose lifetime matches the worker process."""

    yield


@contextmanager
def shutdown_signals(stop_event: asyncio.Event) -> Iterator[None]:
    """Translate process termination signals into graceful worker shutdown."""

    previous_handlers = {signum: signal.getsignal(signum) for signum in _SHUTDOWN_SIGNALS}

    def request_shutdown(_signum: int, _frame: FrameType | None) -> None:
        stop_event.set()

    try:
        for signum in _SHUTDOWN_SIGNALS:
            signal.signal(signum, request_shutdown)
        yield
    finally:
        for signum, previous_handler in previous_handlers.items():
            signal.signal(signum, previous_handler)


async def run_worker(
    settings: WorkerSettings | None = None,
    shutdown_event: asyncio.Event | None = None,
    *,
    register_signals: bool = True,
) -> None:
    """Run the worker until an external shutdown is requested."""

    resolved_settings = settings or WorkerSettings()
    stop_event = shutdown_event if shutdown_event is not None else asyncio.Event()

    async with worker_lifespan(resolved_settings):
        if register_signals:
            with shutdown_signals(stop_event):
                await stop_event.wait()
        else:
            await stop_event.wait()


def main() -> None:
    """Start the worker runtime from the command line."""

    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
