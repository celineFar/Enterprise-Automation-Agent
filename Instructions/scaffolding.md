
```
agent-platform/
├── pyproject.toml
├── uv.lock
├── README.md
├── Makefile
├── Dockerfile
├── compose.yaml
├── .env.example
├── .pre-commit-config.yaml
├── alembic.ini
│
├── src/
│   └── agent_platform/
│       ├── __init__.py
│       │
│       ├── bootstrap/
│       │   ├── application.py
│       │   ├── container.py
│       │   └── lifecycle.py
│       │
│       ├── api/
│       │   ├── app.py
│       │   ├── dependencies.py
│       │   ├── middleware/
│       │   ├── routes/
│       │   │   ├── health.py
│       │   │   ├── requests.py
│       │   │   ├── workflows.py
│       │   │   └── approvals.py
│       │   └── schemas/
│       │
│       ├── workers/
│       │   ├── main.py
│       │   ├── consumer.py
│       │   └── handlers/
│       │
│       ├── workflows/
│       │   ├── common/
│       │   └── discussion_to_jira/
│       │       ├── graph.py
│       │       ├── nodes.py
│       │       ├── state.py
│       │       ├── plan_template.py
│       │       └── versions.py
│       │
│       ├── domain/
│       │   ├── users/
│       │   ├── requests/
│       │   ├── workflows/
│       │   ├── plans/
│       │   ├── approvals/
│       │   ├── executions/
│       │   └── audit/
│       │
│       ├── capabilities/
│       │   ├── registry.py
│       │   ├── contracts.py
│       │   └── jira/
│       │       └── create_issue.py
│       │
│       ├── policies/
│       │   ├── actions.py
│       │   ├── decisions.py
│       │   └── authorization.py
│       │
│       ├── integrations/
│       │   ├── common/
│       │   ├── slack/
│       │   ├── email/
│       │   └── jira/
│       │
│       ├── persistence/
│       │   ├── database.py
│       │   ├── models/
│       │   ├── repositories/
│       │   ├── transactions.py
│       │   └── checkpoints.py
│       │
│       ├── config/
│       │   ├── settings.py
│       │   └── types.py
│       │
│       ├── observability/
│       │   ├── logging.py
│       │   ├── tracing.py
│       │   ├── metrics.py
│       │   └── context.py
│       │
│       ├── security/
│       │   ├── credentials.py
│       │   ├── encryption.py
│       │   └── redaction.py
│       │
│       └── admin/
│           ├── services.py
│           └── schemas.py
│
├── tests/
│   ├── unit/
│   ├── graph/
│   ├── integration/
│   ├── contract/
│   ├── fault_injection/
│   └── evaluation/
│
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── deploy/
│   ├── compose/
│   ├── staging/
│   └── production/
│
├── observability/
│   ├── collector/
│   ├── prometheus/
│   ├── grafana/
│   │   ├── dashboards/
│   │   └── provisioning/
│   ├── loki/
│   └── tempo/
│
├── scripts/
│   ├── wait_for_postgres.py
│   ├── check_migrations.py
│   └── emit_deployment_event.py
│
└── .github/
    └── workflows/
        ├── ci.yml
        ├── security.yml
        ├── deploy-staging.yml
        └── deploy-production.yml
```