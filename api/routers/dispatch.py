from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_dispatcher
from entities import DispatchResponse
from kernel.scheduler.dispatcher import TaskDispatcher

router = APIRouter(prefix="/dispatch", tags=["dispatch"])


@router.post("", response_model=DispatchResponse)
def dispatch_created_tasks(
    dispatcher: TaskDispatcher = Depends(get_dispatcher),
) -> DispatchResponse:
    dispatched_count = dispatcher.dispatch_created_tasks()
    return DispatchResponse(dispatched_count=dispatched_count)
