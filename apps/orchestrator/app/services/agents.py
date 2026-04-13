from __future__ import annotations

from datetime import datetime, timezone

from shared.enums import ActionMode, ActionStatus, ActionType, AgentName, Severity
from shared.schemas import (
    ActionAgentInput,
    ActionAgentOutput,
    AgentEnvelope,
    AnomalyEvent,
    DecisionAgentInput,
    DecisionAgentOutput,
    MonitoringAgentInput,
    MonitoringAgentOutput,
    PredictionAgentInput,
    PredictionAgentOutput,
    PredictionEvent,
)


class BaseAgent:
    name: AgentName

    def handle(self, envelope: AgentEnvelope):
        raise NotImplementedError


class MonitoringAgentService(BaseAgent):
    name = AgentName.monitoring

    def handle(self, envelope: AgentEnvelope) -> MonitoringAgentOutput:
        payload = MonitoringAgentInput.model_validate(envelope.payload)
        metrics = payload.metric_window
        latest = metrics[-1]
        cpu_peak = max(item.cpu_usage for item in metrics)
        memory_peak = max(item.memory_usage for item in metrics)
        temp_peak = max(item.temperature_c for item in metrics)
        avg_cpu = sum(item.cpu_usage for item in metrics) / len(metrics)

        anomaly_candidates = list(payload.recent_anomalies)
        if temp_peak >= 80 or cpu_peak >= 88:
            anomaly_candidates.append(
                AnomalyEvent(
                    machine_id=payload.machine_id,
                    severity=Severity.high if temp_peak >= 84 or cpu_peak >= 92 else Severity.medium,
                    anomaly_score=round(max(cpu_peak, memory_peak) / 100, 3),
                    anomaly_type="resource_pressure",
                    summary="Monitoring agent detected rising load and thermal stress.",
                    detected_at=datetime.now(timezone.utc),
                    context={
                        "cpu_peak": round(cpu_peak, 2),
                        "memory_peak": round(memory_peak, 2),
                        "temperature_peak": round(temp_peak, 2),
                    },
                    reasoning="Threshold and trend checks flagged elevated compute and thermal pressure.",
                )
            )

        if temp_peak >= 86 or cpu_peak >= 94:
            priority = Severity.critical
        elif temp_peak >= 80 or avg_cpu >= 75:
            priority = Severity.high
        elif avg_cpu >= 55:
            priority = Severity.medium
        else:
            priority = Severity.low

        return MonitoringAgentOutput(
            health_summary=(
                f"Current machine posture shows avg CPU {avg_cpu:.1f}% and peak temperature {temp_peak:.1f}C."
            ),
            anomaly_candidates=anomaly_candidates,
            priority_level=priority,
            reasoning=(
                "Monitoring agent evaluated the metric window for saturation and heat buildup. "
                f"Observed CPU peak {cpu_peak:.1f}%, memory peak {memory_peak:.1f}%, and thermal peak {temp_peak:.1f}C."
            ),
        )


class PredictionAgentService(BaseAgent):
    name = AgentName.prediction

    def handle(self, envelope: AgentEnvelope) -> PredictionAgentOutput:
        payload = PredictionAgentInput.model_validate(envelope.payload)
        metrics = payload.metric_window
        latest = metrics[-1]
        avg_cpu = sum(item.cpu_usage for item in metrics) / len(metrics)
        avg_memory = sum(item.memory_usage for item in metrics) / len(metrics)
        max_temp = max(item.temperature_c for item in metrics)
        recent_severity_bonus = 0.08 * len(
            [
                anomaly
                for anomaly in payload.anomaly_candidates
                if anomaly.severity in {Severity.high, Severity.critical}
            ]
        )
        risk_score = min(
            0.99,
            round(
                (avg_cpu / 100) * 0.32
                + (avg_memory / 100) * 0.20
                + min(max_temp / 95, 1.0) * 0.40
                + recent_severity_bonus,
                3,
            ),
        )
        time_to_failure = max(5, int((1 - risk_score) * 180))
        failure_type = "thermal_overload" if max_temp >= 82 else "resource_degradation"

        prediction = PredictionEvent(
            machine_id=payload.machine_id,
            risk_score=risk_score,
            prediction_type="predictive_maintenance",
            failure_type=failure_type,
            time_to_failure_minutes=time_to_failure,
            generated_at=datetime.now(timezone.utc),
            features={
                "avg_cpu": round(avg_cpu, 2),
                "avg_memory": round(avg_memory, 2),
                "max_temperature": round(max_temp, 2),
                "anomaly_count": len(payload.anomaly_candidates),
            },
            reasoning=(
                "Prediction agent combined rolling utilization, thermal maxima, and anomaly history "
                f"to estimate near-term failure risk for {latest.machine_id}."
            ),
        )

        return PredictionAgentOutput(
            failure_predictions=[prediction],
            risk_score=risk_score,
            time_to_failure_minutes=time_to_failure,
            reasoning=(
                f"Prediction agent estimated risk score {risk_score:.2f} with time-to-failure "
                f"{time_to_failure} minutes based on sustained load and temperature exposure."
            ),
        )


class DecisionAgentService(BaseAgent):
    name = AgentName.decision

    def handle(self, envelope: AgentEnvelope) -> DecisionAgentOutput:
        payload = DecisionAgentInput.model_validate(envelope.payload)
        risk = payload.prediction_output.risk_score
        priority = payload.monitoring_output.priority_level

        if risk >= 0.85 or priority == Severity.critical:
            action = ActionType.cooling_adjustment
            confidence = 0.91
        elif risk >= 0.70:
            action = ActionType.load_balance
            confidence = 0.82
        elif risk >= 0.55:
            action = ActionType.alert
            confidence = 0.73
        else:
            action = ActionType.alert
            confidence = 0.60

        approval_required = payload.action_mode == ActionMode.manual or risk >= 0.90

        return DecisionAgentOutput(
            recommended_action=action,
            confidence=confidence,
            approval_required=approval_required,
            reasoning=(
                "Decision agent selected the least disruptive response that addresses predicted risk. "
                f"Priority is {priority.value}, risk score is {risk:.2f}, and action mode is {payload.action_mode.value}."
            ),
        )


class ActionAgentService(BaseAgent):
    name = AgentName.action

    def handle(self, envelope: AgentEnvelope) -> ActionAgentOutput:
        payload = ActionAgentInput.model_validate(envelope.payload)
        if payload.decision_output.approval_required:
            status = ActionStatus.pending
            side_effects = ["Awaiting operator approval"]
        else:
            status = ActionStatus.simulated
            side_effects = ["Simulation executed", "No external infrastructure was changed"]

        return ActionAgentOutput(
            execution_status=status,
            executed_action=payload.decision_output.recommended_action,
            side_effects=side_effects,
            reasoning=(
                "Action agent transformed the decision payload into an executable remediation plan. "
                f"Selected action {payload.decision_output.recommended_action.value} with "
                f"{'approval required' if payload.decision_output.approval_required else 'simulation mode enabled'}."
            ),
        )
