from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    BLOCKED = "blocked"
    FAILED = "failed"


class ObservationCategory(str, Enum):
    INGESTION = "ingestion"
    CLASSIFICATION = "classification"
    PLANNING = "planning"
    EXECUTION = "execution"
    EVALUATION = "evaluation"
    QUALITY = "quality"
    SYSTEM = "system"


class NodeEventType(str, Enum):
    TASK_CREATED = "task_created"
    TASK_ROUTED = "task_routed"
    HUMAN_REVIEW_REQUIRED = "human_review_required"
    RETRY_REQUESTED = "retry_requested"
    EXECUTION_COMPLETED = "execution_completed"
    EVALUATION_FAILED = "evaluation_failed"


@dataclass
class NodeObservation:
    name: str
    value: Any
    category: ObservationCategory
    message: Optional[str] = None
    confidence: Optional[float] = None
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"confidence must be between 0.0 and 1.0, got {self.confidence}"
            )


@dataclass
class NodeEvent:
    """
    Structured event emitted by a node.
    Useful for runtime handling, notifications, or analytics.
    """
    event_type: NodeEventType
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NodeResult:
    """
    Standard return type for all kernel-managed nodes.

    A node should never mutate kernel state directly.
    Instead, it returns a state_patch plus artifacts / observations / events.
    The kernel runtime is responsible for applying the patch.
    """
    status: NodeStatus
    state_patch: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Any] = field(default_factory=list)
    observations: List[NodeObservation] = field(default_factory=list)
    events: List[NodeEvent] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status in {
            NodeStatus.SUCCESS,
            NodeStatus.PARTIAL_SUCCESS,
        }

    @classmethod
    def success(
        cls,
        *,
        state_patch: Optional[Dict[str, Any]] = None,
        artifacts: Optional[List[Any]] = None,
        observations: Optional[List[NodeObservation]] = None,
        events: Optional[List[NodeEvent]] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> "NodeResult":
        return cls(
            status=NodeStatus.SUCCESS,
            state_patch=state_patch or {},
            artifacts=artifacts or [],
            observations=observations or [],
            events=events or [],
            metrics=metrics or {},
            errors=[],
        )

    @classmethod
    def partial_success(
        cls,
        *,
        state_patch: Optional[Dict[str, Any]] = None,
        artifacts: Optional[List[Any]] = None,
        observations: Optional[List[NodeObservation]] = None,
        events: Optional[List[NodeEvent]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None,
    ) -> "NodeResult":
        return cls(
            status=NodeStatus.PARTIAL_SUCCESS,
            state_patch=state_patch or {},
            artifacts=artifacts or [],
            observations=observations or [],
            events=events or [],
            metrics=metrics or {},
            errors=errors or [],
        )

    @classmethod
    def blocked(
        cls,
        *,
        errors: Optional[List[str]] = None,
        observations: Optional[List[NodeObservation]] = None,
        events: Optional[List[NodeEvent]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        state_patch: Optional[Dict[str, Any]] = None,
        artifacts: Optional[List[Any]] = None,
    ) -> "NodeResult":
        return cls(
            status=NodeStatus.BLOCKED,
            state_patch=state_patch or {},
            artifacts=artifacts or [],
            observations=observations or [],
            events=events or [],
            metrics=metrics or {},
            errors=errors or [],
        )

    @classmethod
    def failed(
        cls,
        *,
        errors: Optional[List[str]] = None,
        observations: Optional[List[NodeObservation]] = None,
        events: Optional[List[NodeEvent]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        state_patch: Optional[Dict[str, Any]] = None,
        artifacts: Optional[List[Any]] = None,
    ) -> "NodeResult":
        return cls(
            status=NodeStatus.FAILED,
            state_patch=state_patch or {},
            artifacts=artifacts or [],
            observations=observations or [],
            events=events or [],
            metrics=metrics or {},
            errors=errors or [],
        )