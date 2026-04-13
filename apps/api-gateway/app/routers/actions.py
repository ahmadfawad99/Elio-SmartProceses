from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from shared.enums import ActionStatus
from shared.schemas import (
    ActionDecisionRequest,
    ActionRecord,
    ActionRequest,
    ActionStatusUpdate,
    ListResponse,
)

from ..services.store import store

router = APIRouter(prefix="/actions", tags=["actions"])


@router.post("", response_model=ActionRecord)
async def create_action(payload: ActionRequest) -> ActionRecord:
    return store.create_action(payload)


@router.post("/from-decision", response_model=ActionRecord)
async def create_action_from_decision(payload: ActionDecisionRequest) -> ActionRecord:
    return store.create_action(
        ActionRequest(
            machine_id=payload.machine_id,
            action_type=payload.decision_output.recommended_action,
            simulated=payload.simulated,
            approval_required=payload.decision_output.approval_required,
            reasoning=payload.decision_output.reasoning,
            payload={"decision_confidence": payload.decision_output.confidence},
        )
    )


@router.get("", response_model=ListResponse)
async def list_actions(
    machine_id: UUID | None = None,
    status: ActionStatus | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> ListResponse:
    items = store.list_actions(machine_id=machine_id, status=status, limit=limit)
    return ListResponse(items=items, total=len(items))


@router.patch("/{action_id}", response_model=ActionRecord)
async def update_action_status(action_id: UUID, payload: ActionStatusUpdate) -> ActionRecord:
    updated = store.update_action(action_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="Action not found")
    return updated
