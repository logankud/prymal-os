from __future__ import annotations

from kernel.tasks.task import Task, TaskStatus
from kernel.tasks.task_store import TaskStore
from kernel.workers.worker_runner import WorkerRunner


class TaskExecutor:
    def __init__(self, task_store: TaskStore) -> None:
        self.task_store = task_store
        self.runner = WorkerRunner(task_store=task_store)

    def execute_task_by_id(self, task_id: str) -> Task:
        task = self.task_store.get_task(task_id)

        if task is None:
            raise ValueError(f"Task '{task_id}' not found.")

        if task.status != TaskStatus.QUEUED:
            raise ValueError(
                f"Task '{task.task_id}' must be QUEUED to execute. "
                f"Current status: '{task.status.value}'."
            )

        if not task.owner_worker:
            raise ValueError(
                f"Task '{task.task_id}' has no owner_worker and cannot be executed."
            )

        return self.runner.run_task(task)

    def execute_queued_tasks(self, worker_id: str | None = None) -> int:
        queued_tasks = self.task_store.list_tasks_by_status(TaskStatus.QUEUED)

        if worker_id is not None:
            queued_tasks = [
                task for task in queued_tasks if task.owner_worker == worker_id
            ]

        execution_count = 0

        for task in queued_tasks:
            self.runner.run_task(task)
            execution_count += 1

        return execution_count