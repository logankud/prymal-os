from __future__ import annotations

from fastapi import Request

from kernel.intake.intake_service import IntakeService
from kernel.scheduler.dispatcher import TaskDispatcher
from kernel.tasks.task_store import TaskStore
from kernel.work_request.work_request_store import WorkRequestStore


def get_task_store(request: Request) -> TaskStore:
    return request.app.state.task_store


def get_dispatcher(request: Request) -> TaskDispatcher:
    return request.app.state.dispatcher


def get_intake_service(request: Request) -> IntakeService:
    return request.app.state.intake_service


def get_work_request_store(request: Request) -> WorkRequestStore:
    return request.app.state.work_request_store
