from typing import Annotated, Self

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    PostgresDsn,
    SecretStr,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from agent_platform.config.types import Environment, LogLevel

PositiveInt = Annotated[int, Field(gt=0)]
NonNegativeInt = Annotated[int, Field(ge=0)]
Port = Annotated[int, Field(ge=1, le=65_535)]


class StrictConfigModel(BaseModel):
    """Base for nested settings sections with strict field names."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class ApplicationSettings(StrictConfigModel):
    name: str = "relay-agent-platform"
    environment: Environment
    deployment_id: str
    log_level: LogLevel = LogLevel.INFO


class BuildSettings(StrictConfigModel):
    version: str
    commit_sha: str
    image_digest: str


class DatabaseSettings(StrictConfigModel):
    url: SecretStr
    pool_size: PositiveInt = 5
    max_overflow: NonNegativeInt = 5
    pool_timeout_seconds: PositiveInt = 30

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: SecretStr) -> SecretStr:
        try:
            dsn = PostgresDsn(value.get_secret_value())
        except ValidationError:
            raise ValueError("url must be a valid PostgreSQL connection URL") from None

        if dsn.scheme != "postgresql+psycopg":
            raise ValueError("url must use the postgresql+psycopg driver")
        if dsn.path in (None, "", "/"):
            raise ValueError("url must include a database name")

        return value


class TelemetrySettings(StrictConfigModel):
    enabled: bool = False
    otlp_endpoint: AnyUrl | None = None
    otlp_insecure: bool = False

    @model_validator(mode="after")
    def require_endpoint_when_enabled(self) -> Self:
        if self.enabled and self.otlp_endpoint is None:
            raise ValueError("otlp_endpoint is required when telemetry is enabled")
        return self


class ApiRuntimeSettings(StrictConfigModel):
    host: str = "0.0.0.0"  # noqa: S104 - API containers must accept external traffic.
    port: Port = 8000
    workers: PositiveInt = 1


class WorkerRuntimeSettings(StrictConfigModel):
    poll_interval_seconds: PositiveInt = 1
    shutdown_grace_period_seconds: PositiveInt = 30


class AgentBaseSettings(BaseSettings):
    """Common environment-variable convention for all runtime roles."""

    model_config = SettingsConfigDict(
        env_prefix="AGENT_",
        env_nested_delimiter="__",
        extra="forbid",
        hide_input_in_errors=True,
    )


class ApiSettings(AgentBaseSettings):
    application: ApplicationSettings
    build: BuildSettings
    database: DatabaseSettings
    telemetry: TelemetrySettings = Field(default_factory=TelemetrySettings)
    api: ApiRuntimeSettings = Field(default_factory=ApiRuntimeSettings)


class WorkerSettings(AgentBaseSettings):
    application: ApplicationSettings
    build: BuildSettings
    database: DatabaseSettings
    telemetry: TelemetrySettings = Field(default_factory=TelemetrySettings)
    worker: WorkerRuntimeSettings = Field(default_factory=WorkerRuntimeSettings)


class MigrationSettings(AgentBaseSettings):
    database: DatabaseSettings
