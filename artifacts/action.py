# kernel/artifacts/action.py

"""
ActionArtifact — record of something executed externally.

Produced when a worker has taken an action in an external system:
paused an ad campaign, sent an email, updated a Shopify tag,
triggered a webhook. This is the artifact type that makes OpsIQ
genuinely agentic rather than just analytical.

ActionArtifacts are immutable audit records. Unlike other artifact
types which represent knowledge, an ActionArtifact represents something
that happened in the real world. The `rollback_hint` field supports
human oversight — if an action was taken in error, the reviewer
has a structured description of how to undo it.

The eval strategy for actions is outcome-based: was the action
taken correctly, did it produce the expected result, and was it
reversible if needed?
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field

from artifacts.base import ArtifactKind, BaseArtifact, BasePayload


# -----------------------------
# ACTION PAYLOAD
# -----------------------------

class ActionPayload(BasePayload):
    """
    Payload for an ActionArtifact.

    Records what was done, where, with what parameters, and what
    happened as a result. Designed to be a complete audit record
    that a human reviewer can understand without additional context.
    """

    # What action was taken, in plain language.
    action_taken: str = Field(
        description=(
            "Plain-language description of the action taken. "
            "e.g. 'Paused Facebook ad set 12345678 targeting segment A.'"
        ),
    )

    # Which external system was acted upon.
    target_system: str = Field(
        description=(
            "The external system or service the action was taken in. "
            "e.g. 'facebook_ads', 'klaviyo', 'shopify', 'google_ads'."
        ),
    )

    # The specific resource acted upon within the target system.
    target_resource: Optional[str] = Field(
        default=None,
        description=(
            "The specific resource ID or name acted upon within the target system. "
            "e.g. an ad set ID, a campaign name, a customer segment ID."
        ),
    )

    # The parameters passed to the external system.
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Key-value parameters used to execute the action. "
            "Stored verbatim for audit and replay purposes."
        ),
    )

    # What the external system returned.
    result: str = Field(
        description=(
            "Plain-language description of what happened after the action. "
            "e.g. 'Ad set status updated to PAUSED. Confirmed via API response.'"
        ),
    )

    # Whether the action succeeded.
    success: bool = Field(
        description="True if the action completed successfully, False if it failed.",
    )

    # Error details if the action failed.
    error_detail: Optional[str] = Field(
        default=None,
        description=(
            "Error message or detail if success is False. "
            "Should be sufficient to diagnose the failure without external context."
        ),
    )

    # How to undo this action — critical for human oversight.
    rollback_hint: Optional[str] = Field(
        default=None,
        description=(
            "Plain-language description of how to reverse this action if needed. "
            "e.g. 'Re-enable ad set 12345678 in Facebook Ads Manager, or via API: "
            "PATCH /adsets/12345678 status=ACTIVE.' "
            "Required for irreversible or high-impact actions."
        ),
    )

    # External reference ID returned by the target system, if any.
    external_reference_id: Optional[str] = Field(
        default=None,
        description=(
            "ID or reference returned by the external system for this action. "
            "e.g. a Klaviyo campaign send ID, a Shopify order ID."
        ),
    )


# -----------------------------
# ACTION ARTIFACT
# -----------------------------

class ActionArtifact(BaseArtifact):
    """
    Artifact produced when a worker executes an action in an external system.

    Represents something that happened in the real world. Treated as an
    immutable audit record — the payload should never be modified after
    creation, even if the action is later reversed.

    The source_artifact_ids should reference the recommendation artifact
    that authorized this action, preserving the full chain from
    data insight → recommendation → execution.
    """

    kind: ArtifactKind = Field(
        default=ArtifactKind.ACTION,
        frozen=True,
        description="Always ArtifactKind.ACTION for this artifact type.",
    )
    payload: ActionPayload

    def summary(self) -> str:
        status = "succeeded" if self.payload.success else "FAILED"
        return (
            f"[action] {self.payload.action_taken[:80]}"
            f" | {self.payload.target_system} | {status}"
        )
