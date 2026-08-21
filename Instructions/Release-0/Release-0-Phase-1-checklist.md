# 4. Phase 1 — Repository and platform skeleton
# Release 0 Phase 1 Checklist

### Checklist

* [x] Add linting, formatting, typing, and unit-test commands.
* [ ] Add pre-commit hooks.
* [x] Add Pydantic configuration models.
* [x] Add environment-specific configuration.
* [x] Create the FastAPI application.
* [x] Create separate API and worker entry points.
* [x] Add local Docker Compose dependencies.
* [x] Add database migration tooling.
* [ ] Add CI validation for migrations.
* [ ] Add dependency injection for repositories and adapters.
* [x] Add health and readiness endpoints.
* [ ] Add build, commit, image, and environment metadata.
* [ ] Add container builds.
* [ ] Add CI validation for event schemas.
* [ ] Add CI secret scanning.
* [ ] Add dependency and container vulnerability scanning.
* [ ] Add staging deployment pipeline.
* [ ] Prevent direct production deployment outside the controlled pipeline.

### Exit gate

* [ ] A migration can be applied and rolled back in a disposable environment.
* [ ] API and worker start independently.
* [ ] Both connect to PostgreSQL.
* [ ] Local development can start from a documented command.
* [ ] Build and deployment metadata appear in application telemetry.



 
“In Phase 1, the main goal is to establish a solid **production-ready foundation** for the application. We’ll finish the core engineering setup around **code quality**, **configuration**, **database migrations**, **dependency injection**, and the **separation of the API and worker processes**. We’ll also make sure the local development environment is reproducible, with PostgreSQL and the required dependencies running through Docker Compose, and that both the API and worker can start independently and connect correctly to the database. This follows the technical architecture’s intent of having one codebase and application image, but separate API, worker, and migration runtime commands.”

  

“The other major part of Phase 1 is getting the **delivery** and **operational pipeline** in place. That means **containerizing** the application, adding **CI checks** for migrations and event schemas, introducing **secret and vulnerability scanning**, and **setting up a controlled staging** deployment process. We’ll also attach **build, commit, image**, and **environment** metadata to **telemetry** so we always know exactly what version is running where. By the end of the phase, we should be able to **bring the system up from a documented command**, **apply and roll back migrations** in a clean environment, **run API and worker independently against PostgreSQL**, and **have the basic controls in place** so production deployments happen only through the approved pipeline.”
