# kernel/artifacts/base.py

"""
Artifact Model for OpsIQ

Artifacts are the typed outputs of worker execution.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


# -----------------------------
# ENUMS
# -----------------------------

class ArtifactKind(str, Enum):
    """
    Discriminator for artifact payload types.

    Each kind maps to a distinct payload schema and eval strategy.
    """
    ANALYSIS       = "analysis"        # findings from investigation
    RECOMMENDATION = "recommendation"  # ranked actions with rationale
    CONTENT        = "content"         # generated copy, emails, briefs
    REPORT         = "report"          # synthesized multi-source narrative
    ACTION         = "action"          # record of something executed externally
    SIGNAL         = "signal"          # anomaly or event worth escalating


# -----------------------------
# BASE PAYLOAD
# -----------------------------

class BasePayload(BaseModel):
    """
    Marker base for all artifact payloads.

    All payload subclasses extend this. Keeping a shared base means
    the ArtifactStore and eval harness can accept any payload without
    losing type information.
    """

    model_config = {"extra": "forbid"}

# -----------------------------
# BASE ARTIFACT
# -----------------------------

class BaseArtifact(BaseModel):
    """
    Root model for all OpsIQ artifacts.

    Subclasses declare a concrete `payload` type by overriding the
    field annotation — Pydantic handles validation and serialization
    of the narrower type automatically.

    Usage:
        class AnalysisArtifact(BaseArtifact):
            kind: ArtifactKind = ArtifactKind.ANALYSIS
            payload: AnalysisPayload

    The `kind` field doubles as the discriminator for union-type
    deserialization (e.g. when loading from the ArtifactStore).

    Lineage fields (task_id, parent_task_id, source_artifact_ids, thread_id)
    together form a directed graph of how and why this artifact came to exist.
    They are sufficient to reconstruct the full reasoning chain without
    additional lookups, and are the foundation for the OpsIQ knowledge graph.
    """

    # -----------------------------
    # IDENTITY
    # -----------------------------

    artifact_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this artifact.",
    )

    # -----------------------------
    # PROVENANCE / LINEAGE
    # -----------------------------

    task_id: str = Field(
        description="ID of the immediate task that produced this artifact.",
    )
    parent_task_id: Optional[str] = Field(
        default=None,
        description=(
            "ID of the parent task, if this artifact was produced within a subtask. "
            "Enables upward traversal of the task hierarchy."
        ),
    )
    source_artifact_ids: List[str] = Field(
        default_factory=list,
        description=(
            "IDs of artifacts this artifact was derived from or informed by. "
            "Captures the reasoning chain — e.g. a RecommendationArtifact built "
            "on top of an AnalysisArtifact lists that artifact's ID here. "
            "Multiple sources are valid: a report may synthesize several analyses."
        ),
    )
    thread_id: Optional[str] = Field(
        default=None,
        description=(
            "ID of the conversation or session that originated this work. "
            "Links the artifact back to the human request that started the chain, "
            "allowing full thread-level lineage reconstruction."
        ),
    )
    worker_id: str = Field(
        description="ID of the worker that produced this artifact.",
    )

    # -----------------------------
    # CLASSIFICATION
    # -----------------------------

    kind: ArtifactKind = Field(
        description="Artifact type — determines payload schema and eval strategy.",
    )

    # -----------------------------
    # PAYLOAD
    # -----------------------------

    payload: BasePayload = Field(
        description="Typed output produced by the worker. Schema varies by kind.",
    )

    # -----------------------------
    # QUALITY SIGNAL
    # -----------------------------

    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "Worker-reported confidence in this artifact (0–1). "
            "Optional at creation; may be populated by the worker or overwritten "
            "by the eval harness after scoring."
        ),
    )

    # -----------------------------
    # METADATA
    # -----------------------------

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp of artifact creation.",
    )

    model_config = {"extra": "forbid"}

    # -----------------------------
    # METHODS
    # -----------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize artifact to a plain dict for storage.

        Payload is serialized as a nested dict — the ArtifactStore
        is responsible for round-tripping it back to the correct type
        using the `kind` field as the discriminator.
        """
        return {
            "artifact_id": self.artifact_id,
            "task_id": self.task_id,
            "parent_task_id": self.parent_task_id,
            "source_artifact_ids": self.source_artifact_ids,
            "thread_id": self.thread_id,
            "worker_id": self.worker_id,
            "kind": self.kind.value,
            "payload": self.payload.model_dump(),
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
        }

    def summary(self) -> str:
        """
        One-line human-readable description of this artifact.
        Subclasses should override this for meaningful output.
        """
        return (
            f"[{self.kind.value}] artifact {self.artifact_id} "
            f"from worker {self.worker_id} "
            f"(task {self.task_id})"
        )
