from __future__ import annotations

import re
from typing import Any, Dict

from integrations.base import BaseIntegration, IntegrationSignal
from integrations.slack.schema import SlackAppMentionEvent


class SlackAdapter(BaseIntegration):
    """
    Normalizes Slack app_mention events into canonical IntegrationSignals.

    Strips the bot mention tag from the message text so downstream
    processing only sees the user's actual intent.

    Example:
        "<@U123BOT> analyze Q1 revenue" → "analyze Q1 revenue"
    """

    source_name = "slack"

    def to_signal(self, raw_payload: Dict[str, Any]) -> IntegrationSignal:
        event_data = raw_payload.get("event", {})
        team = raw_payload.get("team_id", "unknown")

        mention = SlackAppMentionEvent.from_payload(event_data, team)
        clean_text = self._strip_bot_mention(mention.text)

        if not clean_text:
            raise ValueError("Slack mention contained no actionable text after stripping bot tag.")

        return IntegrationSignal(
            source=self.source_name,
            text=clean_text,
            user_id=mention.user,
            channel_id=mention.channel,
            thread_id=mention.thread_ts,
            metadata={
                "slack_ts": mention.ts,
                "slack_team": mention.team,
            },
        )

    def _strip_bot_mention(self, text: str) -> str:
        """Remove <@BOTID> mention tags and normalize whitespace."""
        return re.sub(r"<@[A-Z0-9]+>", "", text).strip()
