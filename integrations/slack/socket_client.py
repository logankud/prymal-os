from __future__ import annotations

import logging
import os
import re
import threading
from typing import Any, Dict

import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

logger = logging.getLogger(__name__)

MENTION_RE = re.compile(r"<@[^>]+>\s*")


def _normalize_text(text: str) -> str:
    return MENTION_RE.sub("", (text or "").strip()).strip()


def _submit_to_opsiq(
    base_url: str,
    text: str,
    user_id: str,
    channel_id: str,
    thread_id: str,
) -> list[Dict[str, Any]]:
    """POST intent text to OpsIQ's intake endpoint and return created tasks."""
    r = requests.post(
        f"{base_url}/intake",
        json={
            "text": text,
            "source": "slack",
            "user_id": user_id,
            "channel_id": channel_id,
            "thread_id": thread_id,
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("tasks", [])


def build_slack_app() -> App:
    """
    Construct and return the Slack Bolt app with all event handlers registered.
    Called once during FastAPI lifespan startup.
    """
    bot_token = os.environ.get("SLACK_BOT_TOKEN", "")
    opsiq_url = os.environ.get("OPSIQ_URL", "http://localhost:8000")

    bolt_app = App(token=bot_token)

    @bolt_app.middleware
    def log_requests(body, next):
        logger.debug("Slack event: %s / %s", body.get("type"), body.get("event", {}).get("type"))
        return next()

    @bolt_app.event("app_mention")
    def handle_app_mention(body, say):
        event = body.get("event", {})
        text = _normalize_text(event.get("text", ""))
        thread_ts = event.get("thread_ts") or event.get("ts")
        channel = event.get("channel")
        user = event.get("user")

        if not text:
            say("What would you like me to work on?", thread_ts=thread_ts)
            return

        try:
            tasks = _submit_to_opsiq(
                base_url=opsiq_url,
                text=text,
                user_id=user,
                channel_id=channel,
                thread_id=f"slack:{channel}:{thread_ts}",
            )
            if tasks:
                task_lines = "\n".join(f"• *{t['action']}* {t['subject']}" for t in tasks)
                say(f"Got it. Queued {len(tasks)} task(s):\n{task_lines}", thread_ts=thread_ts)
            else:
                say("Received, but no tasks were extracted.", thread_ts=thread_ts)
        except Exception as exc:
            logger.error("Failed to submit to OpsIQ intake: %s", exc)
            say("Something went wrong — please try again.", thread_ts=thread_ts)

    @bolt_app.event("message")
    def handle_message(body, logger):
        """Acknowledge non-mention messages without responding."""
        event = body.get("event", {}) or {}
        if event.get("subtype") in {"bot_message", "message_changed", "message_deleted"}:
            return
        if event.get("bot_id"):
            return

    return bolt_app


def start_socket_client() -> SocketModeHandler | None:
    """
    Start the Slack Socket Mode client in a background daemon thread.

    Returns the handler if successfully started, None if env vars are missing.
    Called during FastAPI lifespan startup.
    """
    app_token = os.environ.get("SLACK_APP_TOKEN", "")
    bot_token = os.environ.get("SLACK_BOT_TOKEN", "")

    if not app_token or not bot_token:
        logger.warning(
            "SLACK_APP_TOKEN or SLACK_BOT_TOKEN not set — Slack socket client will not start."
        )
        return None

    bolt_app = build_slack_app()
    handler = SocketModeHandler(bolt_app, app_token)

    thread = threading.Thread(target=handler.start, daemon=True, name="slack-socket-client")
    thread.start()

    logger.info("Slack socket client started in background thread.")
    return handler
