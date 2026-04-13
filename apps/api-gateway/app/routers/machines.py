from fastapi import APIRouter

router = APIRouter(tags=["machines"])


@router.get("/machines")
async def list_machines() -> list[dict[str, str]]:
    return []
