"""
ExecutionLoop — async background loop that executes queued tasks concurrently.

Started as an asyncio background task at app startup. Polls the TaskStore
for QUEUED tasks and executes them concurrently via asyncio.gather.

WorkerRunner marks tasks as RUNNING immediately on pickup, so concurrent
polling is safe — subsequent iterations won't re-claim in-progress tasks.

When workers become async, replace asyncio.to_thread with direct awaits.
"""

from __future__ import annotations

import asyncio
import logging

from kernel.runtime.task_executor import TaskExecutor
from kernel.tasks.task import Task, TaskStatus
from kernel.tasks.task_store import TaskStore

logger = logging.getLogger(__name__)


async def _execute_task(task: Task, executor: TaskExecutor) -> None:
    """Execute a single task in a thread pool, logging any failures."""
    try:
        await asyncio.to_thread(executor.execute_task_by_id, task.task_id)
        logger.info(f"Task {task.task_id} completed.")
    except Exception as exc:
        logger.error(f"Task {task.task_id} failed: {exc}")


async def run_execution_loop(
    task_store: TaskStore,
    executor: TaskExecutor,
    interval: float = 2.0,
) -> None:
    """
    Poll for QUEUED tasks and execute them concurrently.

    Args:
        task_store: used to query for QUEUED tasks each iteration
        executor:   handles status transitions and worker dispatch
        interval:   seconds to sleep between polls
    """
    logger.info("Execution loop started.")

    while True:
        try:
            queued = task_store.list_tasks_by_status(TaskStatus.QUEUED)

            if queued:
                await asyncio.gather(
                    *[_execute_task(task, executor) for task in queued],
                    return_exceptions=True,
                )

        except Exception as exc:
            logger.error(f"Execution loop error: {exc}")

        await asyncio.sleep(interval)
