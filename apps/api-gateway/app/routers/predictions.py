from uuid import UUID

from fastapi import APIRouter, Query

from shared.schemas import ListResponse, PredictionEvent

from ..services.store import store

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("", response_model=PredictionEvent)
async def create_prediction(payload: PredictionEvent) -> PredictionEvent:
    return store.add_prediction(payload)


@router.get("", response_model=ListResponse)
async def list_predictions(
    machine_id: UUID | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> ListResponse:
    items = store.list_predictions(machine_id=machine_id, limit=limit)
    return ListResponse(items=items, total=len(items))
