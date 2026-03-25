from __future__ import annotations

import json
from datetime import datetime

from kernel.storage.sqllite import SQLiteStorage
from kernel.tasks.task import Objective, Task, TaskDomain, TaskPriority, TaskStatus
from kernel.utils.sql_loader import load_sql

CREATE_TABLE = load_sql("tasks/create_table.sql")
INSERT_TASK = load_sql("tasks/insert_task.sql")
GET_TASK = load_sql("tasks/get_task.sql")
UPDATE_TASK = load_sql("tasks/update_task.sql")
LIST_TASKS = load_sql("tasks/list_tasks.sql")
LIST_TASK_BY_STATUS = load_sql("tasks/list_task_by_status.sql")
LIST_TASKS_BY_WORK_REQUEST = load_sql("tasks/list_tasks_by_work_request.sql")


class TaskStore:
    def __init__(self, storage):
        self.storage = storage

    def initialize(self) -> None:
        self.storage.execute(CREATE_TABLE)

    def create_task(self, task: Task) -> None:
        params = (
            task.task_id,
            task.objective.action,
            task.objective.subject,
            task.objective.outcome,
            task.domain.value,
            task.created_by,
            task.owner_worker,
            task.priority.value,
            task.status.value,
            json.dumps(task.expected_outputs),
            task.expected_token_count,
            task.due_date.isoformat() if task.due_date else None,
            task.dependency_str,
            task.parent_task_id,
            json.dumps(task.dependencies),
            task.created_at.isoformat(),
            task.updated_at.isoformat(),
            json.dumps(task.artifacts),
            task.thread_id,
            task.work_request_id,
            task.intent_index,
        )
        self.storage.execute(INSERT_TASK, params)

    def get_task(self, task_id: str) -> Task | None:
        row = self.storage.fetch_one(GET_TASK, (task_id,))
        if not row:
            return None
        return self._row_to_task(row)

    def update_task(self, task: Task) -> None:
        params = (
            task.objective.action,
            task.objective.subject,
            task.objective.outcome,
            task.domain.value,
            task.created_by,
            task.owner_worker,
            task.priority.value,
            task.status.value,
            json.dumps(task.expected_outputs),
            task.expected_token_count,
            task.due_date.isoformat() if task.due_date else None,
            task.dependency_str,
            task.parent_task_id,
            json.dumps(task.dependencies),
            task.created_at.isoformat(),
            task.updated_at.isoformat(),
            json.dumps(task.artifacts),
            task.thread_id,
            task.work_request_id,
            task.intent_index,
            task.task_id,
        )
        self.storage.execute(UPDATE_TASK, params)

    def list_tasks(self) -> list[Task]:
        rows = self.storage.fetch_all(LIST_TASKS)
        return [self._row_to_task(row) for row in rows]

    def list_tasks_by_work_request(self, work_request_id: str) -> list[Task]:
        rows = self.storage.fetch_all(LIST_TASKS_BY_WORK_REQUEST, (work_request_id,))
        return [self._row_to_task(row) for row in rows]

    def list_tasks_by_status(self, status: TaskStatus) -> list[Task]:
        rows = self.storage.fetch_all(LIST_TASK_BY_STATUS, (status.value,))
        return [self._row_to_task(row) for row in rows]

    def _row_to_task(self, row: dict) -> Task:
        return Task(
            task_id=row["task_id"],
            objective=Objective(
                action=row["action"],
                subject=row["subject"],
                outcome=row["outcome"],
            ),
            domain=TaskDomain(row["domain"]),
            status=TaskStatus(row["status"]),
            priority=TaskPriority(row["priority"]),
            owner_worker=row["owner_worker"],
            created_by=row["created_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            expected_outputs=json.loads(row["expected_outputs"]),
            expected_token_count=row["expected_token_count"],
            due_date=datetime.fromisoformat(row["due_date"]) if row["due_date"] else None,
            dependency_str=row["dependency_str"],
            dependencies=json.loads(row["dependencies"]),
            parent_task_id=row["parent_task_id"],
            artifacts=json.loads(row["artifacts"]),
            thread_id=row["thread_id"],
            work_request_id=row.get("work_request_id"),
            intent_index=row.get("intent_index"),
        )