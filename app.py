from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

load_dotenv()

from api.routers.dispatch import router as dispatch_router
from api.routers.health import router as health_router
from api.routers.intake import router as intake_router
from api.routers.tasks import router as tasks_router
from api.routers.execution import router as execution_router
from integrations.slack.router import router as slack_router
from kernel.config import TASK_STORE_DB
from kernel.intake.intake_service import IntakeService
from kernel.model import configure_lm
from kernel.runtime.execution_loop import run_execution_loop
from kernel.runtime.task_executor import TaskExecutor
from kernel.scheduler.dispatcher import TaskDispatcher
from kernel.scheduler.router import TaskRouter
from kernel.storage.sqllite import SQLiteStorage
from kernel.tasks.task_store import TaskStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_lm()

    storage = SQLiteStorage(db_path=TASK_STORE_DB)
    task_store = TaskStore(storage)
    task_store.initialize()

    router = TaskRouter()
    dispatcher = TaskDispatcher(task_store=task_store, router=router)
    executor = TaskExecutor(task_store=task_store)
    intake_service = IntakeService(task_store=task_store, dispatcher=dispatcher)

    app.state.storage = storage
    app.state.task_store = task_store
    app.state.dispatcher = dispatcher
    app.state.intake_service = intake_service

    execution_task = asyncio.create_task(
        run_execution_loop(task_store=task_store, executor=executor)
    )

    try:
        yield
    finally:
        execution_task.cancel()
        storage.close()


app = FastAPI(
    title="OpsIQ Dev API",
    description="Minimal developer harness for inspecting the OpsIQ kernel.",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(health_router)
app.include_router(tasks_router)
app.include_router(dispatch_router)
app.include_router(execution_router)
app.include_router(intake_router)
app.include_router(slack_router)


@app.get("/ui", response_class=HTMLResponse)
def ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
