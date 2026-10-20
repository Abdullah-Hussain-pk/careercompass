"""
CareerCompass – Skill-gap analysis and learning roadmap (FR-10, FR-11).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_active_student
from app.models.models import (
    User, StudentProfile, StudentSkillRating, Career,
    CareerSkill, LearningResource
)
from app.schemas.schemas import SkillGapResponse, SkillGapItem, RoadmapMilestone, LearningResourceOut

router = APIRouter(prefix="/skillgap", tags=["Skill Gap"])


@router.get("/{career_id}", response_model=SkillGapResponse)
async def get_skill_gap(
    career_id: str,
    current_user: User = Depends(get_current_active_student),
    db: AsyncSession = Depends(get_db),
) -> SkillGapResponse:
    """
    Compute skill gap between student's ratings and a career's requirements (FR-10).
    Also return an ordered learning roadmap with curated resource links (FR-11).

    Only shows skills where student_level < required_level (actual gaps).
    Roadmap orders milestones from largest gap to smallest.
    """
    # Load career with skills
    career_result = await db.execute(
        select(Career)
        .where(Career.id == career_id)
        .where(Career.is_active == True)
        .options(
            selectinload(Career.required_skills).selectinload(CareerSkill.skill)
        )
    )
    career = career_result.scalar_one_or_none()
    if not career:
        raise HTTPException(status_code=404, detail="Career not found")

    # Load student skill ratings
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()

    student_ratings: dict[str, int] = {}
    if profile:
        ratings_result = await db.execute(
            select(StudentSkillRating)
            .where(StudentSkillRating.student_profile_id == profile.id)
        )
        student_ratings = {r.skill_id: r.rating for r in ratings_result.scalars().all()}

    # Compute gaps
    gaps: list[SkillGapItem] = []
    for career_skill in career.required_skills:
        student_level = student_ratings.get(career_skill.skill_id, 0)
        gap = career_skill.required_level - student_level
        if gap > 0:
            gaps.append(SkillGapItem(
                skill_id=career_skill.skill_id,
                skill_name=career_skill.skill.name,
                student_level=student_level,
                required_level=career_skill.required_level,
                gap=gap,
            ))

    # Sort by gap (largest first) for roadmap ordering
    gaps.sort(key=lambda g: g.gap, reverse=True)

    # Build roadmap: fetch learning resources for each gap skill
    roadmap: list[RoadmapMilestone] = []
    for gap_item in gaps:
        resources_result = await db.execute(
            select(LearningResource)
            .where(LearningResource.skill_id == gap_item.skill_id)
            .where(LearningResource.is_free == True)
            .limit(3)
        )
        resources = resources_result.scalars().all()
        roadmap.append(RoadmapMilestone(
            skill_id=gap_item.skill_id,
            skill_name=gap_item.skill_name,
            gap=gap_item.gap,
            resources=[LearningResourceOut.model_validate(r) for r in resources],
        ))

    return SkillGapResponse(
        career_id=career.id,
        career_title=career.title,
        gaps=gaps,
        roadmap=roadmap,
    )
