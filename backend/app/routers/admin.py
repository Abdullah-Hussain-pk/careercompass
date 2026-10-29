"""
CareerCompass – Admin router (FR-17, FR-18, FR-16 approval).
Manages careers, users, weights, expert submissions, and analytics.
"""
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.models import (
    User, Career, CareerSkill, CareerDegree, Degree, Skill,
    Setting, ExpertSubmission, Assessment, Recommendation,
    RecommendationFeedback, Booking
)
from app.schemas.schemas import (
    CareerOut, CareerCreate, CareerUpdate, CareerSkillOut,
    UserOut, AdminCreateUser, SettingOut, SettingUpdate, WeightsUpdate, WeightsOut,
    ExpertSubmissionOut, ReviewSubmission, AnalyticsSummary, EvaluationResult
)
from app.services.analytics.evaluator import compute_evaluation

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Careers CRUD (FR-17) ────────────────────────────────────────────────────

async def _career_to_out(career: Career, db: AsyncSession) -> CareerOut:
    """Helper: convert Career ORM to CareerOut schema."""
    skills = []
    for cs in career.required_skills:
        skills.append(CareerSkillOut(
            skill_id=cs.skill_id,
            skill_name=cs.skill.name if cs.skill else "Unknown",
            required_level=cs.required_level,
        ))
    degree_names = [cd.degree.name for cd in career.eligible_degrees if cd.degree]
    return CareerOut(
        id=career.id,
        title=career.title,
        description=career.description,
        r_score=career.r_score,
        i_score=career.i_score,
        a_score=career.a_score,
        s_score=career.s_score,
        e_score=career.e_score,
        c_score=career.c_score,
        typical_roles=career.typical_roles,
        salary_range=career.salary_range,
        source=career.source,
        is_active=career.is_active,
        last_updated=career.last_updated,
        required_skills=skills,
        eligible_degrees=degree_names,
    )


@router.get("/careers", response_model=List[CareerOut])
async def list_careers(
    include_inactive: bool = False,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> List[CareerOut]:
    """List all careers (admin can see inactive ones)."""
    query = select(Career).options(
        selectinload(Career.required_skills).selectinload(CareerSkill.skill),
        selectinload(Career.eligible_degrees).selectinload(CareerDegree.degree),
    )
    if not include_inactive:
        query = query.where(Career.is_active == True)

    result = await db.execute(query.order_by(Career.title))
    careers = result.scalars().all()
    return [await _career_to_out(c, db) for c in careers]


@router.get("/careers/all-public", response_model=List[CareerOut])
async def list_careers_public(db: AsyncSession = Depends(get_db)) -> List[CareerOut]:
    """Public career listing (active only) – no auth needed."""
    result = await db.execute(
        select(Career)
        .where(Career.is_active == True)
        .options(
            selectinload(Career.required_skills).selectinload(CareerSkill.skill),
            selectinload(Career.eligible_degrees).selectinload(CareerDegree.degree),
        )
        .order_by(Career.title)
    )
    return [await _career_to_out(c, db) for c in result.scalars().all()]


@router.post("/careers", response_model=CareerOut, status_code=201)
async def create_career(
    body: CareerCreate,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> CareerOut:
    """Add a new career (FR-17)."""
    career = Career(
        title=body.title,
        description=body.description,
        r_score=body.r_score, i_score=body.i_score, a_score=body.a_score,
        s_score=body.s_score, e_score=body.e_score, c_score=body.c_score,
        typical_roles=body.typical_roles,
        salary_range=body.salary_range,
        source=body.source,
    )
    db.add(career)
    await db.flush()

    # Add skills
    for skill_item in body.required_skills:
        db.add(CareerSkill(
            career_id=career.id,
            skill_id=skill_item.skill_id,
            required_level=skill_item.rating,
        ))

    # Add degrees
    for degree_id in body.eligible_degree_ids:
        db.add(CareerDegree(career_id=career.id, degree_id=degree_id))

    await db.commit()

    result = await db.execute(
        select(Career).where(Career.id == career.id).options(
            selectinload(Career.required_skills).selectinload(CareerSkill.skill),
            selectinload(Career.eligible_degrees).selectinload(CareerDegree.degree),
        )
    )
    return await _career_to_out(result.scalar_one(), db)


@router.patch("/careers/{career_id}", response_model=CareerOut)
async def update_career(
    career_id: str,
    body: CareerUpdate,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> CareerOut:
    """Edit a career (FR-17, NFR-7 – editable without code changes)."""
    result = await db.execute(select(Career).where(Career.id == career_id))
    career = result.scalar_one_or_none()
    if not career:
        raise HTTPException(status_code=404, detail="Career not found")

    update_data = body.model_dump(exclude_none=True, exclude={"required_skills", "eligible_degree_ids"})
    for field, value in update_data.items():
        setattr(career, field, value)
    career.last_updated = datetime.now(timezone.utc)

    # Update skills if provided
    if body.required_skills is not None:
        await db.execute(delete(CareerSkill).where(CareerSkill.career_id == career_id))
        for skill_item in body.required_skills:
            db.add(CareerSkill(career_id=career_id, skill_id=skill_item.skill_id, required_level=skill_item.rating))

    # Update degrees if provided
    if body.eligible_degree_ids is not None:
        await db.execute(delete(CareerDegree).where(CareerDegree.career_id == career_id))
        for degree_id in body.eligible_degree_ids:
            db.add(CareerDegree(career_id=career_id, degree_id=degree_id))

    await db.commit()

    result2 = await db.execute(
        select(Career).where(Career.id == career_id).options(
            selectinload(Career.required_skills).selectinload(CareerSkill.skill),
            selectinload(Career.eligible_degrees).selectinload(CareerDegree.degree),
        )
    )
    return await _career_to_out(result2.scalar_one(), db)


@router.delete("/careers/{career_id}/deactivate", status_code=200)
async def deactivate_career(
    career_id: str,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Soft-delete (deactivate) a career (FR-17)."""
    result = await db.execute(select(Career).where(Career.id == career_id))
    career = result.scalar_one_or_none()
    if not career:
        raise HTTPException(status_code=404, detail="Career not found")
    career.is_active = False
    await db.commit()
    return {"ok": True, "message": f"Career '{career.title}' deactivated"}


# ── User Management ─────────────────────────────────────────────────────────

@router.post("/users", response_model=UserOut, status_code=201)
async def admin_create_user(
    body: AdminCreateUser,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """
    Admin-only endpoint to create counsellor / expert / admin accounts (H2 / FR-2).
    Public registration (/auth/register) is restricted to students only.
    """
    from app.core.security import hash_password
    from app.models.models import AuditLog

    # Reject duplicate email
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
    )
    db.add(new_user)
    await db.flush()  # get new_user.id

    # Audit log (no email in detail – NFR-4 / GDPR)
    audit = AuditLog(
        action="user_created_by_admin",
        resource_type="user",
        actor_id=current_user.id,
        resource_id=new_user.id,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(new_user)
    return UserOut.model_validate(new_user)


@router.get("/users", response_model=List[UserOut])
async def list_users(
    role: Optional[str] = None,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> List[UserOut]:
    """List all users, optionally filtered by role."""
    query = select(User)
    if role:
        query = query.where(User.role == role)
    result = await db.execute(query.order_by(User.created_at.desc()))
    return [UserOut.model_validate(u) for u in result.scalars().all()]


@router.patch("/users/{user_id}/deactivate", status_code=200)
async def deactivate_user(
    user_id: str,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Deactivate a user account."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    await db.commit()
    return {"ok": True}


# ── Weights (NFR-7) ─────────────────────────────────────────────────────────

@router.get("/weights", response_model=WeightsOut)
async def get_weights(
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> WeightsOut:
    """Return current recommendation weights."""
    result = await db.execute(select(Setting).where(Setting.key.in_(["w1", "w2", "w3"])))
    settings = {s.key: float(s.value) for s in result.scalars().all()}
    return WeightsOut(
        w1=settings.get("w1", 0.5),
        w2=settings.get("w2", 0.3),
        w3=settings.get("w3", 0.2),
    )


@router.put("/weights", response_model=WeightsOut)
async def update_weights(
    body: WeightsUpdate,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> WeightsOut:
    """Update recommendation weights (NFR-7, must sum to 1.0)."""
    for key, value in [("w1", body.w1), ("w2", body.w2), ("w3", body.w3)]:
        result = await db.execute(select(Setting).where(Setting.key == key))
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = str(value)
        else:
            db.add(Setting(key=key, value=str(value)))
    await db.commit()
    return WeightsOut(w1=body.w1, w2=body.w2, w3=body.w3)


# ── Expert Submissions (FR-16) ──────────────────────────────────────────────

@router.get("/submissions", response_model=List[ExpertSubmissionOut])
async def list_submissions(
    status: Optional[str] = "pending",
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> List[ExpertSubmissionOut]:
    """List expert submissions filtered by status."""
    query = select(ExpertSubmission)
    if status:
        query = query.where(ExpertSubmission.status == status)
    result = await db.execute(query.order_by(ExpertSubmission.submitted_at.desc()))
    return [ExpertSubmissionOut.model_validate(s) for s in result.scalars().all()]


@router.patch("/submissions/{submission_id}/review", response_model=ExpertSubmissionOut)
async def review_submission(
    submission_id: str,
    body: ReviewSubmission,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ExpertSubmissionOut:
    """Approve or reject an expert submission (FR-16)."""
    result = await db.execute(select(ExpertSubmission).where(ExpertSubmission.id == submission_id))
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    submission.status = body.status
    submission.admin_comment = body.admin_comment
    submission.reviewed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(submission)
    return ExpertSubmissionOut.model_validate(submission)


# ── Analytics (FR-18) ──────────────────────────────────────────────────────

@router.get("/analytics", response_model=AnalyticsSummary)
async def get_analytics(
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsSummary:
    """Admin analytics dashboard (FR-18)."""
    # Total students
    total_students = await db.scalar(
        select(func.count(User.id)).where(User.role == "student")
    )

    # Completed assessments
    completed = await db.scalar(
        select(func.count(Assessment.id)).where(Assessment.status == "completed")
    )

    # Total bookings
    total_bookings = await db.scalar(select(func.count(Booking.id)))

    # Top 10 most recommended careers
    top_careers_result = await db.execute(
        select(Career.title, func.count(Recommendation.id).label("count"))
        .join(Recommendation, Recommendation.career_id == Career.id)
        .group_by(Career.title)
        .order_by(func.count(Recommendation.id).desc())
        .limit(10)
    )
    top_careers = [{"career": row.title, "count": row.count} for row in top_careers_result.all()]

    # Average feedback rating
    avg_rating = await db.scalar(
        select(func.avg(RecommendationFeedback.rating)).where(
            RecommendationFeedback.rating.isnot(None)
        )
    )

    return AnalyticsSummary(
        total_students=total_students or 0,
        completed_assessments=completed or 0,
        total_bookings=total_bookings or 0,
        top_careers=top_careers,
        avg_feedback_rating=round(float(avg_rating), 2) if avg_rating else None,
    )


@router.get("/evaluation", response_model=List[EvaluationResult])
async def get_evaluation(
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> List[EvaluationResult]:
    """
    Compute precision@5 and nDCG@5 from stored feedback (FR-18).
    Results are based on real student feedback (FR-19), never fabricated.
    """
    return await compute_evaluation(db)


@router.get("/degrees", response_model=List[dict])
async def list_degrees(
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """List all degrees (public endpoint for dropdowns)."""
    result = await db.execute(select(Degree).order_by(Degree.name))
    return [{"id": d.id, "name": d.name, "short_name": d.short_name} for d in result.scalars().all()]
