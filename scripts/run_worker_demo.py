from __future__ import annotations

import sys
from pathlib import Path

workspace_root = Path(__file__).parent.parent
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

from interfaces.inputs.sample_task import build_sample_task
from kernel.config import TASK_STORE_DB
from kernel.runtime.task_executor import TaskExecutor
from kernel.scheduler.dispatcher import TaskDispatcher
from kernel.scheduler.router import TaskRouter
from kernel.storage.sqllite import SQLiteStorage
from kernel.tasks.task_store import TaskStore


def main() -> None:
    storage = SQLiteStorage(db_path=TASK_STORE_DB)
    task_store = TaskStore(storage)
    task_store.initialize()

    task = build_sample_task()
    task_store.create_task(task)

    persisted_after_creation = task_store.get_task(task.task_id)
    print("=== After creation ===")
    print(f"task_id: {persisted_after_creation.task_id}")
    print(f"status: {persisted_after_creation.status.value}")
    print(f"owner_worker: {persisted_after_creation.owner_worker}")
    print(f"artifacts: {persisted_after_creation.artifacts}")

    dispatcher = TaskDispatcher(task_store=task_store, router=TaskRouter())
    dispatcher.add_task_to_queue(task)

    persisted_after_dispatch = task_store.get_task(task.task_id)
    print("\n=== After dispatch ===")
    print(f"task_id: {persisted_after_dispatch.task_id}")
    print(f"status: {persisted_after_dispatch.status.value}")
    print(f"owner_worker: {persisted_after_dispatch.owner_worker}")
    print(f"artifacts: {persisted_after_dispatch.artifacts}")

    executor = TaskExecutor(task_store=task_store)
    executor.execute_task_by_id(task.task_id)

    persisted_after_execution = task_store.get_task(task.task_id)
    print("\n=== After execution ===")
    print(f"task_id: {persisted_after_execution.task_id}")
    print(f"status: {persisted_after_execution.status.value}")
    print(f"owner_worker: {persisted_after_execution.owner_worker}")
    print(f"artifacts: {persisted_after_execution.artifacts}")

    storage.close()


if __name__ == "__main__":
    main()