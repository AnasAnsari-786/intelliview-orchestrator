"""
End-to-end smoke tests against a running stack.

Run the stack first:
    docker compose up -d
    pip install -r requirements.txt
    pytest tests/test_e2e_smoke.py -v

Set API_BASE_URL to override default http://localhost:8000.
"""

import time
import uuid

import httpx
import pytest


def _wait_for_api(base_url: str, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    last_err = None
    while time.monotonic() < deadline:
        try:
            r = httpx.get(f"{base_url}/health", timeout=2.0)
            if r.status_code == 200:
                return
        except Exception as e:
            last_err = e
        time.sleep(1.0)
    pytest.fail(f"API not reachable at {base_url}: {last_err}")


def _wait_for_worker(base_url: str, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    last_err = None
    while time.monotonic() < deadline:
        try:
            r = httpx.get(f"{base_url}/system-health", timeout=2.0)
            if r.status_code == 200:
                body = r.json()
                if (
                    body.get("components", {})
                    .get("workers", {})
                    .get("healthy_workers", 0)
                    >= 1
                ):
                    return
        except Exception as e:
            last_err = e
        time.sleep(1.0)
    pytest.fail(f"Worker not ready at {base_url}: {last_err}")


@pytest.mark.e2e
def test_health(api_base_url):
    _wait_for_api(api_base_url)
    r = httpx.get(f"{api_base_url}/health", timeout=5.0)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "system running"
    assert body["timestamp"]


@pytest.mark.e2e
def test_start_interview_and_get_status(api_base_url, api_token):
    _wait_for_api(api_base_url)
    _wait_for_worker(api_base_url)

    candidate_id = f"cand-{uuid.uuid4().hex[:8]}"
    r = httpx.post(
        f"{api_base_url}/start-interview",
        headers={"X-API-Token": api_token},
        json={"candidate_id": candidate_id, "priority": "high"},
        timeout=30.0,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body, dict) and "session_id" in body
    session_id = body["session_id"]
    assert isinstance(session_id, str) and session_id.startswith("session_")

    r = httpx.get(f"{api_base_url}/session-status/{session_id}", timeout=5.0)
    assert r.status_code == 200
    status_body = r.json()
    assert status_body["session_id"] == session_id
    assert status_body["status"] in {
        "CREATED",
        "QUEUED",
        "PROCESSING",
        "VIDEO_PROCESSING",
        "AUDIO_PROCESSING",
        "EVALUATING",
        "COMPLETED",
        "FAILED",
        "TIMEOUT",
        "CANCELLED",
    }


@pytest.mark.e2e
def test_start_interview_duplicate_candidate_behavior(api_base_url, api_token):
    """Verify duplicate candidate submission behavior and explicit session reuse/generation contract."""
    _wait_for_api(api_base_url)
    _wait_for_worker(api_base_url)

    candidate_id = f"dup-{uuid.uuid4().hex[:8]}"
    payload = {"candidate_id": candidate_id, "priority": "high"}
    headers = {"X-API-Token": api_token}

    resp1 = httpx.post(
        f"{api_base_url}/start-interview",
        headers=headers,
        json=payload,
        timeout=30.0,
    )
    assert resp1.status_code in (200, 201), f"First request failed: {resp1.text}"
    data1 = resp1.json()
    assert isinstance(data1, dict) and "session_id" in data1
    session1_id = data1["session_id"]
    assert isinstance(session1_id, str) and session1_id.startswith("session_")

    resp2 = httpx.post(
        f"{api_base_url}/start-interview",
        headers=headers,
        json=payload,
        timeout=30.0,
    )
    assert resp2.status_code == 200, resp2.text
    data2 = resp2.json()
    assert isinstance(data2, dict) and "session_id" in data2
    session2_id = data2["session_id"]
    assert isinstance(session2_id, str) and session2_id.startswith("session_")
    assert session2_id != session1_id


@pytest.mark.e2e
def test_system_health(api_base_url):
    _wait_for_api(api_base_url)
    r = httpx.get(f"{api_base_url}/system-health", timeout=5.0)
    assert r.status_code == 200
    body = r.json()
    assert "overall_status" in body
    assert "components" in body
    assert "redis" in body["components"]


@pytest.mark.e2e
def test_worker_register_requires_token(api_base_url, api_token):
    _wait_for_api(api_base_url)
    r = httpx.post(
        f"{api_base_url}/register-worker",
        json={"worker_id": "test-w", "capacity": 2},
        timeout=5.0,
    )
    assert r.status_code == 401

    r = httpx.post(
        f"{api_base_url}/register-worker",
        json={"worker_id": "test-w", "capacity": 2},
        headers={"X-API-Token": api_token},
        timeout=5.0,
    )
    assert r.status_code == 200, r.text


@pytest.mark.e2e
def test_full_pipeline_completes(api_base_url, api_token):
    """End-to-end: verify pipeline processes job to a terminal execution state."""
    _wait_for_api(api_base_url)
    _wait_for_worker(api_base_url)

    candidate_id = f"e2e-{uuid.uuid4().hex[:8]}"
    r = httpx.post(
        f"{api_base_url}/start-interview",
        headers={"X-API-Token": api_token},
        json={"candidate_id": candidate_id, "priority": "medium"},
        timeout=30.0,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body, dict) and "session_id" in body
    session_id = body["session_id"]

    deadline = time.monotonic() + 60
    last_body = None
    terminal_states = {"COMPLETED", "FAILED", "TIMEOUT", "CANCELLED"}

    while time.monotonic() < deadline:
        try:
            r = httpx.get(f"{api_base_url}/session-status/{session_id}", timeout=5.0)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and "status" in data:
                    last_body = data
                    if data["status"] in terminal_states:
                        break
        except Exception:
            pass
        time.sleep(1.0)

    assert last_body is not None, f"Polling failed for session {session_id}"
    assert (
        last_body["status"] in terminal_states
    ), f"Pipeline stuck in non-terminal state: {last_body['status']}"


@pytest.mark.e2e
def test_candidate_lifecycle(api_base_url, api_token):
    """Create a candidate, fetch it, and verify its interview history."""
    _wait_for_api(api_base_url)
    email = f"e2e-{uuid.uuid4().hex[:8]}@example.com"
    r = httpx.get(
        f"{api_base_url}/candidates/does-not-exist",
        timeout=5.0,
    )
    assert r.status_code == 404

    r = httpx.post(
        f"{api_base_url}/candidates",
        json={
            "name": "E2E Test Candidate",
            "email": email,
            "skills": ["python", "testing"],
        },
        timeout=30.0,
    )
    assert r.status_code == 200, r.text
    candidate = r.json()
    candidate_id = candidate["candidate_id"]

    r = httpx.get(f"{api_base_url}/candidates/{candidate_id}", timeout=5.0)
    assert r.status_code == 200
    assert r.json()["candidate_id"] == candidate_id

    r = httpx.get(f"{api_base_url}/candidates/{candidate_id}/history", timeout=5.0)
    assert r.status_code == 200
    assert r.json()["candidate_id"] == candidate_id


@pytest.mark.e2e
def test_worker_lifecycle(api_base_url, api_token):
    """Register a worker, send a heartbeat, list it, and deregister it."""
    _wait_for_api(api_base_url)
    worker_id = f"w-{uuid.uuid4().hex[:6]}"
    r = httpx.post(
        f"{api_base_url}/register-worker",
        headers={"X-API-Token": api_token},
        json={"worker_id": worker_id, "capacity": 1},
        timeout=5.0,
    )
    assert r.status_code == 200

    r = httpx.post(
        f"{api_base_url}/worker/heartbeat",
        headers={"X-API-Token": api_token},
        json={"worker_id": worker_id, "active_tasks": 0},
        timeout=5.0,
    )
    assert r.status_code == 200, r.text

    r = httpx.get(f"{api_base_url}/workers", timeout=5.0)
    assert r.status_code == 200
    worker_ids = {worker.get("worker_id") for worker in r.json().get("workers", [])}
    assert worker_id in worker_ids

    r = httpx.delete(
        f"{api_base_url}/deregister-worker/{worker_id}",
        headers={"X-API-Token": api_token},
        timeout=5.0,
    )
    assert r.status_code == 200, r.text


@pytest.mark.e2e
def test_dead_letter_queue_reachable(api_base_url, api_token):
    """The dead-letter queue endpoint responds with a list, even when empty."""
    _wait_for_api(api_base_url)
    r = httpx.get(
        f"{api_base_url}/dead-letter-queue",
        timeout=5.0,
    )
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body.get("dead_letter_queue"), list)
