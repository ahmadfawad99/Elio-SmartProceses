# Elio POC Architecture

## Goals

- Monitor infrastructure in real time.
- Detect anomalies and forecast failures before incidents occur.
- Run a multi-agent decision loop with explainable outputs.
- Allow safe autonomous or manual remediation.

## High-Level Architecture

```text
+--------------------+      +----------------------+      +----------------------+
| Edge Collectors    | ---> | API Gateway          | ---> | Redpanda Event Bus   |
| - host agents      |      | - auth / RBAC        |      | - metrics.raw        |
| - external APIs    |      | - ingestion APIs     |      | - metrics.enriched   |
+--------------------+      +----------------------+      | - anomalies.detected |
                                                           | - predictions.ready  |
                                                           | - decisions.made     |
                                                           | - actions.requested  |
                                                           +----------+-----------+
                                                                      |
                                                                      v
                     +---------------------+      +-------------------------+
                     | Analytics Service   | ---> | Agent Orchestrator      |
                     | - anomaly detection |      | - monitoring agent      |
                     | - forecasting       |      | - prediction agent      |
                     | - risk scoring      |      | - decision agent        |
                     +----------+----------+      | - action agent          |
                                |                 +-----------+-------------+
                                v                             |
                    +------------------------+                v
                    | TimescaleDB / Postgres | <--- +----------------------+
                    | - metrics hypertables  |      | Action Runner         |
                    | - anomalies            |      | - cooling simulation  |
                    | - predictions          |      | - load balancing      |
                    | - actions              |      | - alerts              |
                    | - agent logs           |      +----------+-----------+
                    +-----------+------------+                 |
                                |                              v
                                v                   +----------------------+
                    +-------------------------+     | Dashboard            |
                    | Explainability Layer     | --> | - realtime charts   |
                    | - decision reasoning     |     | - AI decisions      |
                    | - audit narrative        |     | - action logs       |
                    +-------------------------+     +----------------------+
```

## Services Breakdown

### 1. API Gateway

- Validates JWTs and enforces RBAC.
- Accepts agent-based and API-based ingestion.
- Exposes query APIs for dashboard and operators.
- Emits canonical events to the streaming bus.

### 2. Analytics Service

- Consumes normalized metrics from the bus.
- Runs anomaly detection on metric windows.
- Produces predictive maintenance forecasts and risk scores.
- Persists AI outputs for downstream agent use.

### 3. Agent Orchestrator

- Manages structured communication between agents.
- Guarantees each step has typed input/output.
- Stores reasoning traces in `agent_logs`.
- Supports manual-approval and autonomous modes.

### 4. Action Runner

- Executes simulated or real actions.
- Enforces policy constraints and cooldown windows.
- Reports success/failure back onto the bus.

### 5. Dashboard

- Shows real-time metrics, alerts, agent outputs, and actions.
- Lets operators toggle between manual and auto mode.
- Makes every AI decision inspectable.

## Agentic System

### Monitoring Agent

Input:

- Machine state
- Recent metric windows
- Current anomalies

Output:

- `health_summary`
- `anomaly_candidates`
- `priority_level`
- `reasoning`

### Prediction Agent

Input:

- Enriched metric windows
- Historical incidents
- Current anomaly candidates

Output:

- `failure_predictions`
- `risk_score`
- `time_to_failure_minutes`
- `reasoning`

### Decision Agent

Input:

- Monitoring output
- Prediction output
- Machine policies
- Automation mode

Output:

- `recommended_action`
- `confidence`
- `approval_required`
- `reasoning`

### Action Agent

Input:

- Decision payload
- Environment constraints
- Allowed remediations

Output:

- `execution_status`
- `executed_action`
- `side_effects`
- `reasoning`

## Event Topics

- `metrics.raw`
- `metrics.normalized`
- `anomalies.detected`
- `predictions.ready`
- `decisions.made`
- `actions.requested`
- `actions.completed`
- `audit.events`

## Data Flow

1. Collectors send metrics to the API Gateway.
2. Gateway validates, normalizes, and publishes metric events.
3. Analytics consumes events, performs anomaly detection and forecasting, and stores results.
4. Orchestrator invokes Monitoring Agent, then Prediction Agent, then Decision Agent, then Action Agent.
5. Action Runner simulates or executes actions and emits completion events.
6. Dashboard subscribes through API/WebSocket endpoints for near real-time visibility.
7. Every stage writes reasoning and audit records.

## Database Design

### Tables

- `users`
- `roles`
- `user_roles`
- `machines`
- `metrics`
- `anomalies`
- `predictions`
- `actions`
- `agent_logs`
- `audit_logs`

### Performance Notes

- Use a Timescale hypertable for `metrics` partitioned by `recorded_at`.
- Index `machine_id, recorded_at DESC` for fast recent-window queries.
- Keep JSONB for agent payloads and reasoning, but promote key filter fields to columns.
- Add retention and compression policies for time-series data.

## Security

- JWT access tokens for all operator and service access.
- RBAC roles: `admin`, `operator`, `viewer`, `service`.
- Signed ingestion keys for machine/agent submissions.
- Audit logging for all auth, policy, and action changes.
- Manual approval gates for high-risk actions.

## Recommended Folder Structure

```text
elio-poc/
  apps/
    api-gateway/
    analytics/
    orchestrator/
    action-runner/
    dashboard/
  packages/
    shared-py/
  infra/
    db/
    redpanda/
  docs/
```

## Why Redpanda Instead of Kafka

- Kafka-compatible API with lighter local operational overhead.
- Better fit for a POC while preserving a clean migration path to Kafka if scale demands it.
