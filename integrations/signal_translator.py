from __future__ import annotations

from integrations.base import IntegrationSignal
from nodes.ingress.schema import IngressEvent, IngressEventType


def to_ingress_event(signal: IntegrationSignal) -> IngressEvent:
    """
    Translate a canonical IntegrationSignal into a kernel IngressEvent.

    This is the single seam between the integration layer and the kernel.
    If IngressEvent evolves, only this function needs to change.
    """
    return IngressEvent(
        event_type=IngressEventType.API_EVENT,
        text=signal.text,
        source=signal.source,
        metadata={
            "user_id": signal.user_id,
            "channel_id": signal.channel_id,
            "thread_id": signal.thread_id,
            **signal.metadata,
        },
    )
