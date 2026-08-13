from collections.abc import Iterator

import pytest
from docker.errors import DockerException  # type: ignore[import-untyped]
from testcontainers.community.postgres import PostgresContainer

from agent_platform.config.settings import ApiSettings, WorkerSettings


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    """Provide one disposable PostgreSQL instance for the integration suite."""

    try:
        postgres = PostgresContainer("postgres:17.6-bookworm", driver="psycopg")
        postgres.start()
    except DockerException as error:
        pytest.skip(f"Docker is unavailable: {error}")

    try:
        yield postgres.get_connection_url()
    finally:
        postgres.stop()


@pytest.fixture
def api_settings(postgres_url: str, monkeypatch: pytest.MonkeyPatch) -> ApiSettings:
    set_role_environment(monkeypatch, postgres_url, role="api")
    return ApiSettings()


@pytest.fixture
def worker_settings(postgres_url: str, monkeypatch: pytest.MonkeyPatch) -> WorkerSettings:
    set_role_environment(monkeypatch, postgres_url, role="worker")
    return WorkerSettings()


def set_role_environment(
    monkeypatch: pytest.MonkeyPatch,
    postgres_url: str,
    *,
    role: str,
) -> None:
    values = {
        "AGENT_APPLICATION__ENVIRONMENT": "test",
        "AGENT_APPLICATION__DEPLOYMENT_ID": f"integration-{role}",
        "AGENT_BUILD__VERSION": "0.1.0-test",
        "AGENT_BUILD__COMMIT_SHA": "integration",
        "AGENT_BUILD__IMAGE_DIGEST": "sha256:integration",
        "AGENT_DATABASE__URL": postgres_url,
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)
