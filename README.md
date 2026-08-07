# Relay Agent Platform

## Local PostgreSQL

Docker Compose provides the PostgreSQL dependency used for local development. Its credentials
are intentionally local-only and come from `.env`.

Create the local environment file and start PostgreSQL:

```bash
cp .env.example .env
make postgres-up
```

`postgres-up` waits for the container health check before returning. To check readiness using
the same database URL as the application:

```bash
make postgres-wait
```

Stop the local stack without deleting its database volume:

```bash
make compose-down
```

The `relay_postgres-data` named volume preserves data between restarts. Removing that volume is
an explicit destructive operation and is not part of the normal Make targets.
