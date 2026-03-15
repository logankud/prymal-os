from __future__ import annotations

from fastapi import Request

from kernel.scheduler.dispatcher import TaskDispatcher
from kernel.tasks.task_store import TaskStore


def get_task_store(request: Request) -> TaskStore:
    return request.app.state.task_store


def get_dispatcher(request: Request) -> TaskDispatcher:
    return request.app.state.dispatcher
