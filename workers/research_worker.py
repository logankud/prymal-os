from __future__ import annotations

import json

import dspy

from artifacts.analysis import AnalysisArtifact, AnalysisPayload, EvidenceItem, Hypothesis, SuggestedTask
from kernel.model import ModelClass, get_lm
from kernel.tasks.task import Task, TaskDomain
from kernel.workers.base_worker import BaseWorker
from signatures.execution.execute_task_signature import ExecuteTaskSignature


class ResearchExecuteSignature(ExecuteTaskSignature):
    """
    Execute a research task and produce thorough investigative findings.

    You are a senior research analyst. Your job is to investigate the subject
    thoroughly and surface what is known, what is uncertain, and what should
    happen next.

    - Lead with the most important finding.
    - Distinguish between what you know with confidence vs. what is uncertain.
    - Surface gaps in information explicitly — this is as valuable as findings.
    - Propose concrete follow-on questions or work if the research is incomplete.

    Cite reasoning. Do not speculate without flagging it. Be precise.
    """


class ResearchWorker(BaseWorker):
    def __init__(self) -> None:
        super().__init__(worker_id="research_worker")
        self._lm = get_lm(ModelClass.BEST)
        self._predict = dspy.ChainOfThought(ResearchExecuteSignature)

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
                        source="research_analysis",
                        finding=result.deliverable,
                    )
                ],
                hypotheses=[
                    Hypothesis(
                        claim=result.executive_summary,
                        confidence=0.75,
                    )
                ],
                suggested_tasks=[
                    SuggestedTask(
                        action="review",
                        subject=f"findings on {task.objective.subject}",
                        outcome="validate research conclusions and identify follow-on work",
                        domain=TaskDomain.RESEARCH,
                        rationale="Research tasks typically surface follow-on questions requiring validation.",
                    )
                ],
            ),
        )

        task.add_artifact(json.dumps(artifact.to_dict()))
        return task
