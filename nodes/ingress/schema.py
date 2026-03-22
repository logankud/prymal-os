from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

from signatures.ingress.types import ParsedIntent


class IngressEventType(str, Enum):
    USER_TEXT = "user_text"
    VOICE_TRANSCRIPT = "voice_transcript"
    API_EVENT = "api_event"
    SYSTEM_EVENT = "system_event"


@dataclass
class IngressEvent:
    """
    Canonical external signal entering OpsIQ.

    For v0, ingress is text-first. voice_transcript is structurally
    identical — the transcription step happens upstream of this node.
    """

    event_type: IngressEventType
    text: str
    source: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.event_type, IngressEventType):
            try:
                self.event_type = IngressEventType(self.event_type)
            except ValueError as exc:
                raise ValueError(f"Invalid event_type: {self.event_type}") from exc

        if not isinstance(self.text, str):
            raise TypeError("IngressEvent.text must be a string.")

        if not self.text.strip():
            raise ValueError("IngressEvent.text cannot be empty.")


@dataclass
class IngressStatePatch:
    """
    Typed partial state update returned by the ingress node.

    Contains all structured intents extracted from the raw input,
    ready for downstream task creation and routing.
    """

    input_text: str
    event_type: str
    intents: List[ParsedIntent]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_text": self.input_text,
            "event_type": self.event_type,
            "intents": [intent.model_dump() for intent in self.intents],
        }
