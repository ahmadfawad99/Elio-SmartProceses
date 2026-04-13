# Database Design

## Objectives

- Support high-write, time-series infrastructure ingestion.
- Preserve explainability for every AI decision and action.
- Keep operational queries fast for dashboards and approval queues.
- Enforce security boundaries for users, roles, and ingestion credentials.

## Schema Overview

### Identity and Access

- `users`: platform operators and internal service identities.
- `roles`: RBAC role catalog.
- `user_roles`: many-to-many role assignments with assignment audit metadata.
- `machine_credentials`: secure ingestion keys for machine or agent submissions.

### Core Infrastructure

- `machines`: inventory of monitored machines and runtime mode flags.
- `metrics`: Timescale hypertable storing time-series telemetry.

### AI Intelligence

- `anomalies`: anomaly detections with severity, context, and reasoning.
- `predictions`: predictive maintenance outputs, risk scores, and model features.

### Agentic Execution

- `actions`: recommended or executed remediations.
- `action_logs`: lifecycle entries for action execution state changes.
- `agent_logs`: structured agent I/O, correlation, timing, and reasoning.

### Audit and Compliance

- `audit_logs`: immutable operational/security audit trail.

## Relationship Model

```text
users ---< user_roles >--- roles
users ---< actions.requested_by
users ---< actions.approved_by
users ---< audit_logs.actor_id

machines ---< machine_credentials
machines ---< metrics
machines ---< anomalies
machines ---< predictions
machines ---< actions
machines ---< agent_logs

anomalies ---< predictions
predictions ---< actions
actions ---< action_logs
actions ---< agent_logs
```

## Table Design Notes

### `machines`

- Holds inventory, placement, health state, and whether the machine is in `manual` or `auto` action mode.
- `ip_address` uses PostgreSQL `INET` for native IP validation and filtering.
- `tags` and `metadata_json` stay in JSONB for flexible environment-specific attributes.

### `metrics`

- Implemented as a Timescale hypertable on `recorded_at`.
- Designed for append-heavy writes with limited updates.
- Stores the most query-relevant signals as typed columns rather than JSON.
- `labels` is JSONB for optional dimensions coming from heterogeneous collectors.

### `anomalies`

- Represents AI or rules-based anomaly detections.
- Keeps `anomaly_type`, `severity`, `status`, and `detected_at` as indexed columns for alert panels.
- `context` stores raw supporting evidence used by the model or rules.

### `predictions`

- Stores failure forecasts and risk estimates.
- `risk_score`, `failure_type`, and `generated_at` are promoted for filtering and ranking.
- `features` retains model input evidence without forcing a rigid schema too early.

### `actions`

- Captures simulated and live remediations.
- Tracks who requested and approved the action, whether approval was required, and the final execution state.
- `execution_result` and `payload` are JSONB because action handlers vary by integration target.

### `agent_logs`

- The main explainability table.
- `correlation_id` groups all Monitoring, Prediction, Decision, and Action steps for one decision cycle.
- Stores structured input/output plus natural-language reasoning.

### `audit_logs`

- Records security-sensitive and operator-sensitive events.
- Includes `actor_type`, source IP, and user agent for traceability.

## Indexing Strategy

### 1. Time-series reads

- `metrics(machine_id, recorded_at DESC)` is the primary dashboard/query index.
- `metrics(recorded_at DESC)` helps global recent-ingest and fleet-wide activity queries.
- `metrics(source, recorded_at DESC)` supports debugging data source quality and lag.

### 2. Hot operational queues

- `actions(status, requested_at DESC)` supports action work queues.
- Partial index `actions(approval_required, status, requested_at DESC) WHERE approval_required = TRUE` keeps approval lookups small and fast.
- `anomalies(status, detected_at DESC)` supports open-alert panels.

### 3. Severity and ranking

- `anomalies(severity, detected_at DESC)` accelerates critical-first alert views.
- `predictions(risk_score DESC, generated_at DESC)` speeds “highest risk now” queries.
- `predictions(failure_type, generated_at DESC)` supports failure-class drilldowns.

### 4. Correlated explainability lookups

- `agent_logs(correlation_id, created_at DESC)` reconstructs a single decision chain quickly.
- `agent_logs(machine_id, created_at DESC)` supports machine detail timelines.
- `action_logs(action_id, created_at DESC)` supports action lifecycle inspection.

### 5. Security and audit

- `user_roles(role_id, user_id)` supports authorization joins.
- `machine_credentials(machine_id, is_active)` is partial for active-key checks.
- `audit_logs(entity_type, entity_id, created_at DESC)` supports entity-level audit trace.
- `audit_logs(actor_id, created_at DESC)` supports user activity investigation.

### 6. JSONB indexes

- GIN on `metrics.labels`, `anomalies.context`, and `predictions.features` enables selective ad hoc filtering without over-indexing every JSON key.
- Keep JSONB indexes only where operators or services actually search inside those documents.

## Performance Strategy

### Metrics retention

- Compress `metrics` after 7 days.
- Retain raw metrics for 90 days in the POC.
- For longer history, create rollup materialized views for hourly/daily aggregates rather than keeping all raw points hot.

### Write behavior

- `metrics` is append-only and should avoid secondary indexes beyond the proven query patterns.
- `anomalies`, `predictions`, `actions`, and `agent_logs` are operationally smaller and can tolerate richer indexing.

### Query guidance

- Query recent windows with `machine_id` and bounded time ranges.
- Avoid scanning JSONB payloads before filtering on machine/time/status columns.
- Use `correlation_id` for cross-agent decision tracing instead of expensive text matching.

## Integrity Rules

- CHECK constraints enforce ranges like CPU, memory, and risk score.
- Enums ensure consistent state names for statuses, severities, and actions.
- Foreign keys use `CASCADE` only where child records are meaningless without the parent.
- Approval and execution timestamps stay nullable because actions can remain simulated or pending.

## Suggested Next DB Step

- Convert this DDL into versioned migrations, then add seed data and repository/query layers in the API and orchestrator services.
