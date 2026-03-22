"""
Shared output types for the ingress signature pipeline.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ParsedIntent(BaseModel):
    """
    A single structured work intent extracted from user input.

    Produced by the precision pass (RefineIntentSignature) after the
    recall pass (ExtractIntentSignature) has enumerated all candidate intents.
    """

    action: str = Field(
        description=(
            "Primary action verb describing the work to be done. "
            "Examples: analyze, create, optimize, research, review, generate, plan, summarize."
        )
    )
    subject: str = Field(
        description="The specific entity, topic, or asset the action applies to."
    )
    outcome: str | None = Field(
        default=None,
        description=(
            "The desired result or goal of the work. "
            "None if not clearly stated."
        ),
    )
    domain: Literal["marketing", "operations", "research", "general"] = Field(
        description="Business domain that owns this work."
    )
