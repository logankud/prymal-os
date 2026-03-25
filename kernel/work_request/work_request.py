"""
WorkRequest — the formal unit of work in OpsIQ.

Represents one complete request lifecycle: from the raw user signal through
parsed intents, commissioned tasks, produced artifacts, and final synthesis.

All objects spawned from a single user signal belong to one WorkRequest.
This is the thread that connects intent → tasks → artifacts → response.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class WorkRequestStatus(str, Enum):
    PENDING            = "pending"             # intents parsed, tasks not yet created
    IN_PROGRESS        = "in_progress"         # one or more tasks running
    READY_FOR_SYNTHESIS = "ready_for_synthesis" # all tasks terminal, synthesis not yet run
    SYNTHESIZING       = "synthesizing"        # synthesis node running
    COMPLETE           = "complete"            # synthesis done, response delivered
    FAILED             = "failed"              # unrecoverable error


@dataclass
class WorkRequest:
    """
    A single unit of work from user signal to synthesized response.

    Owns the full lineage:
      IngressEvent → ParsedIntents → Tasks → Artifacts → SynthesisResult
    """

    # ── Identity ──────────────────────────────────────────────────────────
    work_request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: WorkRequestStatus = field(default=WorkRequestStatus.PENDING)

    # ── Source signal ─────────────────────────────────────────────────────
    source: str = ""                      # "slack", "ui", "api"
    raw_text: str = ""                    # original user input
    thread_id: Optional[str] = None       # delivery target (e.g. slack:C123:ts)
    user_id: Optional[str] = None

    # ── Parsed intents (set by IngressNode) ───────────────────────────────
    intents: List[Dict[str, Any]] = field(default_factory=list)

    # ── Task IDs commissioned from this request ────────────────────────────
    task_ids: List[str] = field(default_factory=list)

    # ── Artifact IDs produced by workers ──────────────────────────────────
    artifact_ids: List[str] = field(default_factory=list)

    # ── Synthesis output (set by SynthesisNode) ───────────────────────────
    synthesis_result: Optional[Dict[str, Any]] = None

    # ── Prior context (future: relevant artifacts from past requests) ──────
    prior_context_ids: List[str] = field(default_factory=list)

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # ── Methods ───────────────────────────────────────────────────────────

    def add_task(self, task_id: str) -> None:
        self.task_ids.append(task_id)
        self.updated_at = datetime.utcnow()
        if self.status == WorkRequestStatus.PENDING:
            self.status = WorkRequestStatus.IN_PROGRESS

    def add_artifact(self, artifact_id: str) -> None:
        self.artifact_ids.append(artifact_id)
        self.updated_at = datetime.utcnow()

    def mark_synthesizing(self) -> None:
        self.status = WorkRequestStatus.SYNTHESIZING
        self.updated_at = datetime.utcnow()

    def mark_complete(self, synthesis_result: Dict[str, Any]) -> None:
        self.synthesis_result = synthesis_result
        self.status = WorkRequestStatus.COMPLETE
        self.updated_at = datetime.utcnow()

    def mark_failed(self) -> None:
        self.status = WorkRequestStatus.FAILED
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "work_request_id": self.work_request_id,
            "status": self.status.value,
            "source": self.source,
            "raw_text": self.raw_text,
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "intents": self.intents,
            "task_ids": self.task_ids,
            "artifact_ids": self.artifact_ids,
            "synthesis_result": self.synthesis_result,
            "prior_context_ids": self.prior_context_ids,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
