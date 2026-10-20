// ============================================================
// CareerCompass – All TypeScript types matching backend schemas
// ============================================================

export interface UserOut {
  id: string;
  email: string;
  full_name: string;
  role: 'student' | 'counsellor' | 'admin' | 'expert';
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface StudentProfileOut {
  id: string;
  user_id: string;
  degree_id: string | null;
  semester: number | null;
  cgpa: number | null;
  phone: string | null;
}

export interface StudentProfileUpdate {
  degree_id?: string;
  semester?: number;
  cgpa?: number;
  phone?: string;
}

export interface RIASECQuestionOut {
  id: string;
  riasec_type: string;
  question_text: string;
  order_index: number;
}

export interface AnswerItem {
  question_id: string;
  answer: number;
}

export interface RIASECScoreOut {
  realistic: number;
  investigative: number;
  artistic: number;
  social: number;
  enterprising: number;
  conventional: number;
  computed_at: string;
}

export interface AssessmentOut {
  id: string;
  student_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  riasec_score: RIASECScoreOut | null;
}

export interface ProgressResponse {
  assessment_id: string | null;
  answered: number;
  total: number;
  saved_answers?: Record<string, number>;
}

export interface SkillOut {
  id: string;
  name: string;
  category: string | null;
  description: string | null;
}

export interface SkillRatingItem {
  skill_id: string;
  rating: number;
}

export interface StudentSkillRatingOut {
  skill_id: string;
  skill_name: string;
  rating: number;
}

export interface DegreeOut {
  id: string;
  name: string;
  short_name: string | null;
}

export interface CareerSkillOut {
  skill_id: string;
  skill_name: string;
  required_level: number;
}

export interface CareerOut {
  id: string;
  title: string;
  description: string;
  r_score: number;
  i_score: number;
  a_score: number;
  s_score: number;
  e_score: number;
  c_score: number;
  typical_roles: string | null;
  salary_range: string | null;
  source: string | null;
  is_active: boolean;
  last_updated: string;
  required_skills: CareerSkillOut[];
  eligible_degrees: string[];
}

export interface CareerCreate {
  title: string;
  description: string;
  r_score: number;
  i_score: number;
  a_score: number;
  s_score: number;
  e_score: number;
  c_score: number;
  typical_roles?: string;
  salary_range?: string;
  source?: string;
  required_skills: SkillRatingItem[];
  eligible_degree_ids: string[];
}

export interface CareerUpdate extends Partial<CareerCreate> {
  is_active?: boolean;
}

export interface FactorBreakdown {
  interest_contribution: number;
  skill_contribution: number;
  degree_contribution: number;
  interest_similarity: number;
  skill_coverage: number;
  degree_eligibility: number;
  top3_explanation: string[];
  is_cold_start: boolean;
}

export interface RecommendationOut {
  id: string;
  career_id: string;
  career_title: string;
  rank: number;
  match_score: number;
  factor_breakdown: FactorBreakdown;
  variant: string;
  is_relevant: boolean | null;
}

export interface FeedbackSubmit {
  is_relevant: boolean;
  rating?: number;
  comment?: string;
}

export interface GenerateRecommendationsRequest {
  variant: 'hybrid' | 'interest_only' | 'skill_only';
}

export interface SkillGapItem {
  skill_id: string;
  skill_name: string;
  student_level: number;
  required_level: number;
  gap: number;
}

export interface LearningResourceOut {
  id: string;
  title: string;
  url: string;
  provider: string | null;
  is_free: boolean;
}

export interface RoadmapMilestone {
  skill_id: string;
  skill_name: string;
  gap: number;
  resources: LearningResourceOut[];
}

export interface SkillGapResponse {
  career_id: string;
  career_title: string;
  gaps: SkillGapItem[];
  roadmap: RoadmapMilestone[];
}

export interface SlotOut {
  id: string;
  counsellor_id: string;
  start_time: string;
  end_time: string;
  is_booked: boolean;
}

export interface SlotWithCounsellorOut extends SlotOut {
  counsellor_name: string;
}

export interface BookingOut {
  id: string;
  slot_id: string;
  student_id: string;
  counsellor_id: string;
  status: string;
  booked_at: string;
  start_time: string | null;
  counsellor_name: string | null;
  student_name: string | null;
  consent_granted: boolean | null;
}

export interface ConsentOut {
  booking_id: string;
  granted: boolean;
  updated_at: string;
}

export interface SessionNoteOut {
  id: string;
  booking_id: string;
  notes: string;
  created_at: string;
}

export interface NotificationOut {
  id: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface ExpertSubmissionOut {
  id: string;
  expert_id: string;
  career_id: string | null;
  submission_type: string;
  payload: Record<string, unknown>;
  status: string;
  admin_comment: string | null;
  submitted_at: string;
}

export interface ExpertSubmissionCreate {
  career_id?: string;
  submission_type: 'update' | 'new';
  payload: Record<string, unknown>;
}

export interface WeightsOut {
  w1: number;
  w2: number;
  w3: number;
}

export interface AnalyticsSummary {
  total_students: number;
  completed_assessments: number;
  total_bookings: number;
  top_careers: { career: string; count: number }[];
  avg_feedback_rating: number | null;
}

export interface EvaluationResult {
  variant: string;
  precision_at_5: number;
  ndcg_at_5: number;
  mean_relevance_rating: number | null;
  sample_size: number;
}

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}

export interface ApiError {
  detail: string;
  code?: string;
}
