from uuid import uuid4

from shared.enums import AgentName
from shared.schemas import (
    ActionAgentInput,
    AgentEnvelope,
    OrchestrationResult,
    DecisionAgentInput,
    MonitoringAgentInput,
    PredictionAgentInput,
)

from .agents import (
    ActionAgentService,
    DecisionAgentService,
    MonitoringAgentService,
    PredictionAgentService,
)
from .protocol import build_envelope, build_execution_log


monitoring_agent = MonitoringAgentService()
prediction_agent = PredictionAgentService()
decision_agent = DecisionAgentService()
action_agent = ActionAgentService()


def _run_agent(agent, envelope: AgentEnvelope, trace: list):
    output = agent.handle(envelope)
    trace.append(
        build_execution_log(
            envelope=envelope,
            output_payload=output.model_dump(mode="json"),
            reasoning=output.reasoning,
        )
    )
    return output


def run_agent_pipeline(payload: MonitoringAgentInput) -> OrchestrationResult:
    correlation_id = uuid4()
    trace = []

    monitoring_envelope = build_envelope(
        correlation_id=correlation_id,
        machine_id=payload.machine_id,
        target_agent=AgentName.monitoring,
        payload=payload.model_dump(mode="json"),
    )
    monitoring_output = _run_agent(monitoring_agent, monitoring_envelope, trace)

    prediction_input = PredictionAgentInput(
        machine_id=payload.machine_id,
        metric_window=payload.metric_window,
        anomaly_candidates=monitoring_output.anomaly_candidates,
    )
    prediction_envelope = build_envelope(
        correlation_id=correlation_id,
        machine_id=payload.machine_id,
        source_agent=AgentName.monitoring,
        target_agent=AgentName.prediction,
        payload=prediction_input.model_dump(mode="json"),
    )
    prediction_output = _run_agent(prediction_agent, prediction_envelope, trace)

    decision_input = DecisionAgentInput(
        machine_id=payload.machine_id,
        monitoring_output=monitoring_output,
        prediction_output=prediction_output,
        action_mode=payload.action_mode,
    )
    decision_envelope = build_envelope(
        correlation_id=correlation_id,
        machine_id=payload.machine_id,
        source_agent=AgentName.prediction,
        target_agent=AgentName.decision,
        payload=decision_input.model_dump(mode="json"),
    )
    decision_output = _run_agent(decision_agent, decision_envelope, trace)

    action_input = ActionAgentInput(
        machine_id=payload.machine_id,
        decision_output=decision_output,
    )
    action_envelope = build_envelope(
        correlation_id=correlation_id,
        machine_id=payload.machine_id,
        source_agent=AgentName.decision,
        target_agent=AgentName.action,
        payload=action_input.model_dump(mode="json"),
    )
    action_output = _run_agent(action_agent, action_envelope, trace)

    return OrchestrationResult(
        correlation_id=correlation_id,
        machine_id=payload.machine_id,
        monitoring_output=monitoring_output,
        prediction_output=prediction_output,
        decision_output=decision_output,
        action_output=action_output,
        communication_trace=trace,
    )
