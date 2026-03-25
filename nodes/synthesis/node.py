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


def _parse_artifact(artifact: dict) -> tuple[str, str, List[str], List[str], float | None]:
    """
    Extract (finding, detail, gaps, suggested_tasks, confidence) from a raw artifact dict.
    """
    payload = artifact.get("payload", {})
    kind = artifact.get("kind", "")

    suggested_tasks: List[str] = [
        f"{t.get('action', '')} {t.get('subject', '')}"
        for t in payload.get("suggested_tasks", [])
        if t.get("action")
    ]

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
        finding = str(payload)[:200]
        detail = str(payload)
        gaps = []

    return finding, detail, gaps, suggested_tasks, artifact.get("confidence")


def _extract_task_result(task: Task) -> TaskResult | None:
    """
    Build a TaskResult from a completed Task's artifacts.

    Combines all artifacts on the task — finding from the first,
    detail/gaps/suggested_tasks merged across all.
    Returns None if the task has no usable artifacts.
    """
    if not task.artifacts:
        return None

    all_findings: List[str] = []
    all_details: List[str] = []
    all_gaps: List[str] = []
    all_suggested: List[str] = []
    confidence: float | None = None

    for raw in task.artifacts:
        try:
            artifact = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Task %s: skipping unparseable artifact", task.task_id)
            continue

        finding, detail, gaps, suggested, conf = _parse_artifact(artifact)
        if finding:
            all_findings.append(finding)
        if detail:
            all_details.append(detail)
        all_gaps.extend(gaps)
        all_suggested.extend(suggested)
        if conf is not None and confidence is None:
            confidence = conf  # use first artifact's confidence

    if not all_findings and not all_details:
        return None

    return TaskResult(
        task_id=task.task_id,
        action=task.objective.action,
        subject=task.objective.subject,
        outcome=task.objective.outcome,
        domain=task.domain.value,
        finding=" | ".join(all_findings),
        detail="\n\n---\n\n".join(all_details),
        confidence=confidence,
        gaps=all_gaps,
        suggested_tasks=all_suggested,
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
