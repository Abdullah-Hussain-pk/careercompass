"""
CareerCompass – All Pydantic v2 schemas for request/response validation.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Any, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================================
# Auth / Users
# ============================================================

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Min 8 characters")
    full_name: str = Field(..., min_length=1, max_length=255)

    # Extra fields (e.g. "role") are rejected at the schema level (H2).
    model_config = {"extra": "forbid"}


class AdminCreateUser(BaseModel):
    """Schema for admin-only user creation (FR-2 / H2)."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Min 8 characters")
    full_name: str = Field(..., min_length=1, max_length=255)
    role: Literal["counsellor", "expert", "admin"]  # student accounts use /auth/register


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# Student Profile
# ============================================================

class StudentProfileUpdate(BaseModel):
    degree_id: Optional[str] = None
    semester: Optional[int] = Field(None, ge=1, le=12)
    cgpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    phone: Optional[str] = Field(None, max_length=20)  # optional, NFR-4


class StudentProfileOut(BaseModel):
    id: str
    user_id: str
    degree_id: Optional[str]
    semester: Optional[int]
    cgpa: Optional[float]
    phone: Optional[str]

    model_config = {"from_attributes": True}


# ============================================================
# RIASEC Questions
# ============================================================

class RIASECQuestionOut(BaseModel):
    id: str
    riasec_type: str
    question_text: str
    order_index: int

    model_config = {"from_attributes": True}


# ============================================================
# Assessment
# ============================================================

class AnswerItem(BaseModel):
    question_id: str
    answer: int = Field(..., ge=1, le=5)


class AssessmentProgressSave(BaseModel):
    """Save partial progress (resume later, FR-3/NFR-5)."""
    answers: List[AnswerItem]


class AssessmentSubmit(BaseModel):
    """Final submission of all 48 answers."""
    answers: List[AnswerItem]

    @field_validator("answers")
    @classmethod
    def validate_count(cls, v: list) -> list:
        if len(v) != 48:
            raise ValueError("All 48 answers must be submitted")
        return v


class RIASECScoreOut(BaseModel):
    realistic: float
    investigative: float
    artistic: float
    social: float
    enterprising: float
    conventional: float
    computed_at: datetime

    model_config = {"from_attributes": True}


class AssessmentOut(BaseModel):
    id: str
    student_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    riasec_score: Optional[RIASECScoreOut]

    model_config = {"from_attributes": True}


# ============================================================
# Skills
# ============================================================

class SkillOut(BaseModel):
    id: str
    name: str
    category: Optional[str]
    description: Optional[str]

    model_config = {"from_attributes": True}


class SkillRatingItem(BaseModel):
    skill_id: str
    rating: int = Field(..., ge=1, le=5)


class SkillRatingsSubmit(BaseModel):
    ratings: List[SkillRatingItem]

    @field_validator("ratings")
    @classmethod
    def validate_min_count(cls, v: list) -> list:
        if len(v) < 10:
            raise ValueError("At least 10 skills must be rated (FR-5)")
        return v


class StudentSkillRatingOut(BaseModel):
    skill_id: str
    skill_name: str
    rating: int

    model_config = {"from_attributes": True}


class LearningResourceOut(BaseModel):
    id: str
    title: str
    url: str
    provider: Optional[str]
    is_free: bool

    model_config = {"from_attributes": True}


# ============================================================
# Degrees & Careers
# ============================================================

class DegreeOut(BaseModel):
    id: str
    name: str
    short_name: Optional[str]

    model_config = {"from_attributes": True}


class CareerSkillOut(BaseModel):
    skill_id: str
    skill_name: str
    required_level: int

    model_config = {"from_attributes": True}


class CareerOut(BaseModel):
    id: str
    title: str
    description: str
    r_score: float
    i_score: float
    a_score: float
    s_score: float
    e_score: float
    c_score: float
    typical_roles: Optional[str]
    salary_range: Optional[str]
    source: Optional[str]
    is_active: bool
    last_updated: datetime
    required_skills: List[CareerSkillOut] = []
    eligible_degrees: List[str] = []   # degree names

    model_config = {"from_attributes": True}


class CareerCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    r_score: float = Field(..., ge=0, le=100)
    i_score: float = Field(..., ge=0, le=100)
    a_score: float = Field(..., ge=0, le=100)
    s_score: float = Field(..., ge=0, le=100)
    e_score: float = Field(..., ge=0, le=100)
    c_score: float = Field(..., ge=0, le=100)
    typical_roles: Optional[str] = None
    salary_range: Optional[str] = None
    source: Optional[str] = None
    required_skills: List[SkillRatingItem] = []  # {skill_id, required_level}
    eligible_degree_ids: List[str] = []


class CareerUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    r_score: Optional[float] = Field(None, ge=0, le=100)
    i_score: Optional[float] = Field(None, ge=0, le=100)
    a_score: Optional[float] = Field(None, ge=0, le=100)
    s_score: Optional[float] = Field(None, ge=0, le=100)
    e_score: Optional[float] = Field(None, ge=0, le=100)
    c_score: Optional[float] = Field(None, ge=0, le=100)
    typical_roles: Optional[str] = None
    salary_range: Optional[str] = None
    source: Optional[str] = None
    is_active: Optional[bool] = None
    required_skills: Optional[List[SkillRatingItem]] = None
    eligible_degree_ids: Optional[List[str]] = None


# ============================================================
# Recommendations
# ============================================================

class FactorBreakdown(BaseModel):
    interest_contribution: float    # w1 * interest_similarity
    skill_contribution: float       # w2 * skill_coverage
    degree_contribution: float      # w3 * degree_eligibility
    interest_similarity: float      # raw cosine similarity
    skill_coverage: float           # raw skill coverage ratio
    degree_eligibility: float       # 1.0 or penalty
    top3_explanation: List[str]     # plain-language sentences
    is_cold_start: bool = False


class RecommendationOut(BaseModel):
    id: str
    career_id: str
    career_title: str
    rank: int
    match_score: float
    factor_breakdown: FactorBreakdown
    variant: str
    is_relevant: Optional[bool] = None   # FR-19 feedback

    model_config = {"from_attributes": True}


class FeedbackSubmit(BaseModel):
    is_relevant: bool
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None


class RecommendationFeedbackOut(BaseModel):
    recommendation_id: str
    is_relevant: bool
    rating: Optional[int]
    submitted_at: datetime

    model_config = {"from_attributes": True}


class GenerateRecommendationsRequest(BaseModel):
    variant: str = Field(default="hybrid", pattern="^(hybrid|interest_only|skill_only)$")


# ============================================================
# Skill Gap & Roadmap
# ============================================================

class SkillGapItem(BaseModel):
    skill_id: str
    skill_name: str
    student_level: int              # 0 if not rated
    required_level: int
    gap: int                        # required - student_level


class RoadmapMilestone(BaseModel):
    skill_id: str
    skill_name: str
    gap: int
    resources: List[LearningResourceOut]


class SkillGapResponse(BaseModel):
    career_id: str
    career_title: str
    gaps: List[SkillGapItem]
    roadmap: List[RoadmapMilestone]


# ============================================================
# Slots & Bookings
# ============================================================

class SlotCreate(BaseModel):
    start_time: datetime


class SlotOut(BaseModel):
    id: str
    counsellor_id: str
    start_time: datetime
    end_time: datetime
    is_booked: bool

    model_config = {"from_attributes": True}


class SlotWithCounsellorOut(SlotOut):
    counsellor_name: str


class BookingCreate(BaseModel):
    slot_id: str
    grant_consent: bool = False     # step 3 of booking flow: consent toggle


class BookingOut(BaseModel):
    id: str
    slot_id: str
    student_id: str
    counsellor_id: str
    status: str
    booked_at: datetime
    start_time: Optional[datetime] = None
    counsellor_name: Optional[str] = None
    student_name: Optional[str] = None
    consent_granted: Optional[bool] = None

    model_config = {"from_attributes": True}


class ConsentUpdate(BaseModel):
    granted: bool


class ConsentOut(BaseModel):
    booking_id: str
    granted: bool
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionNoteCreate(BaseModel):
    notes: str = Field(..., min_length=1)


class SessionNoteOut(BaseModel):
    id: str
    booking_id: str
    notes: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# Notifications
# ============================================================

class NotificationOut(BaseModel):
    id: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# Expert Submissions
# ============================================================

class ExpertSubmissionCreate(BaseModel):
    career_id: Optional[str] = None
    submission_type: str = Field(default="update", pattern="^(update|new)$")
    payload: dict


class ExpertSubmissionOut(BaseModel):
    id: str
    expert_id: str
    career_id: Optional[str]
    submission_type: str
    payload: dict
    status: str
    admin_comment: Optional[str]
    submitted_at: datetime

    model_config = {"from_attributes": True}


class ReviewSubmission(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected)$")
    admin_comment: Optional[str] = None


# ============================================================
# Admin / Settings
# ============================================================

class SettingOut(BaseModel):
    key: str
    value: str
    description: Optional[str]
    updated_at: datetime

    model_config = {"from_attributes": True}


class SettingUpdate(BaseModel):
    value: str


class WeightsUpdate(BaseModel):
    w1: float = Field(..., ge=0.0, le=1.0, description="Interest weight")
    w2: float = Field(..., ge=0.0, le=1.0, description="Skill weight")
    w3: float = Field(..., ge=0.0, le=1.0, description="Degree weight")

    @field_validator("w3")
    @classmethod
    def must_sum_to_one(cls, w3: float, info: Any) -> float:
        w1 = info.data.get("w1", 0)
        w2 = info.data.get("w2", 0)
        total = round(w1 + w2 + w3, 6)
        if abs(total - 1.0) > 1e-4:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        return w3


class WeightsOut(BaseModel):
    w1: float
    w2: float
    w3: float


# ============================================================
# Analytics
# ============================================================

class AnalyticsSummary(BaseModel):
    total_students: int
    completed_assessments: int
    total_bookings: int
    top_careers: List[dict]
    avg_feedback_rating: Optional[float]


class EvaluationResult(BaseModel):
    variant: str
    precision_at_5: float
    ndcg_at_5: float
    mean_relevance_rating: Optional[float]
    sample_size: int


# ============================================================
# Pagination helper
# ============================================================

class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[Any]


# ============================================================
# Error schema
# ============================================================

class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
