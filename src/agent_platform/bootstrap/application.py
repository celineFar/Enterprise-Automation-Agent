from agent_platform.bootstrap.container import ApplicationContainer
from agent_platform.config.settings import ApiSettings, WorkerSettings
from agent_platform.persistence.database import DatabaseRuntime


def create_application_container[RuntimeSettingsT: ApiSettings | WorkerSettings](
    settings: RuntimeSettingsT,
    database: DatabaseRuntime,
) -> ApplicationContainer[RuntimeSettingsT]:
    """Compose the process dependencies from validated settings and owned resources."""

    return ApplicationContainer(settings=settings, database=database)
