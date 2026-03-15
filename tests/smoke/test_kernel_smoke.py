"""Smoke tests for core OpsIQ kernel functionality."""

from __future__ import annotations

from pathlib import Path

import pytest

from interfaces.inputs.sample_task import build_sample_task
from kernel.config import TASK_STORE_DB
from kernel.scheduler.dispatcher import TaskDispatcher
from kernel.scheduler.router import TaskRouter
from kernel.storage.sqllite import SQLiteStorage
from kernel.tasks.task import TaskDomain, TaskStatus
from kernel.tasks.task_store import TaskStore
from kernel.workers.registry import build_worker_registry


@pytest.fixture
def task_store(tmp_path: Path) -> TaskStore:
    """Create an isolated SQLite-backed TaskStore for each test."""
    db_path = tmp_path / TASK_STORE_DB
    storage = SQLiteStorage(db_path=str(db_path))
    store = TaskStore(storage)
    store.initialize()

    try:
        yield store
    finally:
        storage.close()


@pytest.fixture
def sample_task():
    """Build a reusable sample task through the input adapter layer."""
    return build_sample_task()


def test_task_creation_and_persistence(task_store: TaskStore, sample_task) -> None:
    """A task can be created via input adapter and persisted to the task store."""
    task_store.create_task(sample_task)

    persisted = task_store.get_task(sample_task.task_id)

    assert persisted is not None
    assert persisted.task_id == sample_task.task_id
    assert persisted.objective.action == sample_task.objective.action
    assert persisted.objective.subject == sample_task.objective.subject
    assert persisted.objective.outcome == sample_task.objective.outcome
    assert persisted.domain == sample_task.domain
    assert persisted.created_by == sample_task.created_by
    assert persisted.expected_outputs == sample_task.expected_outputs
    assert persisted.status == TaskStatus.CREATED
    assert persisted.owner_worker is None


def test_task_routing_returns_expected_worker(sample_task) -> None:
    """Registry-backed routing returns the expected worker for the sample task."""
    router = TaskRouter()
    registry = build_worker_registry()

    worker_name = router.route_task(sample_task)
    expected_worker = registry.resolve_for_task(sample_task).worker_id

    assert worker_name == expected_worker


@pytest.mark.parametrize(
    ("domain", "expected_worker"),
    [
        (TaskDomain.OPERATIONS, "coo_worker"),
        (TaskDomain.MARKETING, "cmo_worker"),
        (TaskDomain.RESEARCH, "research_worker"),
        (TaskDomain.GENERAL, "general_worker"),
    ],
)
def test_router_domain_mapping(domain: TaskDomain, expected_worker: str) -> None:
    """The router resolves each domain to the expected worker via the registry."""
    task = build_sample_task()
    task.domain = domain

    router = TaskRouter()

    assert router.route_task(task) == expected_worker


def test_dispatch_created_tasks_queues_and_assigns_worker(
    task_store: TaskStore,
    sample_task,
) -> None:
    """Dispatcher finds CREATED tasks, assigns a worker, and moves them to QUEUED."""
    task_store.create_task(sample_task)

    dispatcher = TaskDispatcher(task_store=task_store, router=TaskRouter())

    dispatch_count = dispatcher.dispatch_created_tasks()
    updated_task = task_store.get_task(sample_task.task_id)
    queued_tasks = task_store.list_tasks_by_status(TaskStatus.QUEUED)

    assert dispatch_count == 1
    assert updated_task is not None
    assert updated_task.status == TaskStatus.QUEUED
    assert updated_task.owner_worker == "coo_worker"
    assert len(queued_tasks) == 1
    assert queued_tasks[0].task_id == sample_task.task_id


def test_dispatch_only_targets_created_tasks(task_store: TaskStore) -> None:
    """Dispatcher should not re-dispatch tasks that are already queued."""
    task = build_sample_task()
    task.update_status(TaskStatus.QUEUED)
    task.assign_worker("coo_worker")
    task_store.create_task(task)

    dispatcher = TaskDispatcher(task_store=task_store, router=TaskRouter())

    dispatch_count = dispatcher.dispatch_created_tasks()
    queued_tasks = task_store.list_tasks_by_status(TaskStatus.QUEUED)

    assert dispatch_count == 0
    assert len(queued_tasks) == 1
    assert queued_tasks[0].task_id == task.task_id
    assert queued_tasks[0].owner_worker == "coo_worker"


def test_router_uses_registry_resolution(sample_task) -> None:
    """Router output matches the registry's resolution for the same task."""
    router = TaskRouter()
    registry = build_worker_registry()

    routed_worker = router.route_task(sample_task)
    resolved_worker = registry.resolve_for_task(sample_task).worker_id

    assert routed_worker == resolved_worker