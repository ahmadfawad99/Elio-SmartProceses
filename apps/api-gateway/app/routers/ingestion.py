from uuid import UUID

from fastapi import APIRouter, Query

from shared.schemas import ListResponse, MetricIngestionRequest, MetricIngestionResponse

from ..services.store import store

router = APIRouter(tags=["ingestion"])


@router.post("/metrics", response_model=MetricIngestionResponse)
async def ingest_metrics(payload: MetricIngestionRequest) -> MetricIngestionResponse:
    accepted = store.add_metrics(payload.metrics)
    machine_ids = list(dict.fromkeys(metric.machine_id for metric in accepted))
    return MetricIngestionResponse(accepted_count=len(accepted), machine_ids=machine_ids)


@router.get("/metrics", response_model=ListResponse)
async def list_metrics(
    machine_id: UUID | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> ListResponse:
    items = store.list_metrics(machine_id=machine_id, limit=limit)
    return ListResponse(items=items, total=len(items))
