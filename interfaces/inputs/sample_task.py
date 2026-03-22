
"""
Sample input adapter for OpsIQ.

This file simulates an external system producing a Task that enters the kernel.
In the future this directory will contain real input adapters such as:
- voice_input.py
- api_input.py
- slack_input.py
- scheduler_input.py
"""

from typing import Optional
from kernel.tasks.task import Objective, Task, TaskDomain


def build_sample_task() -> Task:
    return Task(
        objective=Objective(
            action="investigate",
            subject="Shopify revenue drop",
            outcome="identify likely causes",
        ),
        domain=TaskDomain.OPERATIONS,
        created_by="sample_input",
        expected_outputs=[
            "root cause summary",
            "recommended next actions",
        ],
        expected_token_count=2500,
        due_date=None,
        dependency_str="Depends on access to Shopify revenue and campaign data.",
    )
