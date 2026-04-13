from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from .enums import ActionMode, ActionStatus, ActionType, AgentName, Severity


class MetricPointIn(BaseModel):
    machine_id: UUID
    cpu_usage: float = Field(ge=0, le=100)
    memory_usage: float = Field(ge=0, le=100)
    temperature_c: float
    network_in_mbps: float = Field(ge=0)
    network_out_mbps: float = Field(ge=0)
    recorded_at: datetime
    source: str = "agent"


class MetricWindow(BaseModel):
    machine_id: UUID
    metrics: list[MetricPointIn] = Field(min_length=1)


class MetricIngestionRequest(BaseModel):
    metrics: list[MetricPointIn] = Field(min_length=1)


class MetricIngestionResponse(BaseModel):
    accepted_count: int
    machine_ids: list[UUID]
    status: str = "accepted"


class AnomalyEvent(BaseModel):
    id: UUID | None = None
    machine_id: UUID
    severity: Severity
    anomaly_score: float
    anomaly_type: str = "resource_pressure"
    summary: str
    detected_at: datetime
    context: dict[str, Any] = Field(default_factory=dict)
    reasoning: str = ""


class PredictionEvent(BaseModel):
    id: UUID | None = None
    machine_id: UUID
    risk_score: float = Field(ge=0, le=1)
    prediction_type: str = "predictive_maintenance"
    failure_type: str
    time_to_failure_minutes: int = Field(ge=0)
    generated_at: datetime
    features: dict[str, Any] = Field(default_factory=dict)
    reasoning: str


class MonitoringAgentInput(BaseModel):
    machine_id: UUID
    metric_window: list[MetricPointIn]
    recent_anomalies: list[AnomalyEvent] = Field(default_factory=list)
    action_mode: ActionMode = ActionMode.manual


class MonitoringAgentOutput(BaseModel):
    agent: AgentName = AgentName.monitoring
    health_summary: str
    anomaly_candidates: list[AnomalyEvent]
    priority_level: Severity
    reasoning: str


class PredictionAgentInput(BaseModel):
    machine_id: UUID
    metric_window: list[MetricPointIn]
    anomaly_candidates: list[AnomalyEvent]


class PredictionAgentOutput(BaseModel):
    agent: AgentName = AgentName.prediction
    failure_predictions: list[PredictionEvent]
    risk_score: float = Field(ge=0, le=1)
    time_to_failure_minutes: int = Field(ge=0)
    reasoning: str


class DecisionAgentInput(BaseModel):
    machine_id: UUID
    monitoring_output: MonitoringAgentOutput
    prediction_output: PredictionAgentOutput
    action_mode: ActionMode


class DecisionAgentOutput(BaseModel):
    agent: AgentName = AgentName.decision
    recommended_action: ActionType
    confidence: float = Field(ge=0, le=1)
    approval_required: bool
    reasoning: str


class ActionAgentInput(BaseModel):
    machine_id: UUID
    decision_output: DecisionAgentOutput


class ActionAgentOutput(BaseModel):
    agent: AgentName = AgentName.action
    execution_status: ActionStatus
    executed_action: ActionType
    side_effects: list[str] = Field(default_factory=list)
    reasoning: str


class AgentMessageMetadata(BaseModel):
    correlation_id: UUID
    machine_id: UUID
    source_agent: AgentName | None = None
    target_agent: AgentName
    created_at: datetime
    schema_version: str = "1.0"


class AgentEnvelope(BaseModel):
    metadata: AgentMessageMetadata
    payload: dict[str, Any]


class AgentExecutionLog(BaseModel):
    metadata: AgentMessageMetadata
    input_payload: dict[str, Any]
    output_payload: dict[str, Any]
    reasoning: str


class OrchestrationResult(BaseModel):
    correlation_id: UUID
    machine_id: UUID
    monitoring_output: MonitoringAgentOutput
    prediction_output: PredictionAgentOutput
    decision_output: DecisionAgentOutput
    action_output: ActionAgentOutput
    communication_trace: list[AgentExecutionLog]


class ActionRequest(BaseModel):
    machine_id: UUID
    action_type: ActionType
    simulated: bool = True
    approval_required: bool = False
    requested_by: UUID | None = None
    reasoning: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ActionRecord(BaseModel):
    id: UUID
    machine_id: UUID
    action_type: ActionType
    status: ActionStatus
    simulated: bool
    approval_required: bool
    requested_by: UUID | None = None
    requested_at: datetime
    executed_at: datetime | None = None
    reasoning: str
    payload: dict[str, Any] = Field(default_factory=dict)
    execution_result: dict[str, Any] = Field(default_factory=dict)


class ActionStatusUpdate(BaseModel):
    status: ActionStatus
    execution_result: dict[str, Any] = Field(default_factory=dict)


class ActionDecisionRequest(BaseModel):
    machine_id: UUID
    decision_output: DecisionAgentOutput
    simulated: bool = True


class ListResponse(BaseModel):
    items: list[Any]
    total: int
