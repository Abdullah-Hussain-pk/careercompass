"""
CareerCompass – pytest configuration and shared fixtures.
Uses SQLite in-memory for fast tests (no Docker required).
"""
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.core.database import Base, get_db

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a fresh DB schema and session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """FastAPI TestClient with DB override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Helper: seed minimal data ──────────────────────────────────────────────

async def _seed_test_data(db: AsyncSession):
    """Seed minimal data for tests: settings, degrees, skills, careers, questions."""
    from app.models.models import Setting, Degree, Skill, Career, RIASECQuestion

    # Settings
    for key, value in [("w1", "0.5"), ("w2", "0.3"), ("w3", "0.2")]:
        db.add(Setting(key=key, value=value))

    # Degree
    deg = Degree(id="deg-test", name="BS Computer Science", short_name="BSCS")
    db.add(deg)

    # Skills
    for sk_id, name in [("sk-python", "Python"), ("sk-sql", "SQL"), ("sk-ml", "Machine Learning"),
                         ("sk-js", "JavaScript"), ("sk-cloud", "Cloud Computing"),
                         ("sk-linux", "Linux"), ("sk-docker", "Docker"),
                         ("sk-net", "Networking"), ("sk-sec", "Cybersecurity"), ("sk-api", "API Design")]:
        db.add(Skill(id=sk_id, name=name))

    # Career
    from app.models.models import CareerSkill, CareerDegree
    career = Career(
        id="car-test-se",
        title="Software Engineer",
        description="Test career",
        r_score=30, i_score=80, a_score=40, s_score=40, e_score=60, c_score=60,
        source="test",
    )
    db.add(career)
    await db.flush()
    db.add(CareerSkill(career_id="car-test-se", skill_id="sk-python", required_level=4))
    db.add(CareerDegree(career_id="car-test-se", degree_id="deg-test"))

    # RIASEC Questions (48 required)
    types = ["R", "I", "A", "S", "E", "C"]
    for i in range(1, 49):
        rtype = types[(i - 1) // 8]
        db.add(RIASECQuestion(
            id=f"q-test-{i:03d}",
            riasec_type=rtype,
            question_text=f"Test question {i} ({rtype})",
            order_index=i,
        ))

    await db.commit()
