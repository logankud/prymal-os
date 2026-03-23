# kernel/artifacts/signal.py

"""
SignalArtifact — anomaly or event worth escalating.

Produced when a worker detects something that warrants attention
but doesn't yet have enough context to produce an analysis or
recommendation. Signals are lightweight and fast — they are the
entry point for reactive workflows.

A signal is typically the first artifact in a chain:
  Signal → triggers a task → produces an Analysis → informs a Recommendation

Signals can originate from workers (a data worker notices an anomaly
while running a routine check) or from input adapters (a Shopify
webhook fires, a scheduled threshold check trips). In both cases
the SignalArtifact is the structured record of what was detected.

The eval strategy for signals is precision/recall-based:
did the signal correctly identify a real event worth investigating,
or was it noise?
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from artifacts.analysis import SuggestedTask
from artifacts.base import ArtifactKind, BaseArtifact, BasePayload


# -----------------------------
# SIGNAL PAYLOAD
# -----------------------------

class SignalPayload(BasePayload):
    """
    Payload for a SignalArtifact.

    Designed to be minimal and fast to produce — a signal should
    surface quickly. The suggested_tasks field is how the signal
    tells the orchestrator what investigation it warrants.
    """

    # What was detected.
    signal_type: str = Field(
        description=(
            "Category of signal detected. "
            "e.g. 'revenue_drop', 'cpm_spike', 'inventory_low', "
            "'open_rate_decline', 'churn_threshold_crossed'."
        ),
    )

    # How urgent this signal is.
    severity: str = Field(
        description=(
            "Severity of the signal: 'low', 'medium', 'high', or 'critical'. "
            "Informs the orchestrator's escalation and prioritization policy."
        ),
    )

    # Plain-language description of what was detected.
    message: str = Field(
        description=(
            "Plain-language description of the signal. "
            "e.g. 'Shopify daily revenue is 31% below the 7-day rolling average "
            "as of 2025-04-07. Threshold: 20% below average.'"
        ),
    )

    # The data source that produced this signal.
    source: str = Field(
        description=(
            "The system or data source where this signal was detected. "
            "e.g. 'shopify_revenue_monitor', 'facebook_ads_alert', 'klaviyo_webhook'."
        ),
    )

    # The metric value that triggered this signal, if applicable.
    metric_value: Optional[float] = Field(
        default=None,
        description="The numeric value that triggered this signal.",
    )
    metric_unit: Optional[str] = Field(
        default=None,
        description="Unit for metric_value. e.g. 'USD', '%', 'orders'.",
    )
    threshold_value: Optional[float] = Field(
        default=None,
        description="The threshold that was crossed to generate this signal.",
    )

    # What investigation this signal warrants.
    suggested_tasks: List[SuggestedTask] = Field(
        default_factory=list,
        description=(
            "Proposed investigation or response tasks for the orchestrator. "
            "A revenue_drop signal might suggest an analysis task; "
            "a critical inventory signal might suggest an action task."
        ),
    )

    # Whether this signal has already been acknowledged by a human or agent.
    acknowledged: bool = Field(
        default=False,
        description=(
            "True if this signal has been acknowledged. "
            "Unacknowledged critical signals may trigger escalation."
        ),
    )


# -----------------------------
# SIGNAL ARTIFACT
# -----------------------------

class SignalArtifact(BaseArtifact):
    """
    Artifact produced when a worker or input adapter detects an anomaly
    or threshold event worth surfacing.

    Typically the first artifact in a reasoning chain. The orchestrator
    reads the suggested_tasks on the payload and decides whether to
    commission an investigation.
    """

    kind: ArtifactKind = Field(
        default=ArtifactKind.SIGNAL,
        frozen=True,
        description="Always ArtifactKind.SIGNAL for this artifact type.",
    )
    payload: SignalPayload

    def summary(self) -> str:
        ack = "acknowledged" if self.payload.acknowledged else "unacknowledged"
        return (
            f"[signal:{self.payload.severity}] {self.payload.signal_type}"
            f" — {self.payload.message[:80]}"
            f" | {ack}"
        )
