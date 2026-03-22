from __future__ import annotations

from typing import Iterable

from kernel.tasks.task import Task, TaskDomain
from kernel.workers.catalog import GENERAL_WORKER, WORKER_SPECS
from kernel.workers.spec import WorkerSpec


class WorkerRegistry:
    """
    Central registry for worker metadata.

    The registry manages:
    - worker lookup by id
    - worker lookup by supported domain
    - task-to-worker resolution
    - implementation resolution via WorkerSpec

    Worker definitions themselves live in catalog.py.
    """

    def __init__(
        self,
        workers: Iterable[WorkerSpec],
        default_worker: WorkerSpec | None = None,
    ) -> None:
        self._workers = tuple(workers)
        self._default_worker = default_worker or GENERAL_WORKER

    @property
    def workers(self) -> tuple[WorkerSpec, ...]:
        return self._workers

    @property
    def default_worker(self) -> WorkerSpec:
        return self._default_worker

    def get_worker_by_id(self, worker_id: str) -> WorkerSpec | None:
        for worker in self._workers:
            if worker.worker_id == worker_id:
                return worker

        if self._default_worker.worker_id == worker_id:
            return self._default_worker

        return None

    def get_workers_for_domain(self, domain: TaskDomain) -> list[WorkerSpec]:
        return [
            worker
            for worker in self._workers
            if worker.supports_domain(domain)
        ]

    def resolve_for_domain(self, domain: TaskDomain) -> WorkerSpec:
        candidates = self.get_workers_for_domain(domain)
        if candidates:
            return candidates[0]
        return self._default_worker

    def resolve_for_task(self, task: Task) -> WorkerSpec:
        return self.resolve_for_domain(task.domain)

    def resolve_implementation_class(self, worker_id: str):
        worker_spec = self.get_worker_by_id(worker_id)
        if worker_spec is None:
            raise ValueError(f"No worker spec found for worker_id='{worker_id}'")

        if worker_spec.implementation_cls is None:
            raise ValueError(
                f"Worker '{worker_id}' is declared but has no implementation class."
            )

        return worker_spec.implementation_cls


def build_worker_registry(
    workers: Iterable[WorkerSpec] | None = None,
    default_worker: WorkerSpec | None = None,
) -> WorkerRegistry:
    return WorkerRegistry(
        workers=workers or WORKER_SPECS,
        default_worker=default_worker or GENERAL_WORKER,
    )