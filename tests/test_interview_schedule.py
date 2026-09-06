"""
Unit and integration tests for Interview Scheduling and Email Notification System.
"""

import smtplib
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.db import Base, get_db
from database.models import Candidate, InterviewSchedule
from orchestrator.email_service import EmailService
from routers.schedule import create_schedule_routes

# Create clean testing app with in-memory SQLite engine
test_engine = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

test_app = FastAPI()
test_app.include_router(create_schedule_routes())


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    test_app.dependency_overrides[get_db] = override_get_db
    with TestClient(test_app) as c:
        yield c
    test_app.dependency_overrides.clear()


def test_interview_schedule_orm_model(db_session):
    """Test creating and querying InterviewSchedule model."""
    candidate = Candidate(
        candidate_id="cand_test_101",
        name="John Doe",
        email="john.doe@example.com",
    )
    db_session.add(candidate)
    db_session.commit()

    scheduled_time = datetime.now(timezone.utc) + timedelta(days=1)
    schedule = InterviewSchedule(
        id="sched_101",
        candidate_id="cand_test_101",
        interviewer_id="interviewer_alice",
        scheduled_at=scheduled_time,
        status="scheduled",
        notes="Senior Backend Role",
    )
    db_session.add(schedule)
    db_session.commit()

    fetched = db_session.query(InterviewSchedule).filter_by(id="sched_101").first()
    assert fetched is not None
    assert fetched.candidate_id == "cand_test_101"
    assert fetched.interviewer_id == "interviewer_alice"
    assert fetched.status == "scheduled"
    assert "sched_101" in repr(fetched)


def test_email_service_send_confirmation():
    """Test EmailService constructs email and handles SMTP gracefully."""
    email_svc = EmailService()

    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        success, msg = email_svc.send_interview_confirmation(
            candidate_name="Jane Doe",
            candidate_email="jane.doe@example.com",
            interview_date="August 12, 2026",
            interview_time="10:00 AM UTC",
            interviewer_name="Alice Smith",
            schedule_id="sched_202",
        )

        assert success is True
        assert "Email sent successfully" in msg
        mock_server.send_message.assert_called_once()


def test_email_service_handles_smtp_error():
    """Test EmailService catches SMTP exceptions and logs error."""
    email_svc = EmailService()

    with patch(
        "smtplib.SMTP",
        side_effect=smtplib.SMTPException("SMTP Connection Refused"),
    ):
        success, msg = email_svc.send_interview_confirmation(
            candidate_name="Jane Doe",
            candidate_email="jane.doe@example.com",
            interview_date="August 12, 2026",
            interview_time="10:00 AM UTC",
            interviewer_name="Alice Smith",
            schedule_id="sched_202",
        )

        assert success is False
        assert "Failed to send email" in msg


def test_create_schedule_api_endpoint(client, db_session):
    """Test POST /api/schedule endpoint with candidate creation and email trigger."""
    candidate = Candidate(
        candidate_id="cand_test_303",
        name="Bob Architect",
        email="bob.architect@example.com",
    )
    db_session.add(candidate)
    db_session.commit()

    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    payload = {
        "candidate_id": "cand_test_303",
        "interviewer_id": "Tech Lead Charlie",
        "scheduled_at": tomorrow,
        "notes": "System Architecture Technical Round",
        "send_email": True,
    }

    with patch(
        "orchestrator.email_service.email_service.send_interview_confirmation"
    ) as mock_send:
        mock_send.return_value = (True, "Email sent successfully")
        response = client.post("/api/schedule", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Interview scheduled successfully."
    assert data["schedule"]["candidate_id"] == "cand_test_303"
    assert data["schedule"]["candidate_name"] == "Bob Architect"
    assert data["schedule"]["interviewer_id"] == "Tech Lead Charlie"
    assert data["email_notification"]["sent"] is True


def test_create_schedule_past_date_fails(client, db_session):
    """Test that scheduling an interview in the past raises HTTP 400 error."""
    candidate = Candidate(
        candidate_id="cand_test_past",
        name="Past Candidate",
        email="past@example.com",
    )
    db_session.add(candidate)
    db_session.commit()

    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

    payload = {
        "candidate_id": "cand_test_past",
        "interviewer_id": "Interviewer X",
        "scheduled_at": yesterday,
    }

    response = client.post("/api/schedule", json=payload)
    assert response.status_code == 400
    assert "must be in the future" in response.json()["detail"]


def test_update_schedule_invalid_status_fails(client, db_session):
    """Test that updating schedule with an invalid status raises HTTP 400 error."""
    candidate = Candidate(
        candidate_id="cand_test_status",
        name="Status Candidate",
        email="status@example.com",
    )
    db_session.add(candidate)
    db_session.commit()

    future_time = datetime.now(timezone.utc) + timedelta(days=2)
    schedule = InterviewSchedule(
        id="sched_invalid_status",
        candidate_id="cand_test_status",
        interviewer_id="Lead Tester",
        scheduled_at=future_time,
        status="scheduled",
    )
    db_session.add(schedule)
    db_session.commit()

    patch_res = client.patch(
        "/api/schedule/sched_invalid_status",
        json={"status": "invalid_status_xyz"},
    )
    assert patch_res.status_code == 400
    assert "Allowed statuses are" in patch_res.json()["detail"]


def test_list_and_upcoming_schedule_api(client, db_session):
    """Test GET /api/schedule and GET /api/schedule/upcoming."""
    candidate = Candidate(
        candidate_id="cand_test_404",
        name="Alice Engineer",
        email="alice.engineer@example.com",
    )
    db_session.add(candidate)
    db_session.commit()

    future_time = datetime.now(timezone.utc) + timedelta(days=2)
    schedule = InterviewSchedule(
        id="sched_future",
        candidate_id="cand_test_404",
        interviewer_id="Manager Dave",
        scheduled_at=future_time,
        status="scheduled",
    )
    db_session.add(schedule)
    db_session.commit()

    # GET /api/schedule
    res_list = client.get("/api/schedule")
    assert res_list.status_code == 200
    schedules = res_list.json()["schedules"]
    assert len(schedules) >= 1
    assert any(s["id"] == "sched_future" for s in schedules)

    # GET /api/schedule/upcoming
    res_upcoming = client.get("/api/schedule/upcoming")
    assert res_upcoming.status_code == 200
    upcoming = res_upcoming.json()["upcoming"]
    assert len(upcoming) >= 1
    assert upcoming[0]["id"] == "sched_future"


def test_full_end_to_end_schedule_flow(client, db_session):
    """
    Final End-to-End Test Verification:
    Schedule interview for tomorrow -> Save in DB -> Send confirmation email -> Show interview on upcoming dashboard.
    """
    candidate = Candidate(
        candidate_id="cand_e2e_999",
        name="E2E Tester",
        email="e2e.tester@example.com",
    )
    db_session.add(candidate)
    db_session.commit()

    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    # 1. Schedule Interview via POST /api/schedule
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        post_res = client.post(
            "/api/schedule",
            json={
                "candidate_id": "cand_e2e_999",
                "interviewer_id": "Aditya Kanojiya",
                "scheduled_at": tomorrow,
                "notes": "Full-Stack Verification Round",
                "send_email": True,
            },
        )

    assert post_res.status_code == 201
    res_data = post_res.json()
    sched_id = res_data["schedule"]["id"]

    # 2. Verify Saved in DB
    db_entry = db_session.query(InterviewSchedule).filter_by(id=sched_id).first()
    assert db_entry is not None
    assert db_entry.candidate_id == "cand_e2e_999"
    assert db_entry.interviewer_id == "Aditya Kanojiya"
    assert db_entry.status == "scheduled"

    # 3. Verify Email Sent Notification
    assert res_data["email_notification"]["sent"] is True

    # 4. Verify Shows on Upcoming Dashboard API
    upcoming_res = client.get("/api/schedule/upcoming")
    assert upcoming_res.status_code == 200
    upcoming_list = upcoming_res.json()["upcoming"]
    assert any(s["id"] == sched_id for s in upcoming_list)
