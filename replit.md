# Prymal OS

AI "OS" - An orchestration framework for using agents to scale humans in an organization. Turn human ideas into AI work.

## Project Structure

```
app.py                         - FastAPI application entry point
api/
  routers/
    health.py                  - GET /health endpoint
    tasks.py                   - Task CRUD endpoints
    dispatch.py                - Task dispatch endpoint
  dependencies.py              - Shared FastAPI dependencies
kernel/
  config.py                    - App configuration (DB path, etc.)
  scheduler/
    dispatcher.py              - TaskDispatcher: runs tasks via router
    router.py                  - TaskRouter: routes tasks to workers
  storage/
    base.py                    - Abstract storage interface
    sqllite.py                 - SQLite storage implementation
  tasks/
    task.py                    - Task entity
    task_store.py              - TaskStore: CRUD over storage
  utils/
    sql_loader.py              - Load SQL files from kernel/sql/
  sql/tasks/                   - SQL query files
    create_table.sql
    get_task.sql
    insert_task.sql
    list_tasks.sql
    list_task_by_status.sql
    update_task.sql
  workers/
    catalog.py                 - Worker catalog
    registry.py                - Worker registry
    spec.py                    - Worker spec definition
interfaces/
  inputs/
    sample_task.py             - Sample task input schema
  outputs/                     - Output schemas
entities.py                    - Shared entity definitions
tests/
  conftest.py
  smoke/
    test_api_smoke.py          - API smoke tests
    test_kernel_smoke.py       - Kernel smoke tests
scripts/
  post-merge.sh                - Post-merge setup (runs uv sync)
pyproject.toml                 - Python project and dependency config
uv.lock                        - Locked dependency versions
```

## Stack

- **Language**: Python 3.12 (via uv)
- **Web Framework**: FastAPI
- **ASGI Server**: Uvicorn (dev) / Gunicorn (prod)
- **Database**: SQLite (via task_store.db)
- **Package Manager**: uv

## Running the App

Development (main webview on port 5000):
```bash
uv run uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

API dev server (port 8000):
```bash
uv run uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Tests:
```bash
uv run pytest -v --disable-warnings
```

## API Endpoints

- `GET /health` - Health check
- `GET /docs` - Interactive API docs (Swagger UI)
- `GET /tasks` - List all tasks
- `POST /tasks` - Create a task
- `POST /tasks/sample` - Create a sample task
- `GET /tasks/{task_id}` - Get a task by ID
- `POST /dispatch` - Dispatch a task for processing

## Deployment

Configured for Replit autoscale using Gunicorn:
```
gunicorn --bind=0.0.0.0:5000 --reuse-port app:app
```
