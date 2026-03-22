from __future__ import annotations

from kernel.workers.base_worker import BaseWorker
from kernel.workers.registry import build_worker_registry


def get_worker(worker_id: str) -> BaseWorker:
    """
    Resolve a worker_id to a concrete worker instance using the registry/catalog
    as the source of truth.
    """
    registry = build_worker_registry()
    worker_cls = registry.resolve_implementation_class(worker_id)
    return worker_cls()