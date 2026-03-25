"""
SynthesisNode — the final node in the OpsIQ pipeline.

Receives a WorkRequest whose tasks are all terminal, loads the artifacts
produced by each task, distills them into TaskResult objects, and runs
the SynthesizeResponseSignature to produce a structured SynthesisResult.

The SynthesisResult is written back to the WorkRequest and the WorkRequest
is marked COMPLETE. Delivery (Slack, UI, etc.) reads from the synthesis result.
"""

from __future__ import annotations

import json
import logging
from typing import List

import dspy

from config.core import ModelClass
from kernel.model import get_lm
from kernel.tasks.task import Task, TaskStatus
from kernel.tasks.task_store import TaskStore
from kernel.work_request.work_request import WorkRequest, WorkRequestStatus
from kernel.work_request.work_request_store import WorkRequestStore
from signatures.synthesis import SynthesizeResponseSignature, TaskResult
from signatures.synthesis.types import SynthesisResult

logger = logging.getLogger(__name__)


def _extract_task_result(task: Task) -> TaskResult | None:
    """
    Build a TaskResult from a completed Task's artifact payload.

    Supports both ReportArtifact (has executive_summary + sections)
    and AnalysisArtifact (has observation + hypotheses).
    Returns None if the task has no usable artifacts.
    """
    if not task.artifacts:
        return None

    try:
        artifact = json.loads(task.artifacts[0])
    except (json.JSONDecodeError, IndexError):
        logger.warning("Task %s: could not parse artifact JSON", task.task_id)
        return None

    payload = artifact.get("payload", {})
    kind = artifact.get("kind", "")

    # Extract primary finding and detail based on artifact kind
    if kind == "report":
        finding = payload.get("executive_summary", "")
        sections = payload.get("sections", [])
        detail = "\n\n".join(
            f"**{s.get('title', '')}**\n{s.get('body', '')}" for s in sections
        )
        gaps: List[str] = []

    elif kind == "analysis":
        finding = payload.get("observation", "")
        hypotheses = payload.get("hypotheses", [])
        detail = "\n".join(
            f"- {h.get('claim', '')} (confidence: {h.get('confidence', 0):.0%})"
            for h in hypotheses
        )
        gaps = payload.get("gaps", [])

    else:
        # Fallback: treat entire payload as detail
        finding = str(payload)[:200]
        detail = str(payload)
        gaps = []

    return TaskResult(
        task_id=task.task_id,
        action=task.objective.action,
        subject=task.objective.subject,
        outcome=task.objective.outcome,
        domain=task.domain.value,
        finding=finding,
        detail=detail,
        confidence=artifact.get("confidence"),
        gaps=gaps,
    )


class SynthesisNode:
    """
    Synthesizes all task artifacts for a WorkRequest into a single response.

    Uses ModelClass.BEST — this is the most important node in the pipeline.
    """

    def __init__(self) -> None:
        self._lm = get_lm(ModelClass.BEST)
        self._predict = dspy.ChainOfThought(SynthesizeResponseSignature)

    def synthesize(
        self,
        work_request: WorkRequest,
        task_store: TaskStore,
        work_request_store: WorkRequestStore,
    ) -> SynthesisResult | None:
        """
        Run synthesis for a READY_FOR_SYNTHESIS WorkRequest.

        Updates the WorkRequest in-place and persists the result.
        Returns the SynthesisResult, or None if synthesis could not run.
        """
        tasks = task_store.list_tasks_by_work_request(work_request.work_request_id)

        if not tasks:
            logger.warning(
                "WorkRequest %s has no tasks — cannot synthesize.",
                work_request.work_request_id,
            )
            work_request.mark_failed()
            work_request_store.update(work_request)
            return None

        task_results: List[TaskResult] = []
        for task in tasks:
            result = _extract_task_result(task)
            if result is not None:
                task_results.append(result)

        if not task_results:
            logger.warning(
                "WorkRequest %s: all tasks had no parseable artifacts.",
                work_request.work_request_id,
            )
            work_request.mark_failed()
            work_request_store.update(work_request)
            return None

        work_request.mark_synthesizing()
        work_request_store.update(work_request)

        try:
            with dspy.context(lm=self._lm):
                prediction = self._predict(
                    user_request=work_request.raw_text,
                    task_results=task_results,
                )
            synthesis: SynthesisResult = prediction.synthesis

        except Exception as exc:
            logger.error(
                "Synthesis failed for WorkRequest %s: %s",
                work_request.work_request_id,
                exc,
            )
            work_request.mark_failed()
            work_request_store.update(work_request)
            return None

        work_request.mark_complete(synthesis.model_dump())
        work_request_store.update(work_request)

        logger.info(
            "WorkRequest %s synthesized (confidence=%.2f, sections=%d).",
            work_request.work_request_id,
            synthesis.confidence,
            len(synthesis.sections),
        )
        return synthesis
