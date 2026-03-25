from __future__ import annotations

import json
from datetime import datetime

from kernel.storage.sqllite import SQLiteStorage
from kernel.utils.sql_loader import load_sql
from kernel.work_request.work_request import WorkRequest, WorkRequestStatus

CREATE_TABLE           = load_sql("work_requests/create_table.sql")
INSERT_WORK_REQUEST    = load_sql("work_requests/insert_work_request.sql")
GET_WORK_REQUEST       = load_sql("work_requests/get_work_request.sql")
UPDATE_WORK_REQUEST    = load_sql("work_requests/update_work_request.sql")
GET_BY_THREAD_ID       = load_sql("work_requests/get_by_thread_id.sql")
LIST_BY_STATUS         = load_sql("work_requests/list_by_status.sql")
LIST_ALL               = load_sql("work_requests/list_all.sql")


class WorkRequestStore:
    def __init__(self, storage: SQLiteStorage) -> None:
        self.storage = storage

    def initialize(self) -> None:
        self.storage.execute(CREATE_TABLE)

    def create(self, wr: WorkRequest) -> None:
        self.storage.execute(INSERT_WORK_REQUEST, (
            wr.work_request_id,
            wr.status.value,
            wr.source,
            wr.raw_text,
            wr.thread_id,
            wr.user_id,
            json.dumps(wr.intents),
            json.dumps(wr.task_ids),
            json.dumps(wr.artifact_ids),
            json.dumps(wr.synthesis_result) if wr.synthesis_result else None,
            json.dumps(wr.prior_context_ids),
            wr.created_at.isoformat(),
            wr.updated_at.isoformat(),
        ))

    def get(self, work_request_id: str) -> WorkRequest | None:
        row = self.storage.fetch_one(GET_WORK_REQUEST, (work_request_id,))
        return self._row_to_wr(row) if row else None

    def update(self, wr: WorkRequest) -> None:
        self.storage.execute(UPDATE_WORK_REQUEST, (
            wr.status.value,
            json.dumps(wr.task_ids),
            json.dumps(wr.artifact_ids),
            json.dumps(wr.synthesis_result) if wr.synthesis_result else None,
            wr.updated_at.isoformat(),
            wr.work_request_id,
        ))

    def get_by_thread_id(self, thread_id: str) -> list[WorkRequest]:
        rows = self.storage.fetch_all(GET_BY_THREAD_ID, (thread_id,))
        return [self._row_to_wr(r) for r in rows]

    def list_by_status(self, status: WorkRequestStatus) -> list[WorkRequest]:
        rows = self.storage.fetch_all(LIST_BY_STATUS, (status.value,))
        return [self._row_to_wr(r) for r in rows]

    def list_all(self) -> list[WorkRequest]:
        rows = self.storage.fetch_all(LIST_ALL)
        return [self._row_to_wr(r) for r in rows]

    def _row_to_wr(self, row: dict) -> WorkRequest:
        return WorkRequest(
            work_request_id=row["work_request_id"],
            status=WorkRequestStatus(row["status"]),
            source=row["source"],
            raw_text=row["raw_text"],
            thread_id=row["thread_id"],
            user_id=row["user_id"],
            intents=json.loads(row["intents"]),
            task_ids=json.loads(row["task_ids"]),
            artifact_ids=json.loads(row["artifact_ids"]),
            synthesis_result=json.loads(row["synthesis_result"]) if row["synthesis_result"] else None,
            prior_context_ids=json.loads(row["prior_context_ids"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
