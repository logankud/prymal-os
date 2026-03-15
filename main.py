from kernel.scheduler.dispatcher import TaskDispatcher
from kernel.scheduler.router import TaskRouter
from interfaces.inputs.sample_task import build_sample_task
from kernel.storage.sqllite import SQLiteStorage
from kernel.config import TASK_STORE_DB
from kernel.tasks.task_store import TaskStore



def main() -> None:
    storage = SQLiteStorage(db_path=TASK_STORE_DB)
    task_store = TaskStore(storage)
    task_store.initialize()

    router = TaskRouter()
    dispatcher = TaskDispatcher(task_store=task_store, router=router)

    incoming_task = build_sample_task()
    if incoming_task is not None:
        task_store.create_task(incoming_task)

    dispatched = dispatcher.dispatch_created_tasks()
    print(f"Dispatched tasks: {dispatched}")

    storage.close()


if __name__ == "__main__":
    main()