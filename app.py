from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routers.dispatch import router as dispatch_router
from api.routers.health import router as health_router
from api.routers.tasks import router as tasks_router
from kernel.config import TASK_STORE_DB
from kernel.scheduler.dispatcher import TaskDispatcher
from kernel.scheduler.router import TaskRouter
from kernel.storage.sqllite import SQLiteStorage
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

app.include_router(health_router)
app.include_router(tasks_router)
app.include_router(dispatch_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
