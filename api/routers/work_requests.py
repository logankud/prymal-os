from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_work_request_store
from kernel.work_request.work_request import WorkRequest
from kernel.work_request.work_request_store import WorkRequestStore

router = APIRouter(prefix="/work-requests", tags=["work-requests"])


@router.get("/{work_request_id}")
def get_work_request(
    work_request_id: str,
    store: WorkRequestStore = Depends(get_work_request_store),
) -> dict:
    wr = store.get(work_request_id)
    if wr is None:
        raise HTTPException(status_code=404, detail=f"WorkRequest '{work_request_id}' not found.")
    return wr.to_dict()


@router.get("")
def list_work_requests(
    store: WorkRequestStore = Depends(get_work_request_store),
) -> list[dict]:
    return [wr.to_dict() for wr in store.list_all()]
