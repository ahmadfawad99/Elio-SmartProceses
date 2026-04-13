from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from shared.enums import ActionStatus, Severity
from shared.schemas import (
    ActionRecord,
    ActionRequest,
    ActionStatusUpdate,
    AnomalyEvent,
    MetricPointIn,
    PredictionEvent,
)


class InMemoryStore:
    def __init__(self) -> None:
        self.metrics: list[MetricPointIn] = []
        self.anomalies: list[AnomalyEvent] = []
        self.predictions: list[PredictionEvent] = []
        self.actions: list[ActionRecord] = []

    def add_metrics(self, metrics: list[MetricPointIn]) -> list[MetricPointIn]:
        self.metrics.extend(metrics)
        return metrics

    def list_metrics(self, machine_id: UUID | None = None, limit: int = 100) -> list[MetricPointIn]:
        items = self.metrics
        if machine_id:
            items = [metric for metric in items if metric.machine_id == machine_id]
        return sorted(items, key=lambda metric: metric.recorded_at, reverse=True)[:limit]

    def add_anomaly(self, anomaly: AnomalyEvent) -> AnomalyEvent:
        record = anomaly.model_copy(update={"id": anomaly.id or uuid4()})
        self.anomalies.append(record)
        return record

    def list_anomalies(
        self,
        machine_id: UUID | None = None,
        severity: Severity | None = None,
        limit: int = 100,
    ) -> list[AnomalyEvent]:
        items = self.anomalies
        if machine_id:
            items = [anomaly for anomaly in items if anomaly.machine_id == machine_id]
        if severity:
            items = [anomaly for anomaly in items if anomaly.severity == severity]
        return sorted(items, key=lambda anomaly: anomaly.detected_at, reverse=True)[:limit]

    def add_prediction(self, prediction: PredictionEvent) -> PredictionEvent:
        record = prediction.model_copy(update={"id": prediction.id or uuid4()})
        self.predictions.append(record)
        return record

    def list_predictions(self, machine_id: UUID | None = None, limit: int = 100) -> list[PredictionEvent]:
        items = self.predictions
        if machine_id:
            items = [prediction for prediction in items if prediction.machine_id == machine_id]
        return sorted(items, key=lambda prediction: prediction.generated_at, reverse=True)[:limit]

    def create_action(self, request: ActionRequest) -> ActionRecord:
        now = datetime.now(timezone.utc)
        status = ActionStatus.pending if request.approval_required else ActionStatus.simulated
        executed_at = None if request.approval_required else now
        execution_result = (
            {}
            if request.approval_required
            else {"mode": "simulation" if request.simulated else "live", "accepted": True}
        )
        record = ActionRecord(
            id=uuid4(),
            machine_id=request.machine_id,
            action_type=request.action_type,
            status=status,
            simulated=request.simulated,
            approval_required=request.approval_required,
            requested_by=request.requested_by,
            requested_at=now,
            executed_at=executed_at,
            reasoning=request.reasoning,
            payload=request.payload,
            execution_result=execution_result,
        )
        self.actions.append(record)
        return record

    def list_actions(
        self,
        machine_id: UUID | None = None,
        status: ActionStatus | None = None,
        limit: int = 100,
    ) -> list[ActionRecord]:
        items = self.actions
        if machine_id:
            items = [action for action in items if action.machine_id == machine_id]
        if status:
            items = [action for action in items if action.status == status]
        return sorted(items, key=lambda action: action.requested_at, reverse=True)[:limit]

    def update_action(self, action_id: UUID, update: ActionStatusUpdate) -> ActionRecord | None:
        for index, action in enumerate(self.actions):
            if action.id == action_id:
                executed_at = action.executed_at
                if update.status in {
                    ActionStatus.executed,
                    ActionStatus.failed,
                    ActionStatus.simulated,
                }:
                    executed_at = datetime.now(timezone.utc)
                updated_action = action.model_copy(
                    update={
                        "status": update.status,
                        "executed_at": executed_at,
                        "execution_result": update.execution_result,
                    }
                )
                self.actions[index] = updated_action
                return updated_action
        return None


store = InMemoryStore()
