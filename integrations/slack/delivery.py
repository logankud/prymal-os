"""
Slack delivery — posts synthesized responses back to the originating thread.

The primary delivery path is synthesis-based: after all tasks in a WorkRequest
complete, the SynthesisNode produces a SynthesisResult which is formatted and
posted to Slack. This replaces the older per-task artifact delivery.
"""

from __future__ import annotations

import logging
import os
from typing import Callable

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from kernel.work_request.work_request import WorkRequest
from signatures.synthesis.types import SynthesisResult

logger = logging.getLogger(__name__)

_MAX_SECTION_CHARS = 2800
_CONFIDENCE_THRESHOLD = 0.5


def _format_synthesis(work_request: WorkRequest, synthesis: SynthesisResult) -> str:
    """Format a SynthesisResult as a Slack message."""
    confidence_note = ""
    if synthesis.confidence < _CONFIDENCE_THRESHOLD:
        confidence_note = (
            f"\n⚠️ _Low confidence ({synthesis.confidence:.0%}) — "
            "findings may be incomplete or speculative._"
        )

    parts = [f"✅ *{synthesis.title}*{confidence_note}"]
    parts.append(synthesis.executive_summary)

    for section in synthesis.sections:
        body = section.content
        if len(body) > _MAX_SECTION_CHARS:
            body = body[:_MAX_SECTION_CHARS] + "…"
        parts.append(f"*{section.title}*\n{body}")

    if synthesis.next_steps:
        steps = "\n".join(f"• {s}" for s in synthesis.next_steps)
        parts.append(f"*Recommended next steps*\n{steps}")

    if synthesis.open_questions:
        questions = "\n".join(f"• {q}" for q in synthesis.open_questions)
        parts.append(f"*Open questions*\n{questions}")

    return "\n\n".join(parts)


def make_synthesis_delivery_callback(
    bot_token: str,
) -> Callable[[WorkRequest, SynthesisResult], None]:
    """
    Returns a delivery callback that posts a SynthesisResult to the originating Slack thread.

    Called by the execution loop after synthesis completes.
    Only fires for WorkRequests with a thread_id in the format "slack:{channel}:{thread_ts}".
    """
    if not bot_token:
        logger.warning("No SLACK_BOT_TOKEN — Slack synthesis delivery disabled.")
        return lambda wr, synthesis: None

    client = WebClient(token=bot_token)

    def deliver(work_request: WorkRequest, synthesis: SynthesisResult) -> None:
        thread_id = work_request.thread_id or ""
        if not thread_id.startswith("slack:"):
            return

        try:
            _, channel, thread_ts = thread_id.split(":", 2)
        except ValueError:
            logger.warning("Malformed slack thread_id: %s", thread_id)
            return

        try:
            message = _format_synthesis(work_request, synthesis)
            client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=message,
                mrkdwn=True,
            )
            logger.info(
                "Delivered synthesis for WorkRequest %s to %s",
                work_request.work_request_id,
                thread_id,
            )
        except SlackApiError as exc:
            logger.error(
                "Slack delivery failed for WorkRequest %s: %s",
                work_request.work_request_id,
                exc,
            )

    return deliver


def make_slack_delivery_callback(bot_token: str):
    """Deprecated: per-task delivery. Use make_synthesis_delivery_callback instead."""
    logger.warning(
        "make_slack_delivery_callback is deprecated — use make_synthesis_delivery_callback."
    )
    return lambda task: None
