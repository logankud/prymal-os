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
from nodes.ingress.node import IngressNode
from signatures.ingress.types import ParsedIntent


class IntakeService:
    def __init__(
        self,
        task_store: TaskStore,
        dispatcher: TaskDispatcher,
    ) -> None:
        self.task_store = task_store
        self.dispatcher = dispatcher
        self._ingress = IngressNode()

    async def process(
        self,
        text: str,
        source: str = "user",
        event_type: str = "user_text",
    ) -> list[Task]:
        """
        Run intake for a single user input.

        1. IngressNode extracts list[ParsedIntent] from raw text
        2. Each intent is created as a Task and persisted
        3. Each task is dispatched (CREATED → QUEUED)

        Returns tasks in QUEUED state. Execution is handled by ExecutionLoop.
        """
        state = {
            "ingress_event": {
                "event_type": event_type,
                "text": text,
                "source": source,
            }
        }

        result = await self._ingress.run(state)

        if not result.ok:
            raise RuntimeError(f"Ingress node failed: {result.errors}")

        intents = [
            ParsedIntent(**i) for i in result.state_patch.get("intents", [])
        ]

        tasks: list[Task] = []
        for intent in intents:
            task = Task(
                objective=Objective(
                    action=intent.action,
                    subject=intent.subject,
                    outcome=intent.outcome,
                ),
                domain=TaskDomain(intent.domain),
                created_by=source,
            )
            self.task_store.create_task(task)
            self.dispatcher.add_task_to_queue(task)
            tasks.append(task)

        return tasks
