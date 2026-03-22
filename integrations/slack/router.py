from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from api.dependencies import get_task_store
from integrations.signal_translator import to_ingress_event
from integrations.slack.adapter import SlackAdapter
from kernel.ingress_pipeline import run_ingress_pipeline
from kernel.tasks.task_store import TaskStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations/slack", tags=["integrations"])

_adapter = SlackAdapter()


def _verify_slack_signature(request_body: bytes, timestamp: str, signature: str) -> bool:
    """
    Verify Slack request signature using HMAC-SHA256.
    https://api.slack.com/authentication/verifying-requests-from-slack
    """
    signing_secret = os.environ.get("SLACK_SIGNING_SECRET", "")
    if not signing_secret:
        logger.warning("SLACK_SIGNING_SECRET not set — skipping signature verification.")
        return True

    try:
        if abs(time.time() - float(timestamp)) > 300:
            return False
    except (ValueError, TypeError):
        return False

    sig_basestring = f"v0:{timestamp}:{request_body.decode('utf-8')}"
    expected = "v0=" + hmac.new(
        signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


@router.post("/events")
async def slack_events(
    request: Request,
    task_store: TaskStore = Depends(get_task_store),
) -> JSONResponse:
    """
    Slack Events API endpoint.

    Handles:
    - url_verification: Slack challenge handshake (required during bot setup)
    - app_mention: Translate event → IngressEvent → ingress pipeline
    """
    body_bytes = await request.body()
    payload: Dict[str, Any] = await request.json()

    # ── Slack URL verification challenge ──────────────────────────────
    if payload.get("type") == "url_verification":
        return JSONResponse({"challenge": payload["challenge"]})

    # ── Signature verification ────────────────────────────────────────
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")

    if not _verify_slack_signature(body_bytes, timestamp, signature):
        raise HTTPException(status_code=403, detail="Invalid Slack signature.")

    # ── Only handle app_mention events ───────────────────────────────
    event = payload.get("event", {})
    if event.get("type") != "app_mention":
        return JSONResponse({"ok": True})

    # ── Translate Slack payload → IntegrationSignal → IngressEvent ────
    try:
        signal = _adapter.to_signal(payload)
    except ValueError as exc:
        logger.warning("Slack signal normalization failed: %s", exc)
        return JSONResponse({"ok": True})

    ingress_event = to_ingress_event(signal)

    # ── Hand off to ingress pipeline ──────────────────────────────────
    try:
        tasks = await run_ingress_pipeline(
            event=ingress_event,
            task_store=task_store,
            created_by=f"slack:{signal.user_id}",
        )
        logger.info("%d task(s) created from Slack mention", len(tasks))
    except Exception as exc:
        logger.error("Ingress pipeline failed for Slack event: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to process Slack event.")

    return JSONResponse({"ok": True, "task_ids": [t.task_id for t in tasks]})
