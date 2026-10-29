"""
CareerCompass – API tests for the assessment endpoints (H3).
Confirms that POST /assessment/start and POST /assessment/progress
no longer raise MissingGreenlet 500 errors.
"""
import pytest
from httpx import AsyncClient

from tests.conftest import _seed_test_data
from app.core.security import hash_password, create_access_token


async def _create_student_token(client: AsyncClient, db_session, email: str = "stu@test.com") -> str:
    """Helper: register a student and return its JWT."""
    resp = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "password123",
        "full_name": "Test Student",
    })
    assert resp.status_code == 201, resp.text
    login = await client.post("/api/v1/auth/login", data={
        "username": email,
        "password": "password123",
    })
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


@pytest.mark.asyncio
async def test_start_assessment_201_no_500(client: AsyncClient, db_session):
    """H3: POST /assessment/start returns 201 and status=='in_progress', not 500."""
    await _seed_test_data(db_session)
    token = await _create_student_token(client, db_session)

    resp = await client.post(
        "/api/v1/assessment/start",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "in_progress"
    assert data["riasec_score"] is None  # no score yet


@pytest.mark.asyncio
async def test_start_assessment_is_idempotent(client: AsyncClient, db_session):
    """H3: Calling /start twice returns the same assessment."""
    await _seed_test_data(db_session)
    token = await _create_student_token(client, db_session)

    resp1 = await client.post(
        "/api/v1/assessment/start",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp2 = await client.post(
        "/api/v1/assessment/start",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.json()["id"] == resp2.json()["id"]


@pytest.mark.asyncio
async def test_save_progress_200_no_500(client: AsyncClient, db_session):
    """H3: POST /assessment/progress returns 200 and not 500."""
    await _seed_test_data(db_session)
    token = await _create_student_token(client, db_session)

    # Start first
    await client.post(
        "/api/v1/assessment/start",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Save 3 answers (using questions from seed data)
    answers = [
        {"question_id": f"q-test-{i:03d}", "answer": 3}
        for i in range(1, 4)
    ]
    resp = await client.post(
        "/api/v1/assessment/progress",
        json={"answers": answers},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "in_progress"
    assert data["riasec_score"] is None


@pytest.mark.asyncio
async def test_get_progress_shows_answered_count(client: AsyncClient, db_session):
    """H3: GET /assessment/progress shows the correct answered count after save."""
    await _seed_test_data(db_session)
    token = await _create_student_token(client, db_session)

    await client.post(
        "/api/v1/assessment/start",
        headers={"Authorization": f"Bearer {token}"},
    )

    answers = [
        {"question_id": f"q-test-{i:03d}", "answer": 3}
        for i in range(1, 4)
    ]
    await client.post(
        "/api/v1/assessment/progress",
        json={"answers": answers},
        headers={"Authorization": f"Bearer {token}"},
    )

    prog_resp = await client.get(
        "/api/v1/assessment/progress",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert prog_resp.status_code == 200, prog_resp.text
    prog = prog_resp.json()
    assert prog["answered"] == 3
    assert prog["total"] == 48
