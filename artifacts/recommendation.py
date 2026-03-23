# kernel/artifacts/recommendation.py

"""
RecommendationArtifact — ranked actions with rationale.

Produced when a worker has moved beyond analysis into prescription:
not just what happened, but what should be done about it. A
recommendation artifact is typically derived from one or more
analysis artifacts (listed in source_artifact_ids) and is the
most likely type to trigger a Decision record at tier 3.

Each recommendation item is independently scoreable — the eval
harness can assess whether accepted recommendations led to the
expected outcomes over time, building a performance record per
worker and per domain.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from artifacts.analysis import SuggestedTask
from artifacts.base import ArtifactKind, BaseArtifact, BasePayload


# -----------------------------
# NESTED MODELS
# -----------------------------

class RecommendationItem(BasePayload):
    """
    A single recommended action with supporting rationale.

    Items are ordered by priority (1 = highest). Each item stands
    alone — a downstream worker or human reviewer can evaluate it
    without reading the others.
    """

    action: str = Field(
        description=(
            "The recommended action in plain language. "
            "e.g. 'Pause the Facebook retargeting campaign for segment A.'"
        ),
    )
    rationale: str = Field(
        description=(
            "Why this action is recommended. Should reference specific evidence "
            "or hypotheses from the analysis it was derived from."
        ),
    )
    expected_impact: str = Field(
        description=(
            "What outcome is expected if this action is taken. "
            "e.g. 'Estimated 15–20% reduction in wasted ad spend over 7 days.'"
        ),
    )
    priority: int = Field(
        ge=1,
        description=(
            "Relative priority among items in this artifact. "
            "1 = highest priority. No upper bound — assigned by the worker."
        ),
    )
    effort: Optional[str] = Field(
        default=None,
        description=(
            "Estimated effort to execute. e.g. 'low', 'medium', 'high', "
            "or a freeform estimate like '~2 hours'."
        ),
    )
    reversible: Optional[bool] = Field(
        default=None,
        description=(
            "Whether this action can be undone if outcomes are negative. "
            "Informs the orchestrator's escalation policy — irreversible actions "
            "should route through human review."
        ),
    )


# -----------------------------
# RECOMMENDATION PAYLOAD
# -----------------------------

class RecommendationPayload(BasePayload):
    """
    Payload for a RecommendationArtifact.

    Represents a worker's ranked prescription for action. The payload
    is self-contained — the context, items, and follow-on proposals
    are all present without requiring the reader to consult other artifacts.
    """

    # Plain-language framing of the situation being addressed.
    context: str = Field(
        description=(
            "Brief description of the situation or problem these recommendations "
            "address. Should be understandable without reading the source analysis. "
            "e.g. 'Revenue dropped 23% in the week of Apr 1–7, likely driven by "
            "underperforming paid acquisition.'"
        ),
    )

    # The ranked list of recommended actions.
    items: List[RecommendationItem] = Field(
        description="Ranked recommended actions. Ordered by priority (1 = highest).",
    )

    # Conditions under which these recommendations may not apply.
    caveats: List[str] = Field(
        default_factory=list,
        description=(
            "Conditions or assumptions under which these recommendations may not hold. "
            "e.g. 'Assumes Facebook campaign budget has not already been adjusted.'"
        ),
    )

    # Follow-on proposals — typically for deeper investigation before acting.
    suggested_tasks: List[SuggestedTask] = Field(
        default_factory=list,
        description=(
            "Proposed follow-on tasks for the orchestrator to evaluate. "
            "Often used to suggest validation or data-gathering before "
            "high-effort or irreversible recommendations are executed."
        ),
    )


# -----------------------------
# RECOMMENDATION ARTIFACT
# -----------------------------

class RecommendationArtifact(BaseArtifact):
    """
    Artifact produced when a worker prescribes ranked actions.

    Typically derived from one or more AnalysisArtifacts. The
    source_artifact_ids field should list the analyses that informed
    these recommendations so the full reasoning chain is traceable.
    """

    kind: ArtifactKind = Field(
        default=ArtifactKind.RECOMMENDATION,
        frozen=True,
        description="Always ArtifactKind.RECOMMENDATION for this artifact type.",
    )
    payload: RecommendationPayload

    def summary(self) -> str:
        item_count = len(self.payload.items)
        top = self.payload.items[0].action[:60] if self.payload.items else "no items"
        conf = f"{self.confidence:.0%}" if self.confidence is not None else "unscored"
        return (
            f"[recommendation] {item_count} item(s) — top: {top}"
            f" | confidence: {conf}"
        )
