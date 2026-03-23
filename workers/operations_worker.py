from __future__ import annotations

import json

import dspy

from artifacts.analysis import AnalysisArtifact, AnalysisPayload, EvidenceItem, Hypothesis
from kernel.model import ModelClass, get_lm
from kernel.tasks.task import Task
from kernel.workers.base_worker import BaseWorker
from signatures.execution.execute_task_signature import ExecuteTaskSignature


class OperationsExecuteSignature(ExecuteTaskSignature):
    """
    Execute an operations task and produce a structured analysis or plan.

    You are a senior operations leader. Depending on the task type:

    - For analysis: examine the operational subject, surface root causes,
      identify bottlenecks, and recommend concrete process improvements.
    - For planning: produce a detailed ops plan with steps, owners, timelines,
      dependencies, and risk mitigations.
    - For review: assess current state, surface gaps, and prioritize fixes
      by impact and effort.

    Be analytical, systematic, and focused on operational outcomes.
    Quantify impact where possible. Surface assumptions explicitly.
    """


class OperationsWorker(BaseWorker):
    def __init__(self) -> None:
        super().__init__(worker_id="coo_worker")
        self._lm = get_lm(ModelClass.FAST)
        self._predict = dspy.ChainOfThought(OperationsExecuteSignature)

    def run(self, task: Task) -> Task:
        with dspy.context(lm=self._lm):
            result = self._predict(
                action=task.objective.action,
                subject=task.objective.subject,
                outcome=task.objective.outcome or "not specified",
                domain=task.domain.value,
            )

        artifact = AnalysisArtifact(
            task_id=task.task_id,
            worker_id=self.worker_id,
            thread_id=task.thread_id,
            payload=AnalysisPayload(
                observation=result.executive_summary,
                evidence=[
                    EvidenceItem(
                        source="worker_analysis",
                        finding=result.deliverable,
                    )
                ],
                hypotheses=[
                    Hypothesis(
                        claim=result.executive_summary,
                        confidence=0.8,
                    )
                ],
            ),
        )

        task.add_artifact(json.dumps(artifact.to_dict()))
        return task
