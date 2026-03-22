from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SlackAppMentionEvent:
    """
    Typed representation of a Slack app_mention event payload.
    https://api.slack.com/events/app_mention
    """
    user: str                          # Slack user ID who mentioned the bot
    text: str                          # Full message text (includes <@BOT_ID>)
    channel: str                       # Channel ID where the mention occurred
    ts: str                            # Slack message timestamp
    team: str                          # Slack workspace/team ID
    thread_ts: Optional[str] = None    # Set if mention was inside a thread
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, event: Dict[str, Any], team: str) -> SlackAppMentionEvent:
        return cls(
            user=event["user"],
            text=event["text"],
            channel=event["channel"],
            ts=event["ts"],
            team=team,
            thread_ts=event.get("thread_ts"),
            metadata={
                "event_ts": event.get("event_ts"),
                "blocks": event.get("blocks"),
            },
        )
