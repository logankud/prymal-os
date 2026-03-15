from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_task_store
from entities import CreateTaskRequest, TaskResponse
from interfaces.inputs.sample_task import build_sample_task
from kernel.tasks.task import Objective, Task
from kernel.tasks.task_store import TaskStore

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/sample", response_model=TaskResponse)
def create_sample_task(
    task_store: TaskStore = Depends(get_task_store),
) -> TaskResponse:
    task = build_sample_task()
    task_store.create_task(task)
    persisted = task_store.get_task(task.task_id)
    if persisted is None:
        raise HTTPException(status_code=500, detail="Sample task was not persisted.")
    return TaskResponse.from_task(persisted)


@router.post("", response_model=TaskResponse)
def create_task(
    payload: CreateTaskRequest,
    task_store: TaskStore = Depends(get_task_store),
) -> TaskResponse:
    task = Task(
        objective=Objective(
            action=payload.action,
            subject=payload.subject,
            outcome=payload.outcome,
        ),
        domain=payload.domain,
        created_by=payload.created_by,
        expected_outputs=payload.expected_outputs,
    )

    task_store.create_task(task)
    persisted = task_store.get_task(task.task_id)

    if persisted is None:
        raise HTTPException(status_code=500, detail="Task was not persisted.")

    return TaskResponse.from_task(persisted)

@router.get("", response_model=list[TaskResponse])
def list_tasks(
    task_store: TaskStore = Depends(get_task_store),
) -> list[TaskResponse]:
    tasks = task_store.list_tasks()
    return [TaskResponse.from_task(task) for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    task_store: TaskStore = Depends(get_task_store),
) -> TaskResponse:
    task = task_store.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    return TaskResponse.from_task(task)
