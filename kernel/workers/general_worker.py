from __future__ import annotations

from kernel.tasks.task import Task
from kernel.workers.base_worker import BaseWorker

class GeneralWorker(BaseWorker):
    def __init__(self) -> None:
        super().__init__(worker_id="general_worker")

    def run(self, task: Task) -> Task:
        artifact_note = (
            f"general_worker processed task '{task.task_id}' "
            f"for subject '{task.objective.subject}'."
        )

        task.artifacts.append(artifact_note)
        return task