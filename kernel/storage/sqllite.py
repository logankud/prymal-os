from __future__ import annotations

import sqlite3
from typing import Any, Iterable, Optional
import threading
from kernel.storage.base import BaseStorage


class SQLiteStorage(BaseStorage):
    """SQLite-backed storage implementation."""

    def __init__(self, db_path: str = "task_store.db") -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.lock = threading.Lock()
        self.conn.row_factory = sqlite3.Row

    def execute(self, query: str, params: tuple = ()) -> None:
        with self.lock:
            with self.conn:
                self.conn.execute(query, params)

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[dict[str, Any]]:
        with self.lock:
            cur = self.conn.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None

    def fetch_all(self, query: str, params: tuple = ()) -> list[dict[str, Any]]:
        with self.lock:
            cur = self.conn.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    
    def executemany(self, query: str, param_sets: Iterable[tuple]) -> None:
        with self.lock:
            with self.conn:
                self.conn.executemany(query, param_sets)

    def close(self) -> None:
        with self.lock:
            self.conn.close()
