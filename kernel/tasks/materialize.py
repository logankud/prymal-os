from kernel.tasks.factory import TaskFactory
from kernel.tasks.task import Objective, TaskDomain, Task


def task_from_ingress_result(result) -> Task:
    objective_dict = result.state_patch["objective"]
    objective = Objective(**objective_dict)

    return TaskFactory.from_objective(
        objective=objective,
        domain=TaskDomain.GENERAL,
        created_by="ingress",
    )