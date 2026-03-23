# kernel/artifacts/analysis.py

"""
AnalysisArtifact — findings from worker investigation.

Produced when a worker has examined data, events, or signals and
formed conclusions. This is the most common artifact type and the
one most other artifact types are derived from — recommendations,
reports, and signals all typically reference one or more analyses
in their source_artifact_ids.

The payload is designed to answer four questions every analysis must address:
  1. What did you find?         → observation, hypotheses
  2. How do you know?           → evidence (each item traceable to a source)
  3. What are you uncertain of? → gaps
  4. What should happen next?   → suggested_tasks (proposals to the orchestrator)
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from artifacts.base import ArtifactKind, BaseArtifact, BasePayload
from kernel.tasks.task import TaskDomain


# -----------------------------
# NESTED MODELS
# -----------------------------

class EvidenceItem(BasePayload):
    """
    A single piece of evidence examined during analysis.

    Each item is traceable to a named source so the eval harness
    and downstream workers know exactly where a claim came from.
    """

    source: str = Field(
        description=(
            "Named data source this evidence came from. "
            "e.g. 'shopify_orders', 'facebook_ads', 'email_open_rates'."
        ),
    )
    finding: str = Field(
        description="Plain-language description of what was observed in this source.",
    )
    period: Optional[str] = Field(
        default=None,
        description="Time window this evidence covers. e.g. '2025-04-01 to 2025-04-07'.",
    )
    metric_value: Optional[float] = Field(
        default=None,
        description="Numeric value of the key metric, if applicable.",
    )
    metric_unit: Optional[str] = Field(
        default=None,
        description="Unit for metric_value. e.g. 'orders', 'ROAS', 'USD', '%'.",
    )


class Hypothesis(BasePayload):
    """
    A causal hypothesis formed during analysis.

    Workers surface multiple ranked hypotheses rather than a single
    conclusion — this keeps the reasoning visible and eval-able.
    The orchestrator and executive agent can weigh competing hypotheses
    when deciding what follow-on work to commission.
    """

    claim: str = Field(
        description="Plain-language statement of the hypothesized cause or explanation.",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Worker's confidence that this hypothesis is correct (0–1).",
    )
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="Source names from EvidenceItem.source that support this hypothesis.",
    )
    contradicting_evidence: List[str] = Field(
        default_factory=list,
        description="Source names from EvidenceItem.source that contradict this hypothesis.",
    )


class SuggestedTask(BasePayload):
    """
    A proposal for follow-on work, surfaced by a worker within an artifact.

    SuggestedTask is NOT a real Task — it is a structured proposal that
    the orchestrator reads and decides whether to commit to the task store.
    Workers propose; the orchestrator disposes.

    Fields map directly to Task fields so the orchestrator can construct
    a real Task from this proposal with no additional inference needed.
    """

    action: str = Field(
        description="Verb describing the proposed task. e.g. 'pull', 'analyze', 'draft'.",
    )
    subject: str = Field(
        description="What the proposed task should act on. e.g. 'Facebook ad performance'.",
    )
    outcome: Optional[str] = Field(
        default=None,
        description="Desired result of the proposed task. e.g. 'identify spend inefficiencies'.",
    )
    domain: TaskDomain = Field(
        description="Domain the proposed task belongs to — used for worker routing.",
    )
    rationale: str = Field(
        description=(
            "Why this task is being suggested. Should reference specific findings "
            "or hypotheses from the artifact. This is what the orchestrator reads "
            "to decide whether to auto-commit or escalate."
        ),
    )
    urgency: str = Field(
        default="medium",
        description=(
            "Urgency hint for the orchestrator: 'low', 'medium', or 'high'. "
            "This is advisory — the orchestrator applies its own priority policy."
        ),
    )


# -----------------------------
# ANALYSIS PAYLOAD
# -----------------------------

class AnalysisPayload(BasePayload):
    """
    Payload for an AnalysisArtifact.

    Represents a worker's structured findings after examining data,
    events, or other artifacts. Designed to be fully self-documenting —
    a reader should be able to understand what was found, how, and why
    without access to any external context.
    """

    # What the worker found, in plain language.
    # Should be a crisp summary — detail lives in hypotheses and evidence.
    observation: str = Field(
        description=(
            "Top-level finding in plain language. "
            "e.g. 'Shopify revenue dropped 23% in the week of Apr 1–7 "
            "compared to the prior week.'"
        ),
    )

    # The data examined to reach this observation.
    evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description=(
            "Specific evidence items examined. Each item is traceable to a named "
            "source so findings can be audited and re-run."
        ),
    )

    # Ranked causal hypotheses — multiple hypotheses, not a single conclusion.
    hypotheses: List[Hypothesis] = Field(
        default_factory=list,
        description=(
            "Causal hypotheses ranked by confidence. Keeping multiple hypotheses "
            "explicit preserves the reasoning and allows downstream workers or "
            "the executive agent to weigh alternatives."
        ),
    )

    # What the worker couldn't determine — critical for long-running task lineage.
    gaps: List[str] = Field(
        default_factory=list,
        description=(
            "What could not be determined and why. "
            "e.g. 'Could not assess cart abandonment rate — Shopify analytics "
            "not connected.' Gaps inform the orchestrator about incomplete coverage "
            "and often map directly to suggested follow-on tasks."
        ),
    )

    # Proposals for follow-on work — proposals only, not committed tasks.
    suggested_tasks: List[SuggestedTask] = Field(
        default_factory=list,
        description=(
            "Proposed follow-on tasks for the orchestrator to evaluate. "
            "Workers propose; the orchestrator decides what gets created. "
            "Suggestions should directly address gaps or high-confidence hypotheses."
        ),
    )

    # The time window this analysis covers.
    analysis_period: Optional[str] = Field(
        default=None,
        description=(
            "The date or date range this analysis covers. "
            "e.g. '2025-04-01 to 2025-04-07'. Used for eval and audit."
        ),
    )

    # Named data sources actually consulted — distinct from evidence items,
    # which describe specific findings. This is the full inventory.
    data_sources: List[str] = Field(
        default_factory=list,
        description=(
            "All data sources consulted during this analysis. "
            "e.g. ['shopify_orders', 'facebook_ads', 'klaviyo_email']. "
            "Enables the eval harness to assess coverage."
        ),
    )


# -----------------------------
# ANALYSIS ARTIFACT
# -----------------------------

class AnalysisArtifact(BaseArtifact):
    """
    Artifact produced when a worker investigates and forms findings.

    The most common artifact type. RecommendationArtifacts,
    ReportArtifacts, and SignalArtifacts typically list one or more
    AnalysisArtifact IDs in their source_artifact_ids.
    """

    kind: ArtifactKind = Field(
        default=ArtifactKind.ANALYSIS,
        frozen=True,
        description="Always ArtifactKind.ANALYSIS for this artifact type.",
    )
    payload: AnalysisPayload

    def summary(self) -> str:
        hyp_count = len(self.payload.hypotheses)
        gap_count = len(self.payload.gaps)
        suggestion_count = len(self.payload.suggested_tasks)
        conf = f"{self.confidence:.0%}" if self.confidence is not None else "unscored"
        return (
            f"[analysis] {self.payload.observation[:80]}"
            f" | {hyp_count} hypothesis(es), {gap_count} gap(s), "
            f"{suggestion_count} suggestion(s) | confidence: {conf}"
        )
