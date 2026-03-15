"""Smoke test the running OpsIQ FastAPI app."""

from __future__ import annotations

import os
from typing import Any

import pytest
import requests


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")


def request_or_die(
    session: requests.Session,
    method: str,
    path: str,
    *,
    expected_status: int = 200,
    **kwargs: Any,
) -> requests.Response:
    url = f"{BASE_URL.rstrip('/')}{path}"

    try:
        response = session.request(method=method, url=url, timeout=15, **kwargs)
    except requests.RequestException as exc:
        pytest.fail(f"Request failed for {method} {url}: {exc}")

    assert response.status_code == expected_status, (
        f"Unexpected status for {method} {url}. "
        f"Expected {expected_status}, got {response.status_code}. "
        f"Response body: {response.text}"
    )

    return response


@pytest.fixture
def session() -> requests.Session:
    with requests.Session() as s:
        yield s


def test_api_health(session: requests.Session) -> None:
    response = request_or_die(session, "GET", "/health")
    payload = response.json()

    assert payload["status"] == "ok"


def test_api_task_lifecycle_sample_and_custom(session: requests.Session) -> None:

    # ----------- Create sample task
    response = request_or_die(session, "POST", "/tasks/sample")
    sample_task = response.json()
    sample_task_id = sample_task["task_id"]

    # ----------- Fetch sample task by id
    response = request_or_die(session, "GET", f"/tasks/{sample_task_id}")
    fetched_sample_before = response.json()

    assert fetched_sample_before["task_id"] == sample_task_id
    assert fetched_sample_before["status"].lower() == "created"

    # ----------- List tasks and confirm sample task exists
    response = request_or_die(session, "GET", "/tasks")
    tasks_before_dispatch = response.json()

    assert any(task["task_id"] == sample_task_id for task in tasks_before_dispatch)

    # ----------- Dispatch created tasks
    response = request_or_die(session, "POST", "/dispatch")
    dispatch_result_1 = response.json()

    assert "dispatched_count" in dispatch_result_1
    assert isinstance(dispatch_result_1["dispatched_count"], int)
    assert dispatch_result_1["dispatched_count"] >= 1

    # ----------- Verify sample task moved to QUEUED
    response = request_or_die(session, "GET", f"/tasks/{sample_task_id}")
    fetched_sample_after = response.json()

    assert fetched_sample_after["status"].lower() == "queued"
    assert fetched_sample_after["owner_worker"] == "coo_worker"

    # ----------- Create a custom task
    custom_payload = {
        "action": "investigate",
        "subject": "ad campaign performance dip",
        "outcome": "identify likely root causes and next actions",
        "domain": "marketing",
        "created_by": "api_smoke_test",
        "expected_outputs": [
            "root cause summary",
            "recommended next steps",
        ],
    }

    response = request_or_die(
        session,
        "POST",
        "/tasks",
        json=custom_payload,
    )
    custom_task = response.json()

    custom_task_id = custom_task["task_id"]
    assert custom_task["status"].lower() == "created"
    assert custom_task["created_by"] == "api_smoke_test"
    assert custom_task["owner_worker"] is None

    # ----------- Verify custom task exists before dispatch
    response = request_or_die(session, "GET", f"/tasks/{custom_task_id}")
    fetched_custom_before = response.json()

    assert fetched_custom_before["task_id"] == custom_task_id
    assert fetched_custom_before["domain"] == "marketing"
    assert fetched_custom_before["status"].lower() == "created"

    # ----------- Dispatch again
    response = request_or_die(session, "POST", "/dispatch")
    dispatch_result_2 = response.json()

    assert "dispatched_count" in dispatch_result_2
    assert isinstance(dispatch_result_2["dispatched_count"], int)
    assert dispatch_result_2["dispatched_count"] >= 1

    # ----------- Verify custom task moved to QUEUED and was routed correctly
    response = request_or_die(session, "GET", f"/tasks/{custom_task_id}")
    fetched_custom_after = response.json()

    assert fetched_custom_after["status"].lower() == "queued"
    assert fetched_custom_after["owner_worker"] == "cmo_worker"

    # ----------- Final list validation
    response = request_or_die(session, "GET", "/tasks")
    final_tasks = response.json()

    final_ids = {task["task_id"] for task in final_tasks}
    assert sample_task_id in final_ids
    assert custom_task_id in final_ids