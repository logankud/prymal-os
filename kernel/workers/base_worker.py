from __future__ import annotations

from abc import ABC, abstractmethod

from kernel.tasks.task import Task


class BaseWorker(ABC):
    def __init__(self, worker_id: str) -> None:
        self.worker_id = worker_id

    @abstractmethod
    def run(self, task: Task) -> Task:
        """Execute work for a task and return the updated task."""
        raise NotImplementedError