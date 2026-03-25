"""
Integration tests for the synthesis layer.

Tests cover:
- WorkRequest created at intake with correct task linkage
- WorkRequest advances to READY_FOR_SYNTHESIS when all tasks complete
- SynthesisNode produces a structured SynthesisResult
- Low-confidence result when artifacts are empty/sparse
- Delivery callback fires with (WorkRequest, SynthesisResult)
- Synthesis skipped (gracefully) if no tasks have artifacts
- list_by_status query on WorkRequestStore
"""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from kernel.tasks.task import Objective, Task, TaskDomain, TaskPriority, TaskStatus
from kernel.work_request.work_request import WorkRequest, WorkRequestStatus
from kernel.work_request.work_request_store import WorkRequestStore
from signatures.synthesis.types import SynthesisResult, SynthesisSection, TaskResult


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_storage():
    """In-memory SQLite storage."""
    from kernel.storage.sqllite import SQLiteStorage
    return SQLiteStorage(db_path=":memory:")


def make_task_store(storage):
    from kernel.tasks.task_store import TaskStore
    ts = TaskStore(storage)
    ts.initialize()
    return ts


def make_wr_store(storage):
    wrs = WorkRequestStore(storage)
    wrs.initialize()
    return wrs


def make_task(
    work_request_id: str,
    intent_index: int = 0,
    status: TaskStatus = TaskStatus.COMPLETED,
    with_report_artifact: bool = False,
    with_analysis_artifact: bool = False,
) -> Task:
    task = Task(
        objective=Objective(action="analyze", subject="pipeline health", outcome="report"),
        domain=TaskDomain.OPERATIONS,
        created_by="test",
        work_request_id=work_request_id,
        intent_index=intent_index,
    )
    task.status = status

    if with_report_artifact:
        artifact = {
            "kind": "report",
            "task_id": task.task_id,
            "worker_id": "general_worker",
            "payload": {
                "title": "Pipeline Health Report",
                "executive_summary": "Pipeline is operating within normal parameters.",
                "sections": [{"title": "Status", "body": "All systems green."}],
            },
        }
        task.artifacts = [json.dumps(artifact)]

    if with_analysis_artifact:
        artifact = {
            "kind": "analysis",
            "task_id": task.task_id,
            "worker_id": "operations_worker",
            "confidence": 0.8,
            "payload": {
                "observation": "Minor latency spike detected in queue processor.",
                "hypotheses": [
                    {"claim": "Backpressure from upstream service", "confidence": 0.75}
                ],
                "gaps": ["No metrics beyond last 24h available"],
            },
        }
        task.artifacts = [json.dumps(artifact)]

    return task


# ── WorkRequest lifecycle ─────────────────────────────────────────────────────

class TestWorkRequestLifecycle:
    def test_pending_transitions_to_in_progress_on_first_task(self):
        wr = WorkRequest(source="test", raw_text="check pipeline")
        assert wr.status == WorkRequestStatus.PENDING
        wr.add_task("task-1")
        assert wr.status == WorkRequestStatus.IN_PROGRESS

    def test_add_task_appends_id(self):
        wr = WorkRequest(source="test", raw_text="foo")
        wr.add_task("t1")
        wr.add_task("t2")
        assert wr.task_ids == ["t1", "t2"]

    def test_add_artifact_appends(self):
        wr = WorkRequest(source="test", raw_text="foo")
        wr.add_artifact("a1")
        assert "a1" in wr.artifact_ids

    def test_mark_synthesizing(self):
        wr = WorkRequest(source="test", raw_text="foo")
        wr.mark_synthesizing()
        assert wr.status == WorkRequestStatus.SYNTHESIZING

    def test_mark_complete_stores_result(self):
        wr = WorkRequest(source="test", raw_text="foo")
        result = {"title": "Done", "confidence": 0.9}
        wr.mark_complete(result)
        assert wr.status == WorkRequestStatus.COMPLETE
        assert wr.synthesis_result == result

    def test_mark_failed(self):
        wr = WorkRequest(source="test", raw_text="foo")
        wr.mark_failed()
        assert wr.status == WorkRequestStatus.FAILED


# ── WorkRequestStore ──────────────────────────────────────────────────────────

class TestWorkRequestStore:
    def test_create_and_get(self):
        storage = make_storage()
        store = make_wr_store(storage)

        wr = WorkRequest(source="slack", raw_text="do something", thread_id="slack:C1:ts1")
        store.create(wr)

        fetched = store.get(wr.work_request_id)
        assert fetched is not None
        assert fetched.raw_text == "do something"
        assert fetched.thread_id == "slack:C1:ts1"
        assert fetched.status == WorkRequestStatus.PENDING

    def test_update_status(self):
        storage = make_storage()
        store = make_wr_store(storage)

        wr = WorkRequest(source="test", raw_text="go")
        store.create(wr)

        wr.add_task("t1")
        store.update(wr)

        fetched = store.get(wr.work_request_id)
        assert fetched.status == WorkRequestStatus.IN_PROGRESS
        assert "t1" in fetched.task_ids

    def test_list_by_status(self):
        storage = make_storage()
        store = make_wr_store(storage)

        wr1 = WorkRequest(source="test", raw_text="one")
        wr2 = WorkRequest(source="test", raw_text="two")
        wr1.status = WorkRequestStatus.READY_FOR_SYNTHESIS
        wr2.status = WorkRequestStatus.COMPLETE

        store.create(wr1)
        store.create(wr2)

        ready = store.list_by_status(WorkRequestStatus.READY_FOR_SYNTHESIS)
        assert len(ready) == 1
        assert ready[0].raw_text == "one"

    def test_get_nonexistent_returns_none(self):
        storage = make_storage()
        store = make_wr_store(storage)
        assert store.get("does-not-exist") is None


# ── Completion check (execution loop helper) ──────────────────────────────────

class TestWorkRequestCompletionCheck:
    def test_all_terminal_advances_to_ready_for_synthesis(self):
        storage = make_storage()
        task_store = make_task_store(storage)
        wr_store = make_wr_store(storage)

        wr = WorkRequest(source="test", raw_text="analyze")
        wr_store.create(wr)

        t1 = make_task(wr.work_request_id, intent_index=0, status=TaskStatus.COMPLETED, with_analysis_artifact=True)
        t2 = make_task(wr.work_request_id, intent_index=1, status=TaskStatus.COMPLETED, with_report_artifact=True)
        task_store.create_task(t1)
        task_store.create_task(t2)
        wr.add_task(t1.task_id)
        wr.add_task(t2.task_id)
        wr_store.update(wr)

        from kernel.runtime.execution_loop import _check_work_request_completion
        _check_work_request_completion(t1, task_store, wr_store)

        # One task still not checked yet — both are COMPLETED though
        fetched = wr_store.get(wr.work_request_id)
        assert fetched.status == WorkRequestStatus.READY_FOR_SYNTHESIS

    def test_partial_completion_does_not_advance(self):
        storage = make_storage()
        task_store = make_task_store(storage)
        wr_store = make_wr_store(storage)

        wr = WorkRequest(source="test", raw_text="analyze")
        wr_store.create(wr)

        t1 = make_task(wr.work_request_id, intent_index=0, status=TaskStatus.COMPLETED)
        t2 = make_task(wr.work_request_id, intent_index=1, status=TaskStatus.QUEUED)
        task_store.create_task(t1)
        task_store.create_task(t2)
        wr.add_task(t1.task_id)
        wr.add_task(t2.task_id)
        wr_store.update(wr)

        from kernel.runtime.execution_loop import _check_work_request_completion
        _check_work_request_completion(t1, task_store, wr_store)

        fetched = wr_store.get(wr.work_request_id)
        assert fetched.status != WorkRequestStatus.READY_FOR_SYNTHESIS

    def test_task_without_work_request_id_is_skipped(self):
        storage = make_storage()
        task_store = make_task_store(storage)
        wr_store = make_wr_store(storage)

        task = Task(
            objective=Objective(action="do", subject="thing", outcome=None),
            domain=TaskDomain.GENERAL,
            created_by="test",
        )
        task.status = TaskStatus.COMPLETED

        from kernel.runtime.execution_loop import _check_work_request_completion
        # Should not raise
        _check_work_request_completion(task, task_store, wr_store)


# ── SynthesisNode ─────────────────────────────────────────────────────────────

class TestSynthesisNode:
    def _make_synthesis_result(self, confidence: float = 0.85) -> SynthesisResult:
        return SynthesisResult(
            title="Pipeline Analysis Complete",
            executive_summary="The pipeline is healthy with minor latency issues.",
            sections=[
                SynthesisSection(title="Findings", content="Latency spike in queue processor."),
            ],
            confidence=confidence,
            open_questions=["Is upstream throttling the cause?"],
        )

    def test_synthesis_marks_work_request_complete(self):
        storage = make_storage()
        task_store = make_task_store(storage)
        wr_store = make_wr_store(storage)

        wr = WorkRequest(source="test", raw_text="check pipeline health")
        wr.status = WorkRequestStatus.READY_FOR_SYNTHESIS
        wr_store.create(wr)

        t = make_task(wr.work_request_id, with_analysis_artifact=True)
        task_store.create_task(t)
        wr.add_task(t.task_id)
        wr_store.update(wr)

        mock_result = self._make_synthesis_result()
        mock_prediction = MagicMock()
        mock_prediction.synthesis = mock_result

        from nodes.synthesis.node import SynthesisNode
        node = SynthesisNode.__new__(SynthesisNode)
        node._lm = MagicMock()
        node._predict = MagicMock(return_value=mock_prediction)

        import dspy
        with patch.object(dspy, "context", return_value=MagicMock(__enter__=MagicMock(return_value=None), __exit__=MagicMock(return_value=False))):
            result = node.synthesize(wr, task_store, wr_store)

        assert result is not None
        assert result.title == "Pipeline Analysis Complete"
        assert result.confidence == 0.85

        fetched = wr_store.get(wr.work_request_id)
        assert fetched.status == WorkRequestStatus.COMPLETE
        assert fetched.synthesis_result is not None

    def test_synthesis_marks_failed_when_no_tasks(self):
        storage = make_storage()
        task_store = make_task_store(storage)
        wr_store = make_wr_store(storage)

        wr = WorkRequest(source="test", raw_text="check pipeline")
        wr.status = WorkRequestStatus.READY_FOR_SYNTHESIS
        wr_store.create(wr)

        from nodes.synthesis.node import SynthesisNode
        node = SynthesisNode.__new__(SynthesisNode)
        node._lm = MagicMock()
        node._predict = MagicMock()

        result = node.synthesize(wr, task_store, wr_store)

        assert result is None
        fetched = wr_store.get(wr.work_request_id)
        assert fetched.status == WorkRequestStatus.FAILED

    def test_synthesis_marks_failed_on_dspy_exception(self):
        storage = make_storage()
        task_store = make_task_store(storage)
        wr_store = make_wr_store(storage)

        wr = WorkRequest(source="test", raw_text="check pipeline")
        wr.status = WorkRequestStatus.READY_FOR_SYNTHESIS
        wr_store.create(wr)

        t = make_task(wr.work_request_id, with_analysis_artifact=True)
        task_store.create_task(t)
        wr.add_task(t.task_id)
        wr_store.update(wr)

        from nodes.synthesis.node import SynthesisNode
        node = SynthesisNode.__new__(SynthesisNode)
        node._lm = MagicMock()
        node._predict = MagicMock(side_effect=RuntimeError("LLM unavailable"))

        import dspy
        with patch.object(dspy, "context", return_value=MagicMock(__enter__=MagicMock(return_value=None), __exit__=MagicMock(return_value=False))):
            result = node.synthesize(wr, task_store, wr_store)

        assert result is None
        fetched = wr_store.get(wr.work_request_id)
        assert fetched.status == WorkRequestStatus.FAILED


# ── TaskResult extraction ─────────────────────────────────────────────────────

class TestTaskResultExtraction:
    def test_extract_from_analysis_artifact(self):
        from nodes.synthesis.node import _extract_task_result

        t = make_task("wr-1", with_analysis_artifact=True)
        result = _extract_task_result(t)

        assert result is not None
        assert result.action == "analyze"
        assert "latency" in result.finding.lower()
        assert result.confidence == 0.8
        assert len(result.gaps) == 1

    def test_extract_from_report_artifact(self):
        from nodes.synthesis.node import _extract_task_result

        t = make_task("wr-1", with_report_artifact=True)
        result = _extract_task_result(t)

        assert result is not None
        assert "pipeline" in result.finding.lower() or "normal parameters" in result.finding.lower()
        assert result.gaps == []

    def test_extract_from_task_with_no_artifacts(self):
        from nodes.synthesis.node import _extract_task_result

        t = make_task("wr-1")
        result = _extract_task_result(t)

        assert result is None


# ── Slack synthesis delivery ──────────────────────────────────────────────────

class TestSlackSynthesisDelivery:
    def _make_synthesis(self, confidence: float = 0.85) -> SynthesisResult:
        return SynthesisResult(
            title="Test Report",
            executive_summary="Everything is fine.",
            sections=[SynthesisSection(title="Details", content="Nothing to report.")],
            confidence=confidence,
        )

    def test_delivery_posts_to_slack_thread(self):
        from integrations.slack.delivery import make_synthesis_delivery_callback

        mock_client = MagicMock()
        with patch("integrations.slack.delivery.WebClient", return_value=mock_client):
            callback = make_synthesis_delivery_callback("xoxb-fake-token")

        wr = WorkRequest(
            source="slack",
            raw_text="analyze pipeline",
            thread_id="slack:C123:1234567890.123",
        )
        callback(wr, self._make_synthesis())

        mock_client.chat_postMessage.assert_called_once()
        call_kwargs = mock_client.chat_postMessage.call_args[1]
        assert call_kwargs["channel"] == "C123"
        assert call_kwargs["thread_ts"] == "1234567890.123"
        assert "Test Report" in call_kwargs["text"]

    def test_low_confidence_includes_warning(self):
        from integrations.slack.delivery import make_synthesis_delivery_callback

        mock_client = MagicMock()
        with patch("integrations.slack.delivery.WebClient", return_value=mock_client):
            callback = make_synthesis_delivery_callback("xoxb-fake-token")

        wr = WorkRequest(source="slack", raw_text="foo", thread_id="slack:C1:ts1")
        callback(wr, self._make_synthesis(confidence=0.3))

        text = mock_client.chat_postMessage.call_args[1]["text"]
        assert "Low confidence" in text or "30%" in text

    def test_non_slack_thread_is_skipped(self):
        from integrations.slack.delivery import make_synthesis_delivery_callback

        mock_client = MagicMock()
        with patch("integrations.slack.delivery.WebClient", return_value=mock_client):
            callback = make_synthesis_delivery_callback("xoxb-fake-token")

        wr = WorkRequest(source="api", raw_text="foo", thread_id=None)
        callback(wr, self._make_synthesis())

        mock_client.chat_postMessage.assert_not_called()

    def test_open_questions_appear_in_message(self):
        from integrations.slack.delivery import make_synthesis_delivery_callback

        mock_client = MagicMock()
        with patch("integrations.slack.delivery.WebClient", return_value=mock_client):
            callback = make_synthesis_delivery_callback("xoxb-fake-token")

        wr = WorkRequest(source="slack", raw_text="foo", thread_id="slack:C1:ts1")
        synthesis = SynthesisResult(
            title="Report",
            executive_summary="Summary.",
            sections=[],
            confidence=0.7,
            open_questions=["What caused the spike?", "Is it recurring?"],
        )
        callback(wr, synthesis)

        text = mock_client.chat_postMessage.call_args[1]["text"]
        assert "What caused the spike?" in text

    def test_no_token_returns_noop(self):
        from integrations.slack.delivery import make_synthesis_delivery_callback

        callback = make_synthesis_delivery_callback("")

        wr = WorkRequest(source="slack", raw_text="foo", thread_id="slack:C1:ts1")
        # Should not raise
        callback(wr, self._make_synthesis())
