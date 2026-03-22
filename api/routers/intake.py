from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_intake_service
from entities import IntakeRequest, IntakeResponse, TaskResponse
from kernel.intake.intake_service import IntakeService

router = APIRouter(prefix="/intake", tags=["intake"])


@router.post("", response_model=IntakeResponse)
async def intake(
    request: IntakeRequest,
    intake_service: IntakeService = Depends(get_intake_service),
) -> IntakeResponse:
    try:
        tasks = await intake_service.process(
            text=request.text,
            source=request.source,
            event_type=request.event_type,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return IntakeResponse(
        tasks_created=len(tasks),
        tasks=[TaskResponse.from_task(t) for t in tasks],
    )
