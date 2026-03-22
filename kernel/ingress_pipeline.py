from __future__ import annotations

import logging
from typing import List, Optional

from kernel.tasks.factory import TaskFactory
from kernel.tasks.task import Objective, Task, TaskDomain
from kernel.tasks.task_store import TaskStore
from nodes.ingress.node import IngressNode
from nodes.ingress.schema import IngressEvent

logger = logging.getLogger(__name__)

_ingress_node = IngressNode()


async def run_ingress_pipeline(
    event: IngressEvent,
    task_store: TaskStore,
    created_by: Optional[str] = None,
) -> List[Task]:
    """
    Run the full ingress pipeline for a canonical IngressEvent.

    This is the single entry point for converting any external signal
    into Tasks in the kernel. All integrations (Slack, UI, voice, etc.)
    funnel through here.

    Steps:
    1. Run IngressNode (two-pass DSPy: extract → refine) to get structured intents
    2. Create one Task per extracted intent
    3. Persist all tasks to the store

    Returns the list of created Tasks (1→N per input signal).
    Raises on ingress failure or task creation failure.
    """
    state = {
        "ingress_event": {
            "event_type": event.event_type.value,
            "text": event.text,
            "source": event.source,
            "metadata": event.metadata,
        }
    }

    result = await _ingress_node.run(state)

    if not result.ok:
        raise RuntimeError(f"IngressNode failed: {result.error}")

    intents = result.state_patch.get("intents", [])

    if not intents:
        raise RuntimeError("IngressNode returned no intents — nothing to create.")

    tasks = []
    for intent in intents:
        task = TaskFactory.from_objective(
            objective=Objective(
                action=intent["action"],
                subject=intent["subject"],
                outcome=intent.get("outcome"),
            ),
            domain=TaskDomain(intent.get("domain", "general")),
            created_by=created_by or "ingress",
        )
        task_store.create_task(task)
        tasks.append(task)
        logger.info("Task %s created via ingress pipeline (source=%s)", task.task_id, event.source)

    return tasks
