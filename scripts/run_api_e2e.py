from __future__ import annotations

import json
import os
import sys
from typing import Any

import requests


BASE_URL = os.getenv("OPSIQ_API_BASE_URL", "http://127.0.0.1:5000")
TIMEOUT_SECONDS = 15


def fail(message: str) -> None:
    print(f"\n[FAIL] {message}")
    sys.exit(1)


def pretty(label: str, payload: Any) -> None:
    print(f"\n=== {label} ===")
    print(json.dumps(payload, indent=2, sort_keys=True))


def request_json(
    session: requests.Session,
    method: str,
    path: str,
    *,
    expected_status: int = 200,
    **kwargs: Any,
) -> dict[str, Any] | list[Any]:
    url = f"{BASE_URL.rstrip('/')}{path}"

    try:
        response = session.request(method=method, url=url, timeout=TIMEOUT_SECONDS, **kwargs)
    except requests.RequestException as exc:
        fail(f"Request error for {method} {url}: {exc}")

    if response.status_code != expected_status:
        body = response.text
        fail(
            f"Unexpected status for {method} {url}. "
            f"Expected {expected_status}, got {response.status_code}. "
            f"Response body: {body}"
        )

    try:
        return response.json()
    except ValueError:
        fail(f"Expected JSON response from {method} {url}, got: {response.text}")
        raise


def main() -> None:
    print(f"Running OpsIQ API end-to-end test against: {BASE_URL}")

    with requests.Session() as session:
        health = request_json(session, "GET", "/health")
        pretty("GET /health", health)

        if health.get("status") != "ok":
            fail(f"Health endpoint returned unexpected payload: {health}")

        created = request_json(session, "POST", "/tasks/sample")
        pretty("POST /tasks/sample", created)

        task_id = created.get("task_id")
        if not task_id:
            fail("Sample task response did not include task_id.")

        if created.get("status") != "created":
            fail(f"Expected created task status to be 'created', got: {created.get('status')}")

        dispatched = request_json(session, "POST", "/dispatch")
        pretty("POST /dispatch", dispatched)

        dispatched_count = dispatched.get("dispatched_count")
        if not isinstance(dispatched_count, int):
            fail(f"Dispatch response missing integer dispatched_count: {dispatched}")

        executed = request_json(session, "POST", "/execute/queued")
        pretty("POST /execute/queued", executed)

        executed_count = executed.get("executed_count")
        if not isinstance(executed_count, int):
            fail(f"Execution response missing integer executed_count: {executed}")

        final_task = request_json(session, "GET", f"/tasks/{task_id}")
        pretty(f"GET /tasks/{task_id}", final_task)

        if final_task.get("task_id") != task_id:
            fail("Fetched task_id does not match created task_id.")

        if final_task.get("status") != "completed":
            fail(f"Expected final task status to be 'completed', got: {final_task.get('status')}")

        owner_worker = final_task.get("owner_worker")
        if not owner_worker:
            fail("Expected owner_worker to be populated after dispatch/execution.")

        artifacts = final_task.get("artifacts", [])
        if not isinstance(artifacts, list) or len(artifacts) == 0:
            fail("Expected at least one artifact after execution, but none were found.")

        print("\n[PASS] OpsIQ end-to-end API test completed successfully.")
        print(f"[PASS] task_id={task_id}")
        print(f"[PASS] owner_worker={owner_worker}")
        print(f"[PASS] dispatched_count={dispatched_count}")
        print(f"[PASS] executed_count={executed_count}")
        print(f"[PASS] artifacts_count={len(artifacts)}")


if __name__ == "__main__":
    main()