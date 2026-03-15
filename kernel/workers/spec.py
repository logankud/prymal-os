from dataclasses import dataclass, field
from typing import Tuple

from kernel.tasks.task import TaskDomain


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

    @property
    def name(self) -> str:
        """
        Convenience alias so callers can use `spec.name`
        """
        return self.worker_id

    def supports_domain(self, domain: TaskDomain) -> bool:
        return domain in self.supported_domains