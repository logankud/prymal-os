from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from entities import CreateTaskRequest, DispatchResponse, TaskResponse
from interfaces.inputs.sample_task import build_sample_task
from kernel.config import TASK_STORE_DB
from kernel.scheduler.dispatcher import TaskDispatcher
from kernel.scheduler.router import TaskRouter
from kernel.storage.sqllite import SQLiteStorage
from kernel.tasks.task import Objective, Task
from kernel.tasks.task_store import TaskStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    storage = SQLiteStorage(db_path=TASK_STORE_DB)
    task_store = TaskStore(storage)
    task_store.initialize()

    router = TaskRouter()
    dispatcher = TaskDispatcher(task_store=task_store, router=router)

    app.state.storage = storage
    app.state.task_store = task_store
    app.state.dispatcher = dispatcher

    try:
        yield
    finally:
        storage.close()


app = FastAPI(
    title="OpsIQ Dev API",
    description="Minimal developer harness for inspecting the OpsIQ kernel.",
    version="0.1.0",
    lifespan=lifespan,
)


def get_task_store() -> TaskStore:
    return app.state.task_store


def get_dispatcher() -> TaskDispatcher:
    return app.state.dispatcher


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/tasks", response_model=TaskResponse)
def create_task(payload: CreateTaskRequest) -> TaskResponse:
    task = Task(
        objective=Objective(
            action=payload.action,
            subject=payload.subject,
            outcome=payload.outcome,
        ),
        domain=payload.domain,
        created_by=payload.created_by,
        expected_outputs=payload.expected_outputs,
    )

    task_store = get_task_store()
    task_store.create_task(task)

    persisted = task_store.get_task(task.task_id)
    if persisted is None:
        raise HTTPException(status_code=500, detail="Task was not persisted.")

    return TaskResponse.from_task(persisted)


@app.post("/tasks/sample", response_model=TaskResponse)
def create_sample_task() -> TaskResponse:
    task = build_sample_task()

    task_store = get_task_store()
    task_store.create_task(task)

    persisted = task_store.get_task(task.task_id)
    if persisted is None:
        raise HTTPException(status_code=500, detail="Sample task was not persisted.")

    return TaskResponse.from_task(persisted)


@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks() -> list[TaskResponse]:
    task_store = get_task_store()
    tasks = task_store.list_tasks()

    return [TaskResponse.from_task(task) for task in tasks]


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str) -> TaskResponse:
    task_store = get_task_store()
    task = task_store.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    return TaskResponse.from_task(task)


@app.post("/dispatch", response_model=DispatchResponse)
def dispatch_created_tasks() -> DispatchResponse:
    dispatcher = get_dispatcher()
    dispatched_count = dispatcher.dispatch_created_tasks()

    return DispatchResponse(dispatched_count=dispatched_count)