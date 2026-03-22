from kernel.tasks.task import Task, Objective, TaskDomain, TaskPriority


class TaskFactory:
    @staticmethod
    def from_objective(
        objective: Objective,
        *,
        domain: TaskDomain = TaskDomain.GENERAL,
        created_by: str = "system",
        priority: TaskPriority = TaskPriority.MEDIUM,
        thread_id: str | None = None,
    ) -> Task:
        return Task(
            objective=objective,
            domain=domain,
            created_by=created_by,
            priority=priority,
            thread_id=thread_id,
        )