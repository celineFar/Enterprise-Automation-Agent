# Release 0 Checklist

# 3. Critical implementation order

The sequence matters. In particular, do not implement the happy-path graph before its persistence, identity, and side-effect contracts are defined.

## Phase 0 — Decisions and contracts

Complete this before substantial feature development.

### Checklist

- [x]  Approve the Release 0 vertical-slice definition.
- [x]  Select the first source integration: Slack or email.
- [x]  Define which email provider is included, if email is selected.
- [x]  Decide how the application identifies a project manager. — Application user ID with a role
- [x]  Decide how source conversations map to Jira projects. — One Jira project per Slack workspace
- [x]  Resolve the operation-ledger discrepancy.
- [x]  Decide whether `workflow_step_executions` is the canonical external-effect record. — I don’t think we need this, idempotency covers this
- [x]  Approve the workflow and step status models.
- [x]  Approve identifier formats and generation rules.
- [x]  Approve the tenant-isolation model.
- [x]  Approve the credential-storage approach.
- [x]  Approve the telemetry data-classification and redaction rules.
- [x]  Define supported deployment environments.
- [x]  Define the Release 0 availability and recovery objectives as test targets, not promises.
- [x]  Assign owners for application, platform, security, integrations, AI quality, and on-call operations.

### Required ADRs

- [ ]  ADR: operation evidence stored in `workflow_step_executions`.
- [ ]  ADR: product tables remain independent of LangGraph checkpoint internals.
- [ ]  ADR: deterministic policy code controls authorization.
- [ ]  ADR: provider APIs are accessed through typed adapters.
- [ ]  ADR: provider success must be verified.
- [ ]  ADR: stable plan revision is the approval boundary.
- [ ]  ADR: telemetry is diagnostic and never authoritative business state.
- [ ]  ADR: raw source content is excluded from ordinary logs and traces.

### Exit gate

Engineering can explain, on one page:

1. Which workflow is being built.
2. Which systems it touches.
3. Where every state transition is stored.
4. How duplicate writes are prevented.
5. How an interrupted workflow resumes.
6. How an operator investigates and recovers a failed run.

---

# 4. Phase 1 — Repository and platform skeleton

## Application structure

A reasonable initial layout:

```
src/
  api/
  graphs/
  domain/
  capabilities/
  policies/
  integrations/
    slack/
    email/
    jira/
  persistence/
  telemetry/
  workers/
  security/
  admin/
tests/
  unit/
  contract/
  integration/
  fault_injection/
  evaluation/
migrations/
deploy/
  local/
  staging/
  production/
```

### Checklist

- [ ]  Create the FastAPI application.
- [ ]  Create separate API and worker entry points.
- [ ]  Add Pydantic configuration models.
- [ ]  Add environment-specific configuration.
- [ ]  Add dependency injection for repositories and adapters.
- [ ]  Add linting, formatting, typing, and unit-test commands.
- [ ]  Add pre-commit hooks.
- [ ]  Add container builds.
- [ ]  Add health and readiness endpoints.
- [ ]  Add build, commit, image, and environment metadata.
- [ ]  Add database migration tooling.
- [ ]  Add local Docker Compose dependencies.
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

---

# 5. Phase 2 — Identity, tenancy, authorization, and connections

Implement tenant boundaries before ingestion or graph execution.

## Core models

- `organizations`
- `users`
- `organization_memberships`
- `roles`
- `provider_identities`
- `integration_connections`
- `resource_mappings`

### Checklist

#### Tenant context

- [ ]  Every API request resolves an `organization_id`.
- [ ]  Every webhook resolves an organization through its integration connection.
- [ ]  Every repository method requires organization context.
- [ ]  Every relevant table includes `organization_id`.
- [ ]  Database uniqueness constraints include tenant boundaries where required.
- [ ]  Cross-tenant access fails closed.
- [ ]  Tenant mismatch produces a security event.
- [ ]  Tests attempt horizontal and vertical privilege escalation.

#### Identity mapping

- [ ]  Map application users to Slack identities.
- [ ]  Map application users to email identities.
- [ ]  Map application users to Jira identities where needed.
- [ ]  Handle missing mappings explicitly.
- [ ]  Handle ambiguous mappings explicitly.
- [ ]  Never let the LLM choose an identity without deterministic validation.

#### Authorization

- [ ]  Define typed actions such as `discussion.analyze`, `jira.draft`, `jira.approve`, and `jira.create`.
- [ ]  Define the initial permission matrix.
- [ ]  Implement `authorize(actor, capability, resource, context)`.
- [ ]  Require PM authority for Jira creation approval.
- [ ]  Reauthorize the requester at workflow start.
- [ ]  Reauthorize the reviewer when an approval is submitted.
- [ ]  Reauthorize immediately before Jira creation.
- [ ]  Store the policy version with authorization and approval records.
- [ ]  Emit durable audit records for sensitive allow/deny decisions.

#### Integration connections

- [ ]  Store connection metadata separately from credentials.
- [ ]  Encrypt credentials at rest.
- [ ]  Restrict credential access to integration execution code.
- [ ]  Implement token refresh where supported.
- [ ]  Represent revoked or expired credentials as `reconnect_required`.
- [ ]  Ensure authentication failures do not retry indefinitely.
- [ ]  Audit connection creation, refresh failure, reconnection, and disconnection.

### Exit gate

- [ ]  A developer can request analysis.
- [ ]  Only an authorized PM can approve Jira creation.
- [ ]  Removing the PM role while a workflow is paused prevents execution.
- [ ]  A user in one organization cannot inspect or affect another organization’s run.

---

# 6. Phase 3 — Durable data model

Create the product system of record before relying on LangGraph checkpoints.

## Recommended Release 0 tables

### Core workflow tables

- `requests`
- `workflow_runs`
- `workflow_transitions`
- `workflow_step_executions`
- `plans`
- `approval_requests`
- `workflow_interrupts`

### Integration reliability tables

- `inbound_events`
- `outbox_events`

### Governance and operations tables

- `audit_events`
- `configuration_versions`
- `deployment_events`
- `integration_connections`
- `provider_identity_mappings`

## Important constraints

### `requests`

- [ ]  Stable `request_id`.
- [ ]  `organization_id`.
- [ ]  `requester_id`.
- [ ]  Request source.
- [ ]  Source reference.
- [ ]  Original payload reference.
- [ ]  Normalized request version.
- [ ]  Creation timestamp.

### `workflow_runs`

- [ ]  Stable `workflow_id`.
- [ ]  Stable LangGraph `thread_id`.
- [ ]  Request relationship.
- [ ]  Graph name and graph version.
- [ ]  State-schema version.
- [ ]  Plan ID and revision.
- [ ]  Current status.
- [ ]  Current wait reason.
- [ ]  Original and current deployment versions.
- [ ]  Optimistic concurrency version.
- [ ]  Started, paused, completed, and updated timestamps.

### `plans`

Release 0 should still create a plan record, even though it is compiled from a fixed template.

- [ ]  Template ID and version.
- [ ]  Exact plan revision.
- [ ]  Policy version.
- [ ]  Typed plan JSON.
- [ ]  Validation status.
- [ ]  Effect summary.
- [ ]  Plan fingerprint.
- [ ]  Immutable approved revision.

### `workflow_step_executions`

This is the most important reliability table.

- [ ]  Stable `step_execution_id`.
- [ ]  `workflow_id`.
- [ ]  `plan_id` and revision.
- [ ]  Stable logical `step_id`.
- [ ]  Capability name and version.
- [ ]  Effect classification.
- [ ]  Attempt number.
- [ ]  Deterministic idempotency key.
- [ ]  Logical target fingerprint.
- [ ]  Input fingerprint.
- [ ]  Status.
- [ ]  Worker lease owner and expiry.
- [ ]  Provider operation.
- [ ]  Provider request ID.
- [ ]  Provider resource ID.
- [ ]  Provider response reference.
- [ ]  Normalized error category and code.
- [ ]  Retryability.
- [ ]  Verification status.
- [ ]  Verification timestamp.
- [ ]  Created, started, completed, and updated timestamps.

### `approval_requests`

- [ ]  Approval ID.
- [ ]  Organization ID.
- [ ]  Plan ID and exact revision.
- [ ]  Required authority.
- [ ]  Resolved reviewer identity.
- [ ]  Effect fingerprint.
- [ ]  Display-safe effect summary.
- [ ]  Status.
- [ ]  Decision and comments.
- [ ]  Expiration.
- [ ]  Policy version.
- [ ]  Optimistic concurrency version.
- [ ]  Decision timestamp.

### Inbox and outbox

- [ ]  Unique provider event ID or deterministic event fingerprint.
- [ ]  Persist before processing.
- [ ]  Processing lease.
- [ ]  Attempt count.
- [ ]  Processing outcome.
- [ ]  Dead-letter or manual-review state.
- [ ]  Outbox records written in the same transaction as domain changes.
- [ ]  Outbox publisher can retry safely.
- [ ]  Published events carry correlation IDs.

### Audit

- [ ]  Append-only application permissions.
- [ ]  No runtime updates or deletes.
- [ ]  Corrections are new linked events.
- [ ]  Actor, target, action, authorization, and result fields.
- [ ]  Workflow, plan, approval, and step references.
- [ ]  Retention and backup policy.
- [ ]  Restricted query access.

### Exit gate

- [ ]  A run’s complete business lifecycle can be reconstructed without using Loki or Tempo.
- [ ]  External write attempts can be reconstructed without application logs.
- [ ]  Duplicate idempotency keys are prevented by a database constraint.
- [ ]  Approval submission is protected by a unique or optimistic concurrency rule.

# 7. Phase 4 — Common telemetry foundation

Observability should be built alongside the first runtime components, not added after the workflow works.

## Correlation model

Every applicable signal should carry:

- `request_id`
- `workflow_id`
- `thread_id`
- `organization_id`
- `actor_id` and actor type
- `trace_id` and `span_id`
- Graph name and node
- Workflow and state-schema version
- Service version and deployment ID
- Provider and provider operation
- Plan ID and revision where relevant
- Prompt and model version for AI calls

## Structured logging

### Checklist

- [ ]  Add shared `structlog` package configuration.
- [ ]  Use JSON output in deployed environments.
- [ ]  Use readable console output locally.
- [ ]  Bind context using `contextvars`.
- [ ]  Bridge standard-library and framework logs.
- [ ]  Define event names and versions.
- [ ]  Define bounded error categories.
- [ ]  Add automatic trace/span correlation.
- [ ]  Add application-level redaction.
- [ ]  Prevent authorization headers, tokens, cookies, secrets, and raw bodies from being logged.
- [ ]  Define log-level rules.
- [ ]  Add schema tests for required event fields.

## OpenTelemetry

- [ ]  Instrument inbound HTTP.
- [ ]  Instrument outbound HTTP.
- [ ]  Instrument PostgreSQL.
- [ ]  Instrument queue publish and consume.
- [ ]  Instrument LangGraph invocation and nodes.
- [ ]  Instrument provider adapters.
- [ ]  Instrument LLM generations.
- [ ]  Preserve trace context through asynchronous work.
- [ ]  Preserve correlation through pause and resume.
- [ ]  Add links when a resumed workflow starts a new trace.

## Collector

- [ ]  Configure OTLP gRPC and HTTP receivers.
- [ ]  Add resource enrichment.
- [ ]  Add environment and release metadata.
- [ ]  Add second-layer redaction.
- [ ]  Add memory limiter.
- [ ]  Add batching.
- [ ]  Add retries.
- [ ]  Route logs to Loki.
- [ ]  Route traces to Tempo.
- [ ]  Expose metrics for Prometheus.
- [ ]  Monitor collector queue size and dropped telemetry.
- [ ]  Ensure collector failure does not fail workflow execution.

## Backends

- [ ]  Deploy Loki.
- [ ]  Deploy Tempo.
- [ ]  Deploy Prometheus.
- [ ]  Deploy Alertmanager or Grafana-managed alerting.
- [ ]  Deploy Grafana.
- [ ]  Connect all data sources.
- [ ]  Configure object storage where needed.
- [ ]  Configure initial retention.
- [ ]  Configure access controls.
- [ ]  Back up configuration and dashboard definitions.

## Langfuse

For Release 0, keep integration basic.

- [ ]  Trace action-item extraction.
- [ ]  Store model, prompt version, latency, tokens, and cost.
- [ ]  Link Langfuse observations to workflow and trace IDs.
- [ ]  Disable or redact raw sensitive prompt/output capture by default.
- [ ]  Ensure Langfuse outages cannot break workflow execution.
- [ ]  Add a simple reviewer feedback or edit-rate mechanism if practical.

### Exit gate

Given a workflow ID, an engineer can find:

1. Product workflow history.
2. Relevant logs.
3. The distributed trace.
4. The model invocation.
5. The provider request and result.
6. The deployment version that executed it.

---

# 8. Phase 5 — Provider adapter contracts and deterministic mocks

Do not put raw provider calls in graph nodes.

## Common adapter contract

Every adapter should support:

- Typed inputs and outputs.
- Canonical identities.
- Credential acquisition.
- Timeouts.
- Retry hints.
- Normalized errors.
- Provider request IDs.
- Rate-limit metadata.
- Reconciliation or lookup.
- Test doubles.
- Safe logging and tracing.

## Normalized error categories

- `transient_transport`
- `rate_limit`
- `authentication`
- `authorization`
- `validation`
- `ambiguous_outcome`
- `permanent_provider_rule`
- `not_found`
- `conflict`

## Source adapter checklist

- [ ]  Fetch a conversation by stable source reference.
- [ ]  Verify access using the requester’s or integration’s authority model.
- [ ]  Return canonical normalized messages.
- [ ]  Preserve source message IDs and authors.
- [ ]  Preserve timestamps and thread structure.
- [ ]  Return references instead of placing unrestricted content in logs.
- [ ]  Support deterministic mock conversations.
- [ ]  Support “not visible to bot” and “resource deleted” cases.
- [ ]  Support rate-limit and timeout simulation.

## Jira adapter checklist

- [ ]  Validate project accessibility.
- [ ]  Validate required fields.
- [ ]  Resolve users and assignees.
- [ ]  Create an issue through a narrow typed method.
- [ ]  Attach an idempotency or correlation marker where Jira permits.
- [ ]  Search for an existing issue using the stable marker or business reference.
- [ ]  Fetch a created issue for verification.
- [ ]  Normalize Jira validation errors.
- [ ]  Normalize permission errors.
- [ ]  Support ambiguous timeout simulation.
- [ ]  Provide a deterministic in-memory or HTTP mock.

## Source publication checklist

- [ ]  Post a completion or partial-completion result to the original source.
- [ ]  Use a stable idempotency key for the result notification.
- [ ]  Store the provider message ID.
- [ ]  Verify or retrieve the published result when practical.
- [ ]  Avoid publishing duplicate messages on workflow resume.

### Exit gate

- [ ]  Graph code imports provider interfaces, not vendor SDK clients.
- [ ]  Provider sandbox contract tests exist.
- [ ]  Deterministic mocks can simulate success, timeout, rate limit, expired token, permission denial, ambiguous write, and malformed response.

---

# 9. Phase 6 — Inbound webhook and command ingestion

## Request envelope

Define one normalized request schema containing:

- Request ID.
- Organization.
- Requester.
- Source.
- Source reference.
- Requested workflow family.
- Execution mode.
- Parameters.
- Payload reference.
- Schema version.

## Checklist

### Webhook gateway

- [ ]  Verify provider signatures.
- [ ]  Reject stale or invalid webhook requests.
- [ ]  Resolve the integration and tenant.
- [ ]  Persist the inbound event before processing.
- [ ]  Deduplicate by provider event ID.
- [ ]  Return provider acknowledgement promptly.
- [ ]  Process asynchronously.
- [ ]  Add a processing lease.
- [ ]  Add bounded retries.
- [ ]  Add manual-review/dead-letter state.
- [ ]  Audit invalid signatures and tenant mismatches.

### API request path

- [ ]  Authenticate the caller.
- [ ]  Resolve organization and actor.
- [ ]  Validate the request schema.
- [ ]  Persist the original request.
- [ ]  Create a workflow run.
- [ ]  Compile the fixed template into a plan.
- [ ]  Publish a durable start command.
- [ ]  Return a stable workflow ID.

### Duplicate handling

- [ ]  Duplicate webhook returns success without creating a second run.
- [ ]  Duplicate API command uses a caller-supplied or generated idempotency key.
- [ ]  Reprocessing the inbox row does not create a duplicate workflow.
- [ ]  All dedupe outcomes are observable.

### Exit gate

- [ ]  Replaying the same webhook 100 times creates one logical request and one workflow.
- [ ]  A crash after inbox persistence but before processing is recoverable.
- [ ]  A crash after workflow creation but before webhook completion does not duplicate the run.

---

# 10. Phase 7 — LangGraph persistence and workflow skeleton

## Graph

```
START
  -> authorize_request
  -> load_source_conversation
  -> normalize_messages
  -> extract_action_items
  -> validate_and_resolve_entities
  -> draft_jira_issues
  -> interrupt_for_pm_review
  -> reauthorize_reviewer_and_plan
  -> create_jira_issues_idempotently
  -> verify_provider_state
  -> publish_result
  -> END
```

## State contract

State should contain references and typed business data—not provider clients, credentials, or unrestricted documents.

Suggested fields:

```
schema_version
graph_version
request_id
workflow_id
organization_id
requester_id
plan_id
plan_revision
source_reference
source_payload_reference
normalized_message_references
draft_issues
entity_resolution_warnings
approval_id
approved_issue_ids
step_results
recoverable_error
status
```

## Checklist

- [ ]  Configure `AsyncPostgresSaver`.
- [ ]  Use stable thread IDs derived from workflow IDs.
- [ ]  Add graph and state-schema versions.
- [ ]  Pin template, capability, and policy versions.
- [ ]  Ensure every node is safe to retry.
- [ ]  Ensure code before an interrupt is side-effect-free or idempotent.
- [ ]  Persist product-level transitions independently of checkpoints.
- [ ]  Store checkpoint references in transition history.
- [ ]  Validate resume payloads.
- [ ]  Implement compatibility checks before resuming on newer code.
- [ ]  Prevent concurrent mutating execution for the same workflow.
- [ ]  Use optimistic concurrency for workflow state changes.
- [ ]  Implement cancellation before future external effects.
- [ ]  Implement recoverable, permanent, and manual-review error states.

### Exit gate

- [ ]  Kill the worker at every node boundary and resume from durable state.
- [ ]  Leave the workflow paused for an extended period and resume successfully.
- [ ]  Deploy a compatible code change and resume the old workflow.
- [ ]  Reject resume under an incompatible state or graph version.

# 11. Phase 8 — Extraction, validation, and Jira draft generation

The LLM may extract and draft. It may not authorize, select unrestricted targets, or determine provider success.

## Draft issue schema

Suggested required fields:

- Summary.
- Description.
- Source references.
- Proposed owner.
- Proposed due date.
- Confidence or warnings.
- Unresolved entities.
- Evidence references.
- Reviewer-editable fields.

## Checklist

- [ ]  Version the extraction prompt.
- [ ]  Version the model configuration.
- [ ]  Require structured output.
- [ ]  Parse through a strict schema.
- [ ]  Reject unknown fields.
- [ ]  Bound the number of generated issues.
- [ ]  Require evidence references for each issue.
- [ ]  Resolve users deterministically after extraction.
- [ ]  Validate Jira project mapping deterministically.
- [ ]  Validate due dates deterministically.
- [ ]  Mark unsupported or ambiguous fields.
- [ ]  Never silently invent an owner.
- [ ]  Never silently invent a deadline.
- [ ]  Add bounded model retry or repair.
- [ ]  Send persistent schema failures to human review.
- [ ]  Record prompt, model, latency, token, and cost metadata.
- [ ]  Create a small evaluation dataset from representative discussions.
- [ ]  Measure reviewer acceptance and edit rate.

### Exit gate

- [ ]  Invalid model output cannot reach the approval screen.
- [ ]  Every proposed issue has provenance.
- [ ]  Unknown owners or projects stop before execution.
- [ ]  The same deterministic test conversation produces structurally stable output within defined tolerance.

---

# 12. Phase 9 — Human approval and resume

Approval is a durable business object, not simply a LangGraph interrupt payload.

## Checklist

### Approval creation

- [ ]  Generate an approval ID.
- [ ]  Bind it to the exact plan revision.
- [ ]  Store the effect fingerprint.
- [ ]  Store required reviewer authority.
- [ ]  Store safe display data.
- [ ]  Store expiration.
- [ ]  Create the approval record before pausing.
- [ ]  Emit an audit event.
- [ ]  Emit a workflow transition.
- [ ]  Send or expose the approval request.

### Approval API/UI

- [ ]  Authenticate the reviewer.
- [ ]  Resolve tenant and role.
- [ ]  Verify the approval is pending.
- [ ]  Verify the plan revision still matches.
- [ ]  Verify the effect fingerprint still matches.
- [ ]  Allow approved fields to be edited only when policy permits.
- [ ]  Require a new revision for material changes.
- [ ]  Use optimistic concurrency.
- [ ]  Make duplicate submissions idempotent.
- [ ]  Store the decision and comments.
- [ ]  Audit the decision.
- [ ]  Resume using the stable thread ID.

### Resume checks

- [ ]  Revalidate reviewer authority.
- [ ]  Revalidate request authority.
- [ ]  Revalidate Jira connection state.
- [ ]  Revalidate project access.
- [ ]  Revalidate plan revision.
- [ ]  Revalidate effect set.
- [ ]  Revalidate deployment compatibility.
- [ ]  Reject stale or revoked approvals.

### Exit gate

- [ ]  Two simultaneous approval submissions produce one decision.
- [ ]  Replaying an approval request has no duplicate effect.
- [ ]  A materially changed plan invalidates the existing approval.
- [ ]  A role revoked while paused prevents Jira creation.

---

# 13. Phase 10 — Idempotent Jira execution

This is the core Release 0 correctness boundary.

## Safe execution sequence

For every Jira issue:

1. Calculate a deterministic logical target.
2. Calculate the idempotency key.
3. Insert or retrieve the step-execution row.
4. Acquire a lease.
5. If already verified successful, return the stored result.
6. If the prior outcome is ambiguous, reconcile before retrying.
7. Call Jira.
8. Persist the provider response reference.
9. Retrieve or search Jira to verify the issue.
10. Mark success only after verification.
11. Publish a durable audit event.
12. Continue with the next approved issue.

Example key:

```
{organization_id}:{workflow_id}:{plan_revision}:{step_id}:{logical_issue_index}
```

## Checklist

- [ ]  Generate stable step IDs during plan compilation.
- [ ]  Generate deterministic operation keys.
- [ ]  Add a unique constraint on organization and idempotency key.
- [ ]  Insert the execution record before the provider call.
- [ ]  Commit the record before calling Jira.
- [ ]  Add worker lease ownership.
- [ ]  Add bounded lease expiration.
- [ ]  Add attempt counting.
- [ ]  Use the same key on retry.
- [ ]  Treat provider timeout after submission as ambiguous.
- [ ]  Reconcile ambiguous outcomes before retry.
- [ ]  Search using stable external metadata or business marker.
- [ ]  Verify project, summary, description, and assignment as appropriate.
- [ ]  Record mismatches.
- [ ]  Route unresolved ambiguity to manual review.
- [ ]  Do not claim rollback if Jira state is unknown.
- [ ]  Allow partial completion across multiple approved drafts.
- [ ]  Do not recreate already verified issues when resuming.
- [ ]  Audit every verified external effect.

### Required fault-injection tests

For each external create, kill the worker:

- [ ]  Before the execution record is committed.
- [ ]  After the execution record is committed.
- [ ]  Immediately before the Jira call.
- [ ]  While the Jira call is in flight.
- [ ]  After Jira creates the issue but before the response is received.
- [ ]  After the response but before it is persisted.
- [ ]  After persistence but before verification.
- [ ]  After verification but before the workflow checkpoint.
- [ ]  After checkpoint but before result publication.

### Exit gate

Every scenario results in no more than one logical Jira issue.

---

# 14. Phase 11 — Verification and source publication

## Provider verification

- [ ]  Retrieve or search for the Jira issue after creation.
- [ ]  Confirm the expected project.
- [ ]  Confirm the expected issue type.
- [ ]  Confirm the correlation marker.
- [ ]  Confirm protected fields.
- [ ]  Store verification results.
- [ ]  Emit `provider.verification.succeeded` or mismatch events.
- [ ]  Distinguish success, partial success, ambiguity, and failure.

## Result publication

- [ ]  Create a human-readable result summary.
- [ ]  Include links or stable Jira references.
- [ ]  State partial failures explicitly.
- [ ]  Publish using an idempotent step record.
- [ ]  Store the source message reference.
- [ ]  Avoid duplicate completion messages after resume.
- [ ]  Persist an outbox event for downstream notifications.
- [ ]  Mark the workflow complete only after required postconditions are met.
- [ ]  Use `PARTIALLY_COMPLETED` when some approved issues could not be created or verified.

### Exit gate

- [ ]  Product state and source message agree on the final outcome.
- [ ]  A successful Jira API response without verification does not mark the workflow complete.
- [ ]  Retrying result publication cannot duplicate the completion message.

---

# 15. Phase 12 — Admin inspection and recovery

Release 0 does not need a large operations console, but it needs a usable run inspector.

## Minimum run-inspection view

- Request and workflow identifiers.
- Tenant and requester.
- Current status and node.
- Graph, state, policy, and deployment versions.
- Plan and revision.
- Pending approval.
- Ordered workflow transitions.
- Step executions and attempts.
- Provider request and resource references.
- Retry, ambiguity, and verification state.
- Recent trace and log links.
- Audit events.
- Permitted recovery actions.

## Checklist

- [ ]  Search by workflow ID.
- [ ]  Search by request ID.
- [ ]  Search by provider resource ID.
- [ ]  Search by source conversation reference.
- [ ]  Display current wait reason.
- [ ]  Display the last successful node.
- [ ]  Display normalized errors.
- [ ]  Link to Grafana trace/log views.
- [ ]  Link to Langfuse where applicable.
- [ ]  Allow retry only for retryable states.
- [ ]  Allow reconciliation of ambiguous writes.
- [ ]  Allow cancellation of future steps.
- [ ]  Allow credential-reconnect resume.
- [ ]  Require elevated authorization for admin actions.
- [ ]  Audit every admin inspection and action.
- [ ]  Never permit arbitrary state editing.

### Exit gate

An on-call engineer can diagnose and safely recover a prepared failure using the runbook and inspector without direct database modification.

---

# 16. Phase 13 — Dashboards, alerts, and runbooks

## Required Release 0 dashboards

### Platform overview

- Request volume and error rate.
- API latency.
- Worker health.
- Queue depth and oldest message age.
- PostgreSQL health and pool usage.
- Checkpoint failures.
- Collector health and dropped telemetry.

### Workflow operations

- Runs by status.
- Runs by outcome.
- Workflow duration.
- Approval wait duration.
- Retry counts.
- Stuck workflows.
- Partial completions.
- Resume failures.

### Provider reliability

- Jira and source-provider latency.
- Error categories.
- Rate-limit frequency.
- Credential failures.
- Ambiguous writes.
- Verification mismatches.
- Provider success rate.

### AI quality and cost

- Model latency.
- Schema-validation failure rate.
- Token and cost totals.
- Draft count.
- Approval and rejection rates.
- Reviewer edit rate.
- Prompt/model/release comparison.

### Security and audit

- Authorization denials.
- Invalid webhook signatures.
- Tenant-scope mismatches.
- Credential events.
- Administrative recovery actions.
- Audit persistence failures.

### Release health

- Deployment annotations.
- Workflow outcomes before and after deployment.
- Provider failures before and after deployment.
- AI validation and edit rates by release.
- Rollback indicators.

## Initial alerts

Page-worthy:

- [ ]  Checkpoint database unavailable.
- [ ]  Audit persistence unavailable.
- [ ]  Significant queue backlog.
- [ ]  Widespread workflow failure.
- [ ]  Repeated resume failures.
- [ ]  Cross-tenant mismatch signal.
- [ ]  Jira authentication outage.
- [ ]  High ambiguous-write rate.
- [ ]  Critical telemetry pipeline failure that prevents investigation, without failing business execution.

Ticket/chat-worthy:

- [ ]  Increasing retries.
- [ ]  Increasing provider rate limits.
- [ ]  Rising verification mismatch rate.
- [ ]  AI schema-validation regression.
- [ ]  Unexpected cost increase.
- [ ]  Storage approaching capacity.
- [ ]  Increasing reviewer edit or rejection rate.

Every page must have:

- [ ]  Owner.
- [ ]  Severity.
- [ ]  Duration threshold.
- [ ]  Dashboard link.
- [ ]  Runbook.
- [ ]  Clear remediation or escalation.
- [ ]  Recent deployment context.

## Minimum runbooks

- [ ]  Workflow failure or partial completion.
- [ ]  PostgreSQL/checkpoint outage.
- [ ]  Paused workflow resume failure.
- [ ]  Provider credential expiration.
- [ ]  Provider rate limiting.
- [ ]  Queue backlog.
- [ ]  Ambiguous Jira write.
- [ ]  Provider verification mismatch.
- [ ]  Collector backpressure.
- [ ]  Loki, Tempo, Prometheus, or Grafana outage.
- [ ]  Langfuse ingestion outage.
- [ ]  Sensitive data found in telemetry.
- [ ]  Bad deployment rollback.
- [ ]  Incompatible paused workflow after release.

# 17. Phase 14 — Security and privacy hardening

## Checklist

- [ ]  Complete a Release 0 threat model.
- [ ]  Model cross-tenant access threats.
- [ ]  Model webhook spoofing.
- [ ]  Model confused-deputy execution.
- [ ]  Model approval replay.
- [ ]  Model role revocation during pause.
- [ ]  Model credential theft.
- [ ]  Model prompt injection in source conversations.
- [ ]  Treat source content as untrusted data.
- [ ]  Ensure source text cannot change policies or tool permissions.
- [ ]  Apply allowlisted Jira fields.
- [ ]  Apply hard issue-count limits.
- [ ]  Restrict target Jira projects.
- [ ]  Redact secrets at application and collector levels.
- [ ]  Test representative tokens and authorization headers.
- [ ]  Test email, Slack, and Jira content redaction.
- [ ]  Test LLM prompt/output redaction.
- [ ]  Restrict production telemetry access.
- [ ]  Audit diagnostic access and exports.
- [ ]  Encrypt database, object storage, and backups.
- [ ]  Test backup restoration.
- [ ]  Document retention policies.
- [ ]  Document deletion and revocation behavior.

### Exit gate

- [ ]  No secrets appear in sampled telemetry.
- [ ]  No raw source conversation appears in ordinary operational logs.
- [ ]  Prompt injection cannot select a forbidden capability or bypass PM approval.
- [ ]  Tenant-isolation tests pass at API, repository, graph, and provider-mapping layers.

---

# 18. Phase 15 — Complete test matrix

## Unit tests

- [ ]  Request normalization.
- [ ]  Policy decisions.
- [ ]  Plan compilation.
- [ ]  Plan fingerprinting.
- [ ]  Idempotency key generation.
- [ ]  Error normalization.
- [ ]  State transitions.
- [ ]  Approval validation.
- [ ]  Event schema validation.
- [ ]  Redaction.
- [ ]  Metric and log label rules.

## Integration tests

- [ ]  PostgreSQL repositories.
- [ ]  LangGraph checkpoint persistence.
- [ ]  Inbox deduplication.
- [ ]  Outbox publication.
- [ ]  Approval pause and resume.
- [ ]  Jira create and verification.
- [ ]  Provider authentication refresh.
- [ ]  Collector routing.
- [ ]  Grafana data-source connectivity.
- [ ]  Langfuse linkage.

## Contract tests

- [ ]  Source provider sandbox or deterministic server.
- [ ]  Jira sandbox or deterministic server.
- [ ]  Provider schema changes.
- [ ]  Error and rate-limit formats.
- [ ]  Authentication refresh behavior.

## Concurrency tests

- [ ]  Two workers consume the same command.
- [ ]  Two workers attempt the same Jira step.
- [ ]  Two reviewers submit approval simultaneously.
- [ ]  Approval and cancellation race.
- [ ]  Credential revocation and execution race.
- [ ]  Workflow resume and deployment race.

## Failure and chaos tests

- [ ]  Worker termination at every critical boundary.
- [ ]  Database connection interruption.
- [ ]  Checkpoint write failure.
- [ ]  Queue delivery duplication.
- [ ]  Queue delay.
- [ ]  Provider timeout.
- [ ]  Provider 500 response.
- [ ]  Provider 429 response.
- [ ]  Credential expiration.
- [ ]  Provider response loss after successful create.
- [ ]  Loki outage.
- [ ]  Tempo outage.
- [ ]  Langfuse outage.
- [ ]  Collector outage.
- [ ]  Partial telemetry backend failure.
- [ ]  Deployment during approval wait.
- [ ]  Rollback while workflows are paused.

## Observability acceptance tests

- [ ]  Trace context survives API → queue → worker.
- [ ]  Correlation survives workflow pause/resume.
- [ ]  Logs link to traces.
- [ ]  Traces link to workflow history.
- [ ]  AI observations link to workflow and release.
- [ ]  High-cardinality IDs are not Prometheus labels.
- [ ]  High-cardinality IDs are not Loki stream labels.
- [ ]  Failed workflows are retained according to sampling policy.
- [ ]  Telemetry exporter failure does not fail business requests.
- [ ]  Audit records persist when telemetry export is unavailable.

---

# 19. Suggested 10-week execution schedule

The source plan proposes a 12-week sequence that begins Release 1 work in weeks 9–12. For a focused Release 0, use approximately 8–10 weeks, then begin the pilot or Release 1a hardening.

## Weeks 1–2: Decisions, skeleton, and schemas

Deliver:

- ADRs.
- Threat-model draft.
- Repository structure.
- FastAPI and worker skeleton.
- PostgreSQL migrations.
- Core identity, request, run, plan, step, approval, inbox, outbox, and audit schemas.
- Local provider mocks.
- Initial event envelope.

Evidence:

- One local durable graph execution.
- Schema and architecture review.
- CI passes.
- Initial tenant isolation tests.

## Weeks 3–4: Persistence, ingestion, and observability pipeline

Deliver:

- LangGraph PostgreSQL checkpointer.
- Product workflow history.
- Inbox deduplication.
- Outbox publisher.
- Source read adapter.
- Jira typed adapter skeleton.
- Structlog and OpenTelemetry.
- Collector, Loki, Tempo, Prometheus, and Grafana.
- Basic Langfuse linkage.

Evidence:

- Duplicate event tests.
- Pause/resume tests.
- End-to-end trace across API, queue, worker, graph, and mock provider.
- Redaction test suite.

## Weeks 5–6: Drafting, approval, and Jira write safety

Deliver:

- Conversation normalization.
- Structured action-item extraction.
- Deterministic entity validation.
- Jira draft schema.
- PM approval interrupt.
- Approval endpoint.
- Plan revision and effect fingerprint.
- Durable step-execution records.
- Idempotent Jira create.
- Provider reconciliation and verification.

Evidence:

- Duplicate approval tests.
- Crash-before/after provider-call tests.
- Role-revocation-during-pause test.
- Ambiguous timeout test.

## Weeks 7–8: Completion path and operations

Deliver:

- Source result publication.
- Partial-completion handling.
- Credential refresh and reconnect state.
- Admin run inspector.
- Audit queries.
- Dashboards.
- Initial alerts.
- Required runbooks.
- Deployment annotations.

Evidence:

- Support recovery drill.
- Complete audit-trace demonstration.
- Telemetry-backend outage tests.
- Bad-release rollback drill.

## Weeks 9–10: Hardening and release gate

Deliver:

- Provider sandbox contract tests.
- Full fault-injection matrix.
- Load and queue-backlog test.
- Tenant isolation and security test report.
- Backup/restore test.
- Evaluation dataset and draft-quality baseline.
- Staging soak.
- Release-readiness review.

Evidence:

- Zero duplicate logical Jira issues under all tested crash points.
- Durable resume across deployment.
- Traceability demonstration.
- Data-safety test results.
- Signed Release 0 exit report.

---

# 20. Workstream ownership

| Workstream | Primary owner | Supporting roles |
| --- | --- | --- |
| Domain and graph | Application engineering | AI engineering, architecture |
| Persistence and migrations | Application/platform | DBA or infrastructure |
| Source and Jira adapters | Integration engineering | Application engineering |
| Identity and policy | Application/security | Product administration |
| Telemetry SDK and Collector | Platform engineering | Feature teams |
| Loki/Tempo/Prometheus/Grafana | Platform/operations | Service owners |
| Langfuse and evaluation | AI engineering | Product |
| Audit and privacy | Security/application | Compliance |
| Dashboards and business metrics | Product analytics | Engineering |
| Alerts and runbooks | Service owners | On-call lead |
| Fault injection and release gates | QA/SRE | All workstream owners |

Each checklist item should have one directly responsible owner, not a shared team label alone.

---

# 21. Recommended epic structure

## Epic 1 — Platform bootstrap

- Repository and services.
- Configuration.
- CI/CD.
- Environments.
- Migrations.
- Secrets.

## Epic 2 — Identity and authority

- Organizations and users.
- Provider identity mapping.
- Roles and policy module.
- Connection lifecycle.
- Tenant isolation.

## Epic 3 — Durable workflow runtime

- LangGraph checkpointing.
- Workflow product tables.
- Transitions.
- Step executions.
- Compatibility checks.
- Cancellation and resume.

## Epic 4 — Reliable ingestion

- Webhook verification.
- Inbox.
- Deduplication.
- Queue.
- Outbox.

## Epic 5 — Discussion-to-Jira workflow

- Source loading.
- Normalization.
- Extraction.
- Validation.
- Jira drafts.
- Source result publication.

## Epic 6 — Approval system

- Approval records.
- Review surface/API.
- Revision fingerprint.
- Authority checks.
- Resume behavior.

## Epic 7 — Safe provider execution

- Adapter contract.
- Jira creation.
- Idempotency.
- Reconciliation.
- Verification.
- Partial completion.

## Epic 8 — Observability platform

- Event standard.
- Structlog.
- OTel.
- Collector.
- Loki/Tempo/Prometheus/Grafana.
- Langfuse.

## Epic 9 — Operations and governance

- Audit.
- Admin inspector.
- Dashboards.
- Alerts.
- Runbooks.
- Retention and access.

## Epic 10 — Release verification

- Contract tests.
- Concurrency tests.
- Fault injection.
- Security tests.
- Load tests.
- Recovery drills.
- Release report.

# 22. Release 0 definition of done

Release 0 is complete only when all of the following are demonstrated in a production-like staging environment.

## Functional

- [ ]  A valid Slack or email discussion starts a workflow.
- [ ]  The conversation is normalized.
- [ ]  Structured Jira drafts are created with provenance.
- [ ]  An authorized PM can approve or reject.
- [ ]  Approved issues are created in Jira.
- [ ]  Jira state is verified.
- [ ]  The result is posted back to the original source.
- [ ]  Partial failures are represented honestly.

## Durability and correctness

- [ ]  Duplicate webhook delivery produces one business request.
- [ ]  Duplicate approval submission produces one decision.
- [ ]  Duplicate worker execution produces no duplicate logical Jira issue.
- [ ]  A worker can die before, during, or after Jira creation without duplication.
- [ ]  An ambiguous provider outcome is reconciled before retry.
- [ ]  A paused workflow survives deployment.
- [ ]  A compatible paused workflow resumes on newer code.
- [ ]  An incompatible resume fails safely.
- [ ]  Expired credentials produce a reconnect state.
- [ ]  Every write is attributable to a request, actor, plan revision, approval, and step execution.

## Security

- [ ]  Tenant isolation tests pass.
- [ ]  PM-only approval rules pass.
- [ ]  Time-of-use authorization checks pass.
- [ ]  Webhook signature validation passes.
- [ ]  Prompt injection cannot change authority or capability scope.
- [ ]  No secrets are present in sampled telemetry.
- [ ]  Sensitive source content is excluded or redacted.

## Operability

- [ ]  Operators can find a run from its workflow ID.
- [ ]  Operators can locate its logs, trace, AI observation, and provider result.
- [ ]  Operators can identify the last successful step.
- [ ]  Operators can reconcile an ambiguous Jira write.
- [ ]  Operators can resume after credential reconnection.
- [ ]  Operators can cancel future effects.
- [ ]  All administrative recovery actions are audited.

## Observability

- [ ]  Event-envelope tests pass.
- [ ]  Context propagates across HTTP, queue, worker, graph, provider, and resume.
- [ ]  Dashboards are available.
- [ ]  Paging alerts have owners and runbooks.
- [ ]  Collector and telemetry backend failures do not fail workflows.
- [ ]  Workflow and audit data remain durable when telemetry is unavailable.
- [ ]  Redaction and label-cardinality tests pass.
- [ ]  A failed synthetic workflow can be traced end to end.

## Release evidence

- [ ]  Architecture and threat-model review completed.
- [ ]  Provider contract test report completed.
- [ ]  Fault-injection report completed.
- [ ]  Tenant-isolation report completed.
- [ ]  Load and recovery baselines recorded.
- [ ]  Backup restoration demonstrated.
- [ ]  Support drill completed.
- [ ]  Rollback and paused-workflow compatibility drill completed.
- [ ]  Known limitations documented.
- [ ]  Owners accept the runbooks and on-call responsibilities.

---

## The most important priorities

If scope pressure appears, protect these five items above everything else:

1. **Durable product state independent of logs and traces.**
2. **Deterministic idempotency and ambiguous-outcome reconciliation.**
3. **Approval tied to an exact immutable plan revision.**
4. **Time-of-use authorization and tenant isolation.**
5. **End-to-end traceability plus tested recovery procedures.**

Do not trade any of these for additional workflow features. Release 0 succeeds when the single workflow is boring, inspectable, restartable, and extremely difficult to execute twice.