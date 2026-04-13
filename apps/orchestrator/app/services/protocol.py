from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from shared.enums import AgentName
from shared.schemas import AgentEnvelope, AgentExecutionLog, AgentMessageMetadata


def build_envelope(
    *,
    correlation_id: UUID,
    machine_id: UUID,
    target_agent: AgentName,
    payload: dict,
    source_agent: AgentName | None = None,
) -> AgentEnvelope:
    return AgentEnvelope(
        metadata=AgentMessageMetadata(
            correlation_id=correlation_id,
            machine_id=machine_id,
            source_agent=source_agent,
            target_agent=target_agent,
            created_at=datetime.now(timezone.utc),
        ),
        payload=payload,
    )


def build_execution_log(
    *,
    envelope: AgentEnvelope,
    output_payload: dict,
    reasoning: str,
) -> AgentExecutionLog:
    return AgentExecutionLog(
        metadata=envelope.metadata,
        input_payload=envelope.payload,
        output_payload=output_payload,
        reasoning=reasoning,
    )
