from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Tuple

from kernel.tasks.task import TaskDomain

if TYPE_CHECKING:
    from kernel.workers.base_worker import BaseWorker


@dataclass(frozen=True)
class WorkerSpec:
    """
    Declarative metadata about a worker.
    """

    worker_id: str
    supported_domains: Tuple[TaskDomain, ...]
    display_name: str | None = None
    description: str | None = None
    tags: Tuple[str, ...] = field(default_factory=tuple)
    implementation_cls: type["BaseWorker"] | None = None

    @property
    def name(self) -> str:
        return self.worker_id

    def supports_domain(self, domain: TaskDomain) -> bool:
        return domain in self.supported_domains

    def is_executable(self) -> bool:
        return self.implementation_cls is not None