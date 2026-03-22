from __future__ import annotations

from kernel.tasks.task import Task, TaskStatus
from kernel.tasks.task_store import TaskStore
from kernel.workers.worker_factory import get_worker

class WorkerRunner:
    def __init__(self, task_store: TaskStore | None = None) -> None:
        self.task_store = task_store

    def _persist_if_available(self, task: Task) -> None:
        if self.task_store is not None:
            self.task_store.update_task(task)

    def run_task(self, task: Task) -> Task:
        if not task.owner_worker:
            raise ValueError(
                f"Task '{task.task_id}' has no owner_worker and cannot be executed."
            )

        worker = get_worker(task.owner_worker)

        task.update_status(TaskStatus.RUNNING)
        self._persist_if_available(task)

        try:
            updated_task = worker.run(task)
            updated_task.update_status(TaskStatus.COMPLETED)
            self._persist_if_available(updated_task)
            return updated_task
        except Exception:
            task.update_status(TaskStatus.FAILED)
            self._persist_if_available(task)
            raise