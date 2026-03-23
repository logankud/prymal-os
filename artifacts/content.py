# kernel/artifacts/content.py

"""
ContentArtifact — generated copy ready for use.

Produced when a worker generates usable content: email drafts,
ad copy, campaign briefs, product descriptions, social posts.
Unlike analysis or recommendation artifacts which inform decisions,
content artifacts ARE the deliverable — they go directly to a
channel or a human for review before publishing.

The eval strategy for content is different from other artifact types:
quality is assessed on tone, relevance, and channel fit rather than
on factual accuracy or causal reasoning.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from artifacts.base import ArtifactKind, BaseArtifact, BasePayload


# -----------------------------
# CONTENT PAYLOAD
# -----------------------------

class ContentPayload(BasePayload):
    """
    Payload for a ContentArtifact.

    Carries the generated content alongside the metadata needed
    to evaluate it, route it to the right channel, and audit
    how it was produced.
    """

    # The generated content itself.
    content: str = Field(
        description=(
            "The generated content in full. For emails this is the body copy. "
            "For ad copy this is the headline and body. For briefs this is the "
            "full document. No truncation — the complete deliverable."
        ),
    )

    # What type of content this is.
    content_type: str = Field(
        description=(
            "The kind of content generated. "
            "e.g. 'email', 'ad_copy', 'campaign_brief', 'product_description', "
            "'social_post', 'sms'."
        ),
    )

    # Where this content is intended to be used.
    channel: str = Field(
        description=(
            "The distribution channel this content is intended for. "
            "e.g. 'klaviyo', 'facebook_ads', 'instagram', 'shopify_pdp', 'sms'."
        ),
    )

    # Who this content is written for.
    target_audience: str = Field(
        description=(
            "Description of the intended audience. "
            "e.g. 'Lapsed customers who purchased more than 90 days ago', "
            "'New visitors from paid search', 'Loyalty program members'."
        ),
    )

    # The subject line, headline, or title — separate from body for eval.
    subject_or_headline: Optional[str] = Field(
        default=None,
        description=(
            "Subject line (email), headline (ad), or title (brief/post). "
            "Stored separately from body so it can be scored and A/B tested "
            "independently."
        ),
    )

    # Tone guidance used to generate this content.
    tone: Optional[str] = Field(
        default=None,
        description=(
            "Tone applied during generation. "
            "e.g. 'warm and conversational', 'urgent', 'professional'. "
            "Stored for eval and regeneration consistency."
        ),
    )

    # Call to action, if applicable.
    call_to_action: Optional[str] = Field(
        default=None,
        description=(
            "Primary call to action. "
            "e.g. 'Shop now', 'Claim your discount', 'Learn more'."
        ),
    )

    # Any variables or personalization tokens used.
    personalization_tokens: List[str] = Field(
        default_factory=list,
        description=(
            "Merge tags or personalization tokens present in the content. "
            "e.g. ['{{first_name}}', '{{last_purchase_date}}']. "
            "Used to validate content before sending."
        ),
    )

    # Word or character count — useful for channel compliance checks.
    character_count: Optional[int] = Field(
        default=None,
        description="Character count of the generated content body.",
    )


# -----------------------------
# CONTENT ARTIFACT
# -----------------------------

class ContentArtifact(BaseArtifact):
    """
    Artifact produced when a worker generates ready-to-use content.

    The source_artifact_ids field should reference the analysis or
    recommendation artifacts that informed the content strategy —
    preserving the link between the data insight and the creative output.
    """

    kind: ArtifactKind = Field(
        default=ArtifactKind.CONTENT,
        frozen=True,
        description="Always ArtifactKind.CONTENT for this artifact type.",
    )
    payload: ContentPayload

    def summary(self) -> str:
        conf = f"{self.confidence:.0%}" if self.confidence is not None else "unscored"
        headline = self.payload.subject_or_headline or "(no headline)"
        return (
            f"[content] {self.payload.content_type} for {self.payload.channel}"
            f" — {headline[:60]}"
            f" | audience: {self.payload.target_audience[:40]}"
            f" | confidence: {conf}"
        )
