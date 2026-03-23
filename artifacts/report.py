# kernel/artifacts/report.py

"""
ReportArtifact — synthesized multi-source narrative.

Produced when a worker synthesizes findings across multiple analyses,
data sources, or time periods into a coherent narrative. Reports are
typically produced by the executive agent or a dedicated reporting
worker, and almost always have multiple source_artifact_ids.

Reports are the primary artifact type consumed by humans — they are
designed to be readable without technical context and to surface
the most important information first.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from artifacts.analysis import SuggestedTask
from artifacts.base import ArtifactKind, BaseArtifact, BasePayload


# -----------------------------
# NESTED MODELS
# -----------------------------

class ReportSection(BasePayload):
    """
    A single section within a report.

    Sections allow the report to be structured and navigable.
    Each section can be independently scored by the eval harness.
    """

    title: str = Field(
        description="Section heading. e.g. 'Revenue performance', 'Key risks'.",
    )
    body: str = Field(
        description="Section content in plain language.",
    )
    source_artifact_ids: List[str] = Field(
        default_factory=list,
        description=(
            "IDs of the specific artifacts this section was derived from. "
            "More granular than the top-level source_artifact_ids on the artifact — "
            "allows tracing individual claims within a report to their source."
        ),
    )


# -----------------------------
# REPORT PAYLOAD
# -----------------------------

class ReportPayload(BasePayload):
    """
    Payload for a ReportArtifact.

    Structured as a title, executive summary, and ordered sections.
    Designed to be readable as a standalone document.
    """

    title: str = Field(
        description="Report title. e.g. 'Weekly operations summary — Apr 1–7 2025'.",
    )

    # The most important 2–3 sentences. Read first, written last.
    executive_summary: str = Field(
        description=(
            "2–3 sentence summary of the most important findings and recommended "
            "actions. Should be readable without the rest of the report."
        ),
    )

    sections: List[ReportSection] = Field(
        description="Ordered report sections. Readers consume these sequentially.",
    )

    # Time window covered by this report.
    reporting_period: Optional[str] = Field(
        default=None,
        description="The date range this report covers. e.g. '2025-04-01 to 2025-04-07'.",
    )

    # Follow-on proposals surfaced during synthesis.
    suggested_tasks: List[SuggestedTask] = Field(
        default_factory=list,
        description=(
            "Proposed follow-on tasks identified during report synthesis. "
            "Often higher-level than suggestions in individual analyses — "
            "e.g. a strategic initiative rather than a tactical investigation."
        ),
    )


# -----------------------------
# REPORT ARTIFACT
# -----------------------------

class ReportArtifact(BaseArtifact):
    """
    Artifact produced when a worker synthesizes findings into a narrative.

    Typically produced by the executive agent. The source_artifact_ids
    field should comprehensively list every analysis and recommendation
    artifact that contributed to this report.
    """

    kind: ArtifactKind = Field(
        default=ArtifactKind.REPORT,
        frozen=True,
        description="Always ArtifactKind.REPORT for this artifact type.",
    )
    payload: ReportPayload

    def summary(self) -> str:
        section_count = len(self.payload.sections)
        source_count = len(self.source_artifact_ids)
        conf = f"{self.confidence:.0%}" if self.confidence is not None else "unscored"
        return (
            f"[report] {self.payload.title}"
            f" | {section_count} section(s) from {source_count} source artifact(s)"
            f" | confidence: {conf}"
        )
