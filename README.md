# Elio POC

Agentic AI platform for data center monitoring, anomaly detection, predictive maintenance, and autonomous remediation.

## Stack

- Backend: FastAPI, SQLAlchemy, Pydantic, async Python services
- Frontend: Next.js, Tailwind CSS
- Database: PostgreSQL + TimescaleDB
- Streaming: Redpanda (Kafka-compatible lightweight alternative)
- AI: scikit-learn/PyTorch-ready prediction services
- Auth: JWT + RBAC

## Services

- `apps/api-gateway`: public API, auth, RBAC, ingestion endpoints
- `apps/orchestrator`: agent workflow coordination
- `apps/analytics`: anomaly detection and predictive scoring
- `apps/action-runner`: executes or simulates remediation actions
- `apps/dashboard`: operator dashboard
- `packages/shared-py`: shared Python schemas, models, and utilities

## Quick Start

1. Start infrastructure:

```bash
docker compose up -d
```

2. Backend services are scaffolded under `apps/`.

3. Read the system design:

- [`docs/architecture.md`](/Users/salmanaslam/Projects/elio-poc/docs/architecture.md)

## Core Flows

- Metrics arrive from agents or API ingestion.
- Streaming events are normalized and stored in TimescaleDB.
- Monitoring, prediction, decision, and action agents exchange structured events.
- Every automated action is logged with reasoning and operator-visible explainability.
