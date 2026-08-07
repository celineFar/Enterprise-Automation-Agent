# Release 0 Phase 1 Checklist

### Checklist

- [x]  Create the FastAPI application.
- [x]  Create separate API and worker entry points.
- [x]  Add Pydantic configuration models.
- [x]  Add environment-specific configuration.
- [ ]  Add dependency injection for repositories and adapters.
- [x]  Add linting, formatting, typing, and unit-test commands.
- [ ]  Add pre-commit hooks.
- [ ]  Add container builds.
- [ ]  Add health and readiness endpoints.
- [ ]  Add build, commit, image, and environment metadata.
- [ ]  Add database migration tooling.
- [x]  Add local Docker Compose dependencies.
- [ ]  Add CI validation for migrations.
- [ ]  Add CI validation for event schemas.
- [ ]  Add CI secret scanning.
- [ ]  Add dependency and container vulnerability scanning.
- [ ]  Add staging deployment pipeline.
- [ ]  Prevent direct production deployment outside the controlled pipeline.

### Exit gate

- [ ]  API and worker start independently.
- [ ]  Both connect to PostgreSQL.
- [ ]  A migration can be applied and rolled back in a disposable environment.
- [ ]  Build and deployment metadata appear in application telemetry.
- [ ]  Local development can start from a documented command.
