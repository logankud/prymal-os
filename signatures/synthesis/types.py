"""
Structured types for the synthesis layer.

These are the input/output contracts for the SynthesizeResponseSignature.
Using Pydantic models directly so DSPy handles structured I/O natively —
no manual serialization needed.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class TaskResult(BaseModel):
    """
    A distilled view of a completed task — what was asked and what was produced.

    Built by the SynthesisNode from a Task + its artifacts. This is what
    the synthesizer receives: enough context to reason about the work without
    needing to decode raw artifact JSON.
    """

    task_id: str = Field(description="ID of the completed task")
    action: str = Field(description="Action verb from the task objective")
    subject: str = Field(description="Subject of the task objective")
    outcome: Optional[str] = Field(default=None, description="Intended outcome of the task")
    domain: str = Field(description="Business domain: operations, marketing, research, general")

    # Distilled worker output
    finding: str = Field(
        description=(
            "The worker's primary finding — the executive summary or top observation "
            "from the artifact. This is the most important thing the worker determined."
        )
    )
    detail: str = Field(
        description=(
            "Full detail from the worker's deliverable. May be long. "
            "Synthesizer should extract what's relevant, not quote verbatim."
        )
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Worker-reported confidence in this result (0–1).",
    )
    gaps: List[str] = Field(
        default_factory=list,
        description="Things the worker could not determine. Critical for gating synthesis confidence.",
    )


class SynthesisSection(BaseModel):
    """A single section in the synthesized response."""

    title: str = Field(description="Section heading — short and specific")
    content: str = Field(description="Section body in plain language")


class SynthesisResult(BaseModel):
    """
    The structured output of the SynthesisNode.

    This is what gets delivered to the user — either via Slack, UI,
    or any other delivery channel. It must stand alone without any
    additional context.

    Confidence gating: if confidence < 0.5, the delivery layer should
    prefer surfacing open_questions over stating findings as fact.
    """

    title: str = Field(description="Response title — a concise restatement of what was accomplished")

    executive_summary: str = Field(
        description=(
            "2–3 sentences directly answering the user's original request. "
            "Written for a non-technical reader. "
            "If confidence is low, lead with what is uncertain."
        )
    )

    sections: List[SynthesisSection] = Field(
        description=(
            "Supporting detail, organized by topic. "
            "Each section should correspond to a distinct finding or thread of work."
        )
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Overall confidence in this synthesis (0–1). "
            "Set below 0.5 if the artifacts do not sufficiently support the response, "
            "if critical data was unavailable, or if findings are speculative."
        ),
    )

    open_questions: List[str] = Field(
        default_factory=list,
        description=(
            "Questions that could not be answered due to missing data or worker gaps. "
            "These are surfaced to the user so they know what remains unresolved."
        ),
    )
