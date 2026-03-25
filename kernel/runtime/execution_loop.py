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
from typing import Optional

from kernel.runtime.task_executor import TaskExecutor
from kernel.tasks.task import Task, TaskStatus
from kernel.tasks.task_store import TaskStore
from kernel.work_request.work_request import WorkRequest, WorkRequestStatus
from kernel.work_request.work_request_store import WorkRequestStore

logger = logging.getLogger(__name__)

_TERMINAL_STATUSES = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}


def _check_work_request_completion(
    completed_task: Task,
    task_store: TaskStore,
    work_request_store: WorkRequestStore,
) -> None:
    """
    After a task completes, check if all tasks in its WorkRequest are terminal.
    If so, mark the WorkRequest READY_FOR_SYNTHESIS.
    """
    if not completed_task.work_request_id:
        return

    work_request = work_request_store.get(completed_task.work_request_id)
    if not work_request:
        return

    # Add artifact references from the completed task
    for artifact in completed_task.artifacts:
        if artifact not in work_request.artifact_ids:
            work_request.add_artifact(artifact)

    # Check if all tasks in this work request have reached a terminal state
    all_tasks = task_store.list_tasks_by_work_request(work_request.work_request_id)
    if all_tasks and all(t.status in _TERMINAL_STATUSES for t in all_tasks):
        work_request.status = WorkRequestStatus.READY_FOR_SYNTHESIS
        work_request_store.update(work_request)
        logger.info(
            f"WorkRequest {work_request.work_request_id} is READY_FOR_SYNTHESIS "
            f"({len(all_tasks)} task(s) complete)."
        )
    else:
        work_request_store.update(work_request)


async def _execute_task(
    task: Task,
    executor: TaskExecutor,
    task_store: TaskStore,
    work_request_store: Optional[WorkRequestStore] = None,
) -> None:
    """Execute a single task in a thread pool, logging any failures."""
    try:
        completed_task = await asyncio.to_thread(executor.execute_task_by_id, task.task_id)
        logger.info(f"Task {task.task_id} completed.")
        if completed_task is not None and work_request_store is not None:
            try:
                _check_work_request_completion(completed_task, task_store, work_request_store)
            except Exception as exc:
                logger.error(f"Work request completion check failed for task {task.task_id}: {exc}")
    except Exception as exc:
        logger.error(f"Task {task.task_id} failed: {exc}")
        if work_request_store is not None:
            try:
                failed_task = task_store.get_task(task.task_id)
                if failed_task is not None:
                    _check_work_request_completion(failed_task, task_store, work_request_store)
            except Exception as inner_exc:
                logger.error(f"Work request completion check failed after task failure {task.task_id}: {inner_exc}")


async def _run_synthesis(
    work_request: WorkRequest,
    task_store: TaskStore,
    work_request_store: WorkRequestStore,
    synthesis_node,
    delivery_callback,
) -> None:
    """Run synthesis for a single READY_FOR_SYNTHESIS WorkRequest in a thread pool."""
    try:
        synthesis_result = await asyncio.to_thread(
            synthesis_node.synthesize,
            work_request,
            task_store,
            work_request_store,
        )
        if synthesis_result is not None and delivery_callback is not None:
            try:
                delivery_callback(work_request, synthesis_result)
            except Exception as exc:
                logger.error(
                    "Delivery callback failed for WorkRequest %s: %s",
                    work_request.work_request_id,
                    exc,
                )
    except Exception as exc:
        logger.error(
            "Synthesis failed for WorkRequest %s: %s",
            work_request.work_request_id,
            exc,
        )


async def run_execution_loop(
    task_store: TaskStore,
    executor: TaskExecutor,
    interval: float = 2.0,
    work_request_store: Optional[WorkRequestStore] = None,
    synthesis_node=None,
    delivery_callback=None,
) -> None:
    """
    Poll for QUEUED tasks and execute them concurrently.

    After each task completes, checks if all tasks in the same WorkRequest
    are terminal and advances the WorkRequest to READY_FOR_SYNTHESIS.

    If a synthesis_node is provided, polls for READY_FOR_SYNTHESIS WorkRequests
    each iteration and runs synthesis. When complete, fires delivery_callback.

    Args:
        task_store:          used to query for QUEUED tasks each iteration
        executor:            handles status transitions and worker dispatch
        interval:            seconds to sleep between polls
        work_request_store:  if provided, tracks work request lifecycle
        synthesis_node:      SynthesisNode instance; if None, synthesis is skipped
        delivery_callback:   called with (WorkRequest, SynthesisResult) after synthesis
    """
    logger.info("Execution loop started.")

    while True:
        try:
            # ── Task execution ────────────────────────────────────────────
            queued = task_store.list_tasks_by_status(TaskStatus.QUEUED)
            if queued:
                await asyncio.gather(
                    *[
                        _execute_task(task, executor, task_store, work_request_store)
                        for task in queued
                    ],
                    return_exceptions=True,
                )

            # ── Synthesis ─────────────────────────────────────────────────
            if synthesis_node is not None and work_request_store is not None:
                ready = work_request_store.list_by_status(WorkRequestStatus.READY_FOR_SYNTHESIS)
                if ready:
                    await asyncio.gather(
                        *[
                            _run_synthesis(
                                wr, task_store, work_request_store,
                                synthesis_node, delivery_callback,
                            )
                            for wr in ready
                        ],
                        return_exceptions=True,
                    )

        except Exception as exc:
            logger.error(f"Execution loop error: {exc}")

        await asyncio.sleep(interval)
