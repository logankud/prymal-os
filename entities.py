from __future__ import annotations

from datetime import datetime

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
    expected_token_count: int | None = Field(
        default=None,
        description="Estimated token budget / proxy for expected LLM work.",
    )
    due_date: datetime | None = Field(
        default=None,
        description="Optional due date for the task.",
    )
    dependency_str: str | None = Field(
        default=None,
        description="Optional freeform description of dependencies at creation time.",
    )


class TaskResponse(BaseModel):
    task_id: str
    action: str
    subject: str
    outcome: str | None
    domain: str
    status: str
    created_by: str
    owner_worker: str | None
    expected_outputs: list[str]
    expected_token_count: int | None
    due_date: datetime | None
    dependency_str: str | None
    artifacts: list[str]

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
            expected_token_count=task.expected_token_count,
            due_date=task.due_date,
            dependency_str=task.dependency_str,
            artifacts=task.artifacts,
        )


class DispatchResponse(BaseModel):
    dispatched_count: int


class IntakeRequest(BaseModel):
    text: str = Field(..., description="Raw user input expressing one or more work intents.")
    source: str = Field(default="user", description="Identifier for who submitted the request.")
    event_type: str = Field(default="user_text", description="Ingress event type.")
    thread_id: str | None = Field(default=None, description="Originating thread ID for delivery routing (e.g. slack:C123:1234567890.123).")
    user_id: str | None = Field(default=None, description="User identifier from the source platform.")
    channel_id: str | None = Field(default=None, description="Channel identifier from the source platform.")


class IntakeResponse(BaseModel):
    tasks_created: int
    tasks: list[TaskResponse]