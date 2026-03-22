from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_task_store
from kernel.runtime.task_executor import TaskExecutor
from kernel.tasks.task_store import TaskStore

router = APIRouter(prefix="/execute", tags=["execution"])

@router.post("/queued")
def execute_queued_tasks(
    task_store: TaskStore = Depends(get_task_store),
) -> dict[str, int]:
    executor = TaskExecutor(task_store=task_store)
    executed_count = executor.execute_queued_tasks()
    return {"executed_count": executed_count}