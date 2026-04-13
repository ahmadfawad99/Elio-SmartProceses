# Agent Communication Protocol

## Goal

Provide a structured, auditable handoff format between the Monitoring, Prediction, Decision, and Action agents.

## Message Contract

Every inter-agent message uses two layers:

- `metadata`: routing and tracing data
- `payload`: typed business input for the target agent

## Envelope Shape

```json
{
  "metadata": {
    "correlation_id": "uuid",
    "machine_id": "uuid",
    "source_agent": "monitoring",
    "target_agent": "prediction",
    "created_at": "2026-04-10T12:00:00Z",
    "schema_version": "1.0"
  },
  "payload": {}
}
```

## Metadata Fields

- `correlation_id`: ties one full decision cycle together across all agents.
- `machine_id`: the infrastructure node the workflow is about.
- `source_agent`: agent producing the message. Null for workflow entry.
- `target_agent`: intended receiving agent.
- `created_at`: UTC timestamp for ordering and latency analysis.
- `schema_version`: allows forward-compatible protocol evolution.

## Agent Handoffs

### 1. Monitoring Agent

Input payload:

- `machine_id`
- `metric_window`
- `recent_anomalies`
- `action_mode`

Output payload:

- `health_summary`
- `anomaly_candidates`
- `priority_level`
- `reasoning`

### 2. Prediction Agent

Input payload:

- `machine_id`
- `metric_window`
- `anomaly_candidates`

Output payload:

- `failure_predictions`
- `risk_score`
- `time_to_failure_minutes`
- `reasoning`

### 3. Decision Agent

Input payload:

- `machine_id`
- `monitoring_output`
- `prediction_output`
- `action_mode`

Output payload:

- `recommended_action`
- `confidence`
- `approval_required`
- `reasoning`

### 4. Action Agent

Input payload:

- `machine_id`
- `decision_output`

Output payload:

- `execution_status`
- `executed_action`
- `side_effects`
- `reasoning`

## Execution Trace

Each agent execution produces a log entry containing:

- the full inbound `metadata`
- `input_payload`
- `output_payload`
- `reasoning`

This execution trace becomes the explainability spine for dashboards, audits, and debugging.

## Current Implementation

- Protocol builders live in [`apps/orchestrator/app/services/protocol.py`](/Users/salmanaslam/Projects/elio-poc/apps/orchestrator/app/services/protocol.py)
- Agent classes live in [`apps/orchestrator/app/services/agents.py`](/Users/salmanaslam/Projects/elio-poc/apps/orchestrator/app/services/agents.py)
- Pipeline orchestration lives in [`apps/orchestrator/app/services/agent_pipeline.py`](/Users/salmanaslam/Projects/elio-poc/apps/orchestrator/app/services/agent_pipeline.py)
