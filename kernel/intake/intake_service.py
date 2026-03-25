"""
IntakeService — bridges the IngressNode to the task pipeline.

Accepts raw text, runs the two-pass DSPy ingress node to extract structured
intents, then creates and dispatches a Task for each intent. Execution is
handled separately by the background ExecutionLoop.
"""

from __future__ import annotations

from kernel.scheduler.dispatcher import TaskDispatcher
from kernel.tasks.task import Objective, Task, TaskDomain
from kernel.tasks.task_store import TaskStore
from kernel.work_request.work_request import WorkRequest
from kernel.work_request.work_request_store import WorkRequestStore
from nodes.ingress.node import IngressNode
from signatures.ingress.types import ParsedIntent


class IntakeService:
    def __init__(
        self,
        task_store: TaskStore,
        dispatcher: TaskDispatcher,
        work_request_store: WorkRequestStore,
    ) -> None:
        self.task_store = task_store
        self.dispatcher = dispatcher
        self.work_request_store = work_request_store
        self._ingress = IngressNode()

    async def process(
        self,
        text: str,
        source: str = "user",
        event_type: str = "user_text",
        thread_id: str | None = None,
        user_id: str | None = None,
    ) -> list[Task]:
        """
        Run intake for a single user input.

        1. Create a WorkRequest to track the full lifecycle
        2. IngressNode extracts list[ParsedIntent] from raw text
        3. Each intent is created as a Task and persisted (with work_request_id + intent_index)
        4. Each task is dispatched (CREATED → QUEUED)

        Returns tasks in QUEUED state. Execution is handled by ExecutionLoop.
        """
        work_request = WorkRequest(
            source=source,
            raw_text=text,
            thread_id=thread_id,
            user_id=user_id,
        )
        self.work_request_store.create(work_request)

        state = {
            "ingress_event": {
                "event_type": event_type,
                "text": text,
                "source": source,
            }
        }

        result = await self._ingress.run(state)

        if not result.ok:
            work_request.mark_failed()
            self.work_request_store.update(work_request)
            raise RuntimeError(f"Ingress node failed: {result.errors}")

        intents = [
            ParsedIntent(**i) for i in result.state_patch.get("intents", [])
        ]

        work_request.intents = [i.model_dump() for i in intents]

        tasks: list[Task] = []
        for idx, intent in enumerate(intents):
            task = Task(
                objective=Objective(
                    action=intent.action,
                    subject=intent.subject,
                    outcome=intent.outcome,
                ),
                domain=TaskDomain(intent.domain),
                created_by=source,
                thread_id=thread_id,
                work_request_id=work_request.work_request_id,
                intent_index=idx,
            )
            self.task_store.create_task(task)
            self.dispatcher.add_task_to_queue(task)
            work_request.add_task(task.task_id)
            tasks.append(task)

        self.work_request_store.update(work_request)
        return tasks
