from __future__ import annotations

import json

import dspy

from artifacts.report import ReportArtifact, ReportPayload, ReportSection
from kernel.model import ModelClass, get_lm
from kernel.tasks.task import Task
from kernel.workers.base_worker import BaseWorker
from signatures.execution.execute_task_signature import ExecuteTaskSignature


class GeneralWorker(BaseWorker):
    def __init__(self) -> None:
        super().__init__(worker_id="general_worker")
        self._lm = get_lm(ModelClass.FAST)
        self._predict = dspy.ChainOfThought(ExecuteTaskSignature)

    def run(self, task: Task) -> Task:
        with dspy.context(lm=self._lm):
            result = self._predict(
                action=task.objective.action,
                subject=task.objective.subject,
                outcome=task.objective.outcome or "not specified",
                domain=task.domain.value,
            )

        artifact = ReportArtifact(
            task_id=task.task_id,
            worker_id=self.worker_id,
            thread_id=task.thread_id,
            payload=ReportPayload(
                title=f"{task.objective.action.title()}: {task.objective.subject}",
                executive_summary=result.executive_summary,
                sections=[
                    ReportSection(
                        title="Deliverable",
                        body=result.deliverable,
                    )
                ],
            ),
        )

        task.add_artifact(json.dumps(artifact.to_dict()))
        return task
