from __future__ import annotations

from fastapi import Request

from kernel.intake.intake_service import IntakeService
from kernel.scheduler.dispatcher import TaskDispatcher
from kernel.tasks.task_store import TaskStore


def get_task_store(request: Request) -> TaskStore:
    return request.app.state.task_store


def get_dispatcher(request: Request) -> TaskDispatcher:
    return request.app.state.dispatcher


def get_intake_service(request: Request) -> IntakeService:
    return request.app.state.intake_service
