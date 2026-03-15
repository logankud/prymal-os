from __future__ import annotations

from pydantic import BaseModel, Field

from kernel.tasks.task import Task, TaskDomain


class CreateTaskRequest(BaseModel):
    action: str = Field(..., description="Verb describing the task objective.")
    subject: str = Field(..., description="The subject of the task.")
    outcome: str = Field(..., description="Desired outcome of the task.")
    domain: TaskDomain = Field(..., description="Task domain used for routing.")
    created_by: str = Field(..., description="Identifier for the creator of the task.")
    expected_outputs: list[str] = Field(
        default_factory=list,
        description="Expected outputs or artifacts from the task.",
    )


class TaskResponse(BaseModel):
    task_id: str
    action: str
    subject: str
    outcome: str
    domain: str
    status: str
    created_by: str
    owner_worker: str | None
    expected_outputs: list[str]

    @classmethod
    def from_task(cls, task: Task) -> "TaskResponse":
        return cls(
            task_id=task.task_id,
            action=task.objective.action,
            subject=task.objective.subject,
            outcome=task.objective.outcome,
            domain=task.domain.value,
            status=task.status.value,
            created_by=task.created_by,
            owner_worker=task.owner_worker,
            expected_outputs=task.expected_outputs,
        )


class DispatchResponse(BaseModel):
    dispatched_count: int