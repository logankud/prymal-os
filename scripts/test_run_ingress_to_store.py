import asyncio
import sys
from pathlib import Path
from pprint import pprint

# Add project root to Python path
workspace_root = Path(__file__).parent.parent
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

from kernel.config import TASK_STORE_DB
from kernel.scheduler.dispatcher import TaskDispatcher
from kernel.scheduler.router import TaskRouter
from kernel.storage.sqllite import SQLiteStorage
from kernel.tasks.materialize import task_from_ingress_result
from kernel.tasks.task_store import TaskStore
from nodes.ingress.node import IngressNode


async def main() -> None:
    storage = SQLiteStorage(db_path=TASK_STORE_DB)
    task_store = TaskStore(storage)
    task_store.initialize()

    router = TaskRouter()
    dispatcher = TaskDispatcher(task_store=task_store, router=router)
    ingress_node = IngressNode()

    state = {
        "ingress_event": {
            "event_type": "user_text",
            "text": "Analyze new product launch messaging to recommend next actions",
            "source": "ui",
        }
    }

    result = await ingress_node.run(state)

    print("\n[Ingress Result]")
    pprint(result)

    if not result.ok:
        print("\nIngress failed; no task will be created.")
        storage.close()
        return

    task = task_from_ingress_result(result)

    print("\n[Materialized Task]")
    pprint(task)

    task_store.create_task(task)
    print(f"\nCreated task: {task.task_id}")

    dispatched = dispatcher.dispatch_created_tasks()
    print(f"Dispatched tasks: {dispatched}")

    storage.close()


if __name__ == "__main__":
    asyncio.run(main())