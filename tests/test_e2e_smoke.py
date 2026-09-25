"""
End-to-end smoke tests against a running stack.
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
                if body.get("components", {}).get("workers", {}).get("healthy_workers", 0) >= 1:
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
        "CREATED", "QUEUED", "PROCESSING", "VIDEO_PROCESSING", 
        "AUDIO_PROCESSING", "EVALUATING", "COMPLETED", "FAILED", "TIMEOUT", "CANCELLED"
    }

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
    assert last_body["status"] in terminal_states

@pytest.mark.e2e
def test_dead_letter_queue_reachable(api_base_url, api_token):
    _wait_for_api(api_base_url)
    r = httpx.get(
        f"{api_base_url}/dead-letter-queue",
        timeout=5.0,
    )
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body.get("dead_letter_queue"), list)
