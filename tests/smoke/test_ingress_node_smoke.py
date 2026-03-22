"""Smoke tests for the IngressNode two-pass DSPy pipeline."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from kernel.nodes.result import NodeStatus
from nodes.ingress.node import IngressNode
from nodes.ingress.schema import IngressEventType
from signatures.ingress.types import ParsedIntent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(text: str, event_type: str = IngressEventType.USER_TEXT) -> dict:
    return {"event_type": event_type, "text": text}


def _make_extract_result(candidates: list[str]) -> SimpleNamespace:
    return SimpleNamespace(intent_candidates=candidates)


def _make_refine_result(action: str, subject: str, outcome: str | None, domain: str) -> SimpleNamespace:
    return SimpleNamespace(
        intent=ParsedIntent(action=action, subject=subject, outcome=outcome, domain=domain)
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_lm():
    """Patch get_lm so IngressNode.__init__ doesn't require a real config or API key."""
    with patch("nodes.ingress.node.get_lm", return_value=MagicMock()) as mock:
        yield mock


# ---------------------------------------------------------------------------
# Scenario 1: single intent — happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_single_intent_returns_success(mock_lm):
    node = IngressNode()

    node._extract = MagicMock(return_value=_make_extract_result(
        ["Analyze Q2 churn rate"]
    ))
    node._refine = MagicMock(return_value=_make_refine_result(
        action="analyze",
        subject="Q2 churn rate",
        outcome=None,
        domain="research",
    ))

    state = {"ingress_event": _make_event("Analyze our Q2 churn rate")}
    result = await node.run(state)

    assert result.status == NodeStatus.SUCCESS
    assert result.ok

    intents = result.state_patch["intents"]
    assert len(intents) == 1
    assert intents[0]["action"] == "analyze"
    assert intents[0]["subject"] == "Q2 churn rate"
    assert intents[0]["domain"] == "research"


async def test_single_intent_emits_observations(mock_lm):
    node = IngressNode()

    node._extract = MagicMock(return_value=_make_extract_result(["Analyze Q2 churn rate"]))
    node._refine = MagicMock(return_value=_make_refine_result("analyze", "Q2 churn rate", None, "research"))

    state = {"ingress_event": _make_event("Analyze our Q2 churn rate")}
    result = await node.run(state)

    observation_names = [o.name for o in result.observations]
    assert "extract_pass" in observation_names
    assert "intent_refined" in observation_names
    assert result.metrics["candidates_found"] == 1
    assert result.metrics["intents_refined"] == 1


# ---------------------------------------------------------------------------
# Scenario 2: multiple candidates — node loops and produces all intents
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_multiple_candidates_produces_multiple_intents(mock_lm):
    node = IngressNode()

    node._extract = MagicMock(return_value=_make_extract_result([
        "Analyze Q2 churn rate",
        "Create a win-back campaign for lapsed enterprise accounts",
    ]))
    node._refine = MagicMock(side_effect=[
        _make_refine_result("analyze", "Q2 churn rate", None, "research"),
        _make_refine_result("create", "win-back campaign", "re-engage lapsed enterprise accounts", "marketing"),
    ])

    state = {"ingress_event": _make_event("Analyze Q2 churn and create a win-back campaign")}
    result = await node.run(state)

    assert result.status == NodeStatus.SUCCESS
    assert len(result.state_patch["intents"]) == 2
    assert result.metrics["candidates_found"] == 2
    assert result.metrics["intents_refined"] == 2


# ---------------------------------------------------------------------------
# Scenario 3: partial refine failure — one candidate fails, rest succeed
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_partial_refine_failure_returns_partial_success(mock_lm):
    node = IngressNode()

    node._extract = MagicMock(return_value=_make_extract_result([
        "Analyze Q2 churn rate",
        "Create a win-back campaign",
    ]))
    node._refine = MagicMock(side_effect=[
        _make_refine_result("analyze", "Q2 churn rate", None, "research"),
        RuntimeError("LLM call failed"),
    ])

    state = {"ingress_event": _make_event("Analyze Q2 churn and create a win-back campaign")}
    result = await node.run(state)

    assert result.status == NodeStatus.PARTIAL_SUCCESS
    assert len(result.state_patch["intents"]) == 1
    assert result.metrics["intents_refined"] == 1
    assert result.metrics["refine_errors"] == 1
    assert len(result.errors) == 1


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_missing_ingress_event_returns_failed(mock_lm):
    node = IngressNode()
    result = await node.run({})
    assert result.status == NodeStatus.FAILED


@pytest.mark.asyncio
async def test_empty_text_returns_failed(mock_lm):
    node = IngressNode()
    state = {"ingress_event": _make_event("   ")}
    result = await node.run(state)
    assert result.status == NodeStatus.FAILED
