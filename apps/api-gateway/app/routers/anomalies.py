from uuid import UUID

from fastapi import APIRouter, Query

from shared.enums import Severity
from shared.schemas import AnomalyEvent, ListResponse

from ..services.store import store

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.post("", response_model=AnomalyEvent)
async def create_anomaly(payload: AnomalyEvent) -> AnomalyEvent:
    return store.add_anomaly(payload)


@router.get("", response_model=ListResponse)
async def list_anomalies(
    machine_id: UUID | None = None,
    severity: Severity | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> ListResponse:
    items = store.list_anomalies(machine_id=machine_id, severity=severity, limit=limit)
    return ListResponse(items=items, total=len(items))
