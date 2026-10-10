import pytest
from pydantic import ValidationError

from routers.candidates import (
    BulkCandidateItem,
    CreateCandidateRequest,
    UpdateCandidateRequest,
    VerifyCandidateRequest,
)


@pytest.mark.parametrize(
    "model, payload",
    [
        (
            CreateCandidateRequest,
            {"name": "Test Candidate", "email": "invalid-email"},
        ),
        (
            UpdateCandidateRequest,
            {"name": "Test Candidate", "email": "user@"},
        ),
        (
            BulkCandidateItem,
            {"name": "Test Candidate", "email": "@gmail.com"},
        ),
        (
            VerifyCandidateRequest,
            {"email": "abc", "token": "123456"},
        ),
    ],
)
def test_candidate_request_rejects_invalid_email(model, payload):
    with pytest.raises(ValidationError):
        model(**payload)


@pytest.mark.parametrize(
    "model, payload",
    [
        (
            CreateCandidateRequest,
            {"name": "Test Candidate", "email": "test@example.com"},
        ),
        (
            UpdateCandidateRequest,
            {"name": "Test Candidate", "email": "test@example.com"},
        ),
        (
            BulkCandidateItem,
            {"name": "Test Candidate", "email": "test@example.com"},
        ),
        (
            VerifyCandidateRequest,
            {"email": "test@example.com", "token": "123456"},
        ),
    ],
)
def test_candidate_request_accepts_valid_email(model, payload):
    instance = model(**payload)
    assert str(instance.email) == "test@example.com"
