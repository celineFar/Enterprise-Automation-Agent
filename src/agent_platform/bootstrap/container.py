from dataclasses import dataclass

from agent_platform.config.settings import ApiSettings, WorkerSettings
from agent_platform.persistence.database import DatabaseRuntime


@dataclass(frozen=True, slots=True)
class ApplicationContainer[RuntimeSettingsT: ApiSettings | WorkerSettings]:
    """Process-scoped dependencies assembled by the bootstrap composition root.

    Repository and adapter factories will be added as typed fields when their
    contracts are introduced. Consumers should receive their narrow dependencies
    through constructor injection rather than use this container as a service locator.
    """

    settings: RuntimeSettingsT
    database: DatabaseRuntime
