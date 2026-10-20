"""
CareerCompass – Recommendations router (FR-7, FR-8, FR-9, FR-19).
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_active_student, require_owner_or_admin, get_current_user
from app.models.models import (
    User, Assessment, RIASECScore, StudentProfile, StudentSkillRating,
    Career, CareerSkill, CareerDegree, Recommendation, RecommendationFeedback,
    Setting
)
from app.schemas.schemas import (
    RecommendationOut, FeedbackSubmit, RecommendationFeedbackOut,
    GenerateRecommendationsRequest, FactorBreakdown
)
from app.services.recommender.engine import rank_careers
from app.services.assessment.scoring import score_vector_from_riasec

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


async def _load_weights(db: AsyncSession) -> tuple[float, float, float]:
    """Load recommendation weights from the settings table."""
    result = await db.execute(select(Setting).where(Setting.key.in_(["w1", "w2", "w3"])))
    settings = {s.key: float(s.value) for s in result.scalars().all()}
    w1 = settings.get("w1", 0.5)
    w2 = settings.get("w2", 0.3)
    w3 = settings.get("w3", 0.2)
    return w1, w2, w3


async def _load_careers_dict(db: AsyncSession) -> list[dict]:
    """
    Pre-load all active careers with their required skills and eligible degrees.
    Returns a list of plain dicts (no ORM objects) for the recommendation engine.
    Pre-fetching avoids N+1 queries and keeps recommendations under 3s (NFR-1).
    """
    result = await db.execute(
        select(Career)
        .where(Career.is_active == True)
        .options(
            selectinload(Career.required_skills).selectinload(CareerSkill.skill),
            selectinload(Career.eligible_degrees).selectinload(CareerDegree.degree),
        )
    )
    careers = result.scalars().all()

    career_dicts = []
    for c in careers:
        career_dicts.append({
            "id": c.id,
            "title": c.title,
            "r_score": c.r_score,
            "i_score": c.i_score,
            "a_score": c.a_score,
            "s_score": c.s_score,
            "e_score": c.e_score,
            "c_score": c.c_score,
            "required_skills": [
                {"skill_id": cs.skill_id, "required_level": cs.required_level}
                for cs in c.required_skills
            ],
            "eligible_degree_ids": [cd.degree_id for cd in c.eligible_degrees],
        })
    return career_dicts


@router.post("/generate", response_model=List[RecommendationOut], status_code=201)
async def generate_recommendations(
    body: GenerateRecommendationsRequest,
    current_user: User = Depends(get_current_active_student),
    db: AsyncSession = Depends(get_db),
) -> List[RecommendationOut]:
    """
    Generate top-10 career recommendations (FR-7, FR-8).
    Must respond in < 3 seconds for 95% of requests (NFR-1).

    Steps:
        1. Load student's RIASEC scores and skill ratings.
        2. Load all active careers (pre-fetched for performance).
        3. Load weights from settings table.
        4. Run the ranking engine.
        5. Persist recommendations to DB.
        6. Return ranked results.
    """
    # 1. Load completed assessment
    assess_result = await db.execute(
        select(Assessment)
        .where(Assessment.student_id == current_user.id)
        .where(Assessment.status == "completed")
        .options(selectinload(Assessment.riasec_score))
        .order_by(Assessment.completed_at.desc())
    )
    assessment = assess_result.scalars().first()
    if not assessment or not assessment.riasec_score:
        raise HTTPException(
            status_code=400,
            detail="Complete the RIASEC assessment first",
        )

    student_riasec = score_vector_from_riasec(assessment.riasec_score)

    # 2. Load skill ratings
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()

    student_skill_ratings: dict[str, int] = {}
    student_degree_id: Optional[str] = None

    if profile:
        student_degree_id = profile.degree_id
        ratings_result = await db.execute(
            select(StudentSkillRating).where(StudentSkillRating.student_profile_id == profile.id)
        )
        student_skill_ratings = {r.skill_id: r.rating for r in ratings_result.scalars().all()}

    # 3. Load weights
    w1, w2, w3 = await _load_weights(db)

    # 4. Load careers
    careers = await _load_careers_dict(db)
    if not careers:
        raise HTTPException(status_code=404, detail="No active careers found in database")

    # 5. Run engine
    ranked = rank_careers(
        student_riasec=student_riasec,
        student_skill_ratings=student_skill_ratings,
        student_degree_id=student_degree_id,
        careers=careers,
        w1=w1,
        w2=w2,
        w3=w3,
        top_n=10,
        variant=body.variant,
    )

    # 6. Persist – delete old recommendations for this assessment, insert new
    old_recs = await db.execute(
        select(Recommendation).where(Recommendation.assessment_id == assessment.id)
        .where(Recommendation.variant == body.variant)
    )
    for old in old_recs.scalars().all():
        await db.delete(old)

    db_recs = []
    for rank, item in enumerate(ranked, start=1):
        rec = Recommendation(
            assessment_id=assessment.id,
            career_id=item["career_id"],
            rank=rank,
            match_score=item["match_score"],
            factor_breakdown=item["factor_breakdown"],
            variant=body.variant,
        )
        db.add(rec)
        db_recs.append((rec, item))

    await db.commit()

    # Reload to get IDs
    output = []
    for rec, item in db_recs:
        await db.refresh(rec)
        output.append(RecommendationOut(
            id=rec.id,
            career_id=item["career_id"],
            career_title=item["career_title"],
            rank=rec.rank,
            match_score=rec.match_score,
            factor_breakdown=FactorBreakdown(**item["factor_breakdown"]),
            variant=body.variant,
        ))

    return output


@router.get("/", response_model=List[RecommendationOut])
async def list_recommendations(
    variant: str = "hybrid",
    current_user: User = Depends(get_current_active_student),
    db: AsyncSession = Depends(get_db),
) -> List[RecommendationOut]:
    """Return previously generated recommendations for this student."""
    assess_result = await db.execute(
        select(Assessment)
        .where(Assessment.student_id == current_user.id)
        .where(Assessment.status == "completed")
        .order_by(Assessment.completed_at.desc())
    )
    assessment = assess_result.scalars().first()
    if not assessment:
        return []

    result = await db.execute(
        select(Recommendation, Career)
        .join(Career, Recommendation.career_id == Career.id)
        .where(Recommendation.assessment_id == assessment.id)
        .where(Recommendation.variant == variant)
        .options(selectinload(Recommendation.feedback))
        .order_by(Recommendation.rank)
    )
    rows = result.all()

    output = []
    for rec, career in rows:
        is_relevant = rec.feedback.is_relevant if rec.feedback else None
        output.append(RecommendationOut(
            id=rec.id,
            career_id=rec.career_id,
            career_title=career.title,
            rank=rec.rank,
            match_score=rec.match_score,
            factor_breakdown=FactorBreakdown(**rec.factor_breakdown),
            variant=rec.variant,
            is_relevant=is_relevant,
        ))
    return output


@router.post("/{recommendation_id}/feedback", response_model=RecommendationFeedbackOut)
async def submit_feedback(
    recommendation_id: str,
    body: FeedbackSubmit,
    current_user: User = Depends(get_current_active_student),
    db: AsyncSession = Depends(get_db),
) -> RecommendationFeedbackOut:
    """
    Student marks recommendation as relevant/not-relevant (FR-19).
    Also accepts an optional 1-5 rating and comment.
    """
    # Ownership check: verify the recommendation belongs to this student
    result = await db.execute(
        select(Recommendation, Assessment)
        .join(Assessment, Recommendation.assessment_id == Assessment.id)
        .where(Recommendation.id == recommendation_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    rec, assessment = row

    if assessment.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Upsert feedback
    fb_result = await db.execute(
        select(RecommendationFeedback)
        .where(RecommendationFeedback.recommendation_id == recommendation_id)
    )
    feedback = fb_result.scalar_one_or_none()

    if feedback:
        feedback.is_relevant = body.is_relevant
        feedback.rating = body.rating
        feedback.comment = body.comment
    else:
        feedback = RecommendationFeedback(
            recommendation_id=recommendation_id,
            is_relevant=body.is_relevant,
            rating=body.rating,
            comment=body.comment,
        )
        db.add(feedback)

    await db.commit()
    await db.refresh(feedback)
    return RecommendationFeedbackOut.model_validate(feedback)
