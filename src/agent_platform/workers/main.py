import asyncio
import signal
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from types import FrameType

from agent_platform.bootstrap.application import create_application_container
from agent_platform.bootstrap.container import ApplicationContainer
from agent_platform.bootstrap.lifecycle import database_lifespan
from agent_platform.config.settings import WorkerSettings

_SHUTDOWN_SIGNALS = (signal.SIGINT, signal.SIGTERM)


@dataclass(slots=True)
class WorkerResources:
    """Resources and background tasks owned by one worker process."""

    container: ApplicationContainer[WorkerSettings]
    tasks: set[asyncio.Task[None]] = field(default_factory=set)


async def finish_or_cancel_tasks(
    tasks: set[asyncio.Task[None]],
    *,
    timeout_seconds: int,
) -> None:
    """Allow owned tasks to finish, then cancel anything past the grace period."""

    if not tasks:
        return

    _, pending = await asyncio.wait(tasks, timeout=timeout_seconds)
    for task in pending:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    tasks.clear()


@asynccontextmanager
async def worker_lifespan(settings: WorkerSettings) -> AsyncIterator[WorkerResources]:
    """Own resources whose lifetime matches the worker process."""

    async with database_lifespan(settings.database) as database:
        resources = WorkerResources(
            container=create_application_container(settings, database),
        )
        try:
            yield resources
        finally:
            await finish_or_cancel_tasks(
                resources.tasks,
                timeout_seconds=settings.worker.shutdown_grace_period_seconds,
            )


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

    async with worker_lifespan(resolved_settings) as _resources:
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
