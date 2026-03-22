from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class IntegrationSignal:
    """
    Canonical intermediate type returned by all integrations.

    This is the integration layer's output contract — decoupled from any
    kernel type. If IngressEvent or the kernel ingress schema changes,
    only the translator (signal_translator.py) needs to be updated,
    not every integration.
    """
    source: str                        # e.g. "slack", "email", "webhook"
    text: str                          # the user's intent as plain text
    user_id: Optional[str] = None      # external user identifier
    channel_id: Optional[str] = None   # channel / thread / room
    thread_id: Optional[str] = None    # thread context if applicable
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseIntegration(ABC):
    """
    Contract for all external system integrations.

    Each integration is responsible for:
    - Receiving a raw external payload
    - Normalizing it into a canonical IntegrationSignal

    The kernel and ingress layer are fully decoupled from this output.
    Conversion to kernel types (IngressEvent) happens in signal_translator.py.
    """

    source_name: str  # e.g. "slack", "email", "webhook"

    @abstractmethod
    def to_signal(self, raw_payload: Dict[str, Any]) -> IntegrationSignal:
        """
        Normalize a raw external payload into a canonical IntegrationSignal.
        Raise ValueError if the payload cannot be converted.
        """
        ...
