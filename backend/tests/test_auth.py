"""
CareerCompass – API tests for authentication endpoints.
Covers H1 (password hashing), H2 (privilege escalation prevention),
and basic RBAC on registration and the new admin-only user creation.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient

from tests.conftest import _seed_test_data


# ── H1: password hashing works ──────────────────────────────────────────────

def test_hash_password_roundtrip():
    """H1: passlib[bcrypt] + pinned bcrypt must hash and verify without error."""
    from app.core.security import hash_password, verify_password
    h = hash_password("password123")
    assert verify_password("password123", h)
    assert not verify_password("wrong", h)


# ── H2: public registration privilege escalation ────────────────────────────

@pytest.mark.asyncio
async def test_register_with_role_admin_rejected(client: AsyncClient, db_session):
    """H2: Sending role=admin in the registration body must return 422."""
    await _seed_test_data(db_session)
    resp = await client.post("/api/v1/auth/register", json={
        "email": "hacker@example.com",
        "password": "password123",
        "full_name": "Hacker",
        "role": "admin",
    })
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_register_with_role_counsellor_rejected(client: AsyncClient, db_session):
    """H2: Sending role=counsellor in the registration body must return 422."""
    await _seed_test_data(db_session)
    resp = await client.post("/api/v1/auth/register", json={
        "email": "fake@example.com",
        "password": "password123",
        "full_name": "Fake",
        "role": "counsellor",
    })
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_register_normal_creates_student(client: AsyncClient, db_session):
    """H2: Normal registration always creates a student, ignores any role field."""
    await _seed_test_data(db_session)
    resp = await client.post("/api/v1/auth/register", json={
        "email": "newstudent@example.com",
        "password": "password123",
        "full_name": "New Student",
    })
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["role"] == "student"
    assert data["email"] == "newstudent@example.com"


# ── H2: admin creates staff accounts ────────────────────────────────────────

async def _register_and_login(client: AsyncClient, email: str, password: str, full_name: str) -> str:
    """Helper: register a student and return access token."""
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": full_name,
    })
    login_resp = await client.post("/api/v1/auth/login", data={
        "username": email,
        "password": password,
    })
    return login_resp.json()["access_token"]


async def _create_admin_token(client: AsyncClient, db_session) -> str:
    """Helper: create an admin directly via ORM and return token."""
    from app.models.models import User
    from app.core.security import hash_password, create_access_token
    admin = User(
        email="admin@test.com",
        hashed_password=hash_password("Admin@1234"),
        full_name="Test Admin",
        role="admin",
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return create_access_token({"sub": admin.id, "role": "admin"})


@pytest.mark.asyncio
async def test_admin_create_user_anonymous_401(client: AsyncClient, db_session):
    """H2: Unauthenticated POST /admin/users returns 401."""
    await _seed_test_data(db_session)
    resp = await client.post("/api/v1/admin/users", json={
        "email": "c@test.com",
        "password": "password123",
        "full_name": "Counsellor",
        "role": "counsellor",
    })
    assert resp.status_code == 401, resp.text


@pytest.mark.asyncio
async def test_admin_create_user_student_403(client: AsyncClient, db_session):
    """H2: Student calling POST /admin/users gets 403."""
    await _seed_test_data(db_session)
    token = await _register_and_login(client, "stu@test.com", "password123", "Student")
    resp = await client.post(
        "/api/v1/admin/users",
        json={"email": "c@test.com", "password": "password123", "full_name": "C", "role": "counsellor"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_admin_create_counsellor_201(client: AsyncClient, db_session):
    """H2: Admin can create a counsellor via POST /admin/users."""
    await _seed_test_data(db_session)
    admin_token = await _create_admin_token(client, db_session)
    resp = await client.post(
        "/api/v1/admin/users",
        json={
            "email": "counsellor@test.com",
            "password": "Counsellor@1234",
            "full_name": "Test Counsellor",
            "role": "counsellor",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["role"] == "counsellor"
    assert data["email"] == "counsellor@test.com"


@pytest.mark.asyncio
async def test_admin_cannot_create_student_via_admin_users(client: AsyncClient, db_session):
    """H2: POST /admin/users with role=student must return 422 (student is for /register)."""
    await _seed_test_data(db_session)
    admin_token = await _create_admin_token(client, db_session)
    resp = await client.post(
        "/api/v1/admin/users",
        json={
            "email": "s@test.com",
            "password": "password123",
            "full_name": "S",
            "role": "student",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_admin_created_counsellor_can_login(client: AsyncClient, db_session):
    """H2: Counsellor created by admin can log in and get a valid token."""
    await _seed_test_data(db_session)
    admin_token = await _create_admin_token(client, db_session)
    await client.post(
        "/api/v1/admin/users",
        json={
            "email": "newc@test.com",
            "password": "NewPass@1234",
            "full_name": "New Counsellor",
            "role": "counsellor",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    login_resp = await client.post("/api/v1/auth/login", data={
        "username": "newc@test.com",
        "password": "NewPass@1234",
    })
    assert login_resp.status_code == 200, login_resp.text
    assert "access_token" in login_resp.json()


@pytest.mark.asyncio
async def test_admin_create_user_duplicate_email_400(client: AsyncClient, db_session):
    """H2: Creating a user with a duplicate email returns 400."""
    await _seed_test_data(db_session)
    admin_token = await _create_admin_token(client, db_session)
    payload = {
        "email": "dup@test.com",
        "password": "password123",
        "full_name": "Dup",
        "role": "counsellor",
    }
    await client.post("/api/v1/admin/users", json=payload,
                      headers={"Authorization": f"Bearer {admin_token}"})
    resp = await client.post("/api/v1/admin/users", json=payload,
                             headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 400, resp.text
