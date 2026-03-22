from __future__ import annotations

from kernel.tasks.task import Task
from kernel.workers.base_worker import BaseWorker

class MarketingWorker(BaseWorker):
    def __init__(self) -> None:
        super().__init__(worker_id="cmo_worker")

    def run(self, task: Task) -> Task:
        artifact = (
            f"marketing_worker analyzed task '{task.task_id}' "
            f"for subject '{task.objective.subject}'. "
            f"Recommended marketing workflow: define audience, define offer, "
            f"define channel, define creative angle."
        )

        task.add_artifact(artifact)
        return task