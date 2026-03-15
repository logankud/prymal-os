from kernel.workers.registry import build_worker_registry

class TaskRouter:
    def __init__(self, registry=None) -> None:
        self.registry = registry or build_worker_registry()

    def route_task(self, task):
        return self.registry.resolve_for_task(task).worker_id


