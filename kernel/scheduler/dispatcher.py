from kernel.tasks.task import TaskStatus
from kernel.tasks.task_store import TaskStore
from kernel.scheduler.router import TaskRouter


class TaskDispatcher:
    """
    Minimal dispatcher:
    - finds newly created tasks
    - assigns a worker
    - moves them to QUEUED
    """

    def __init__(self, task_store: TaskStore, router: TaskRouter):
        self.task_store = task_store
        self.router = router

    def add_task_to_queue(self, task) -> None:
        """
        Route a single task and move it to QUEUED status.
        Convenience method for explicit single-task dispatch.
        """
        worker_name = self.router.route_task(task)
        task.assign_worker(worker_name)
        task.update_status(TaskStatus.QUEUED)
        self.task_store.update_task(task)

    def dispatch_created_tasks(self) -> int:
        created_tasks = self.task_store.list_tasks_by_status(TaskStatus.CREATED)

        dispatch_count = 0

        for task in created_tasks:
            self.add_task_to_queue(task)
            dispatch_count += 1

        return dispatch_count




