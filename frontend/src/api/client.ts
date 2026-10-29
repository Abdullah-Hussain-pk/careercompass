/**
 * CareerCompass – Central API client
 * - Attaches Bearer token from localStorage
 * - Handles 401 by clearing token and redirecting to /login
 * - Provides typed methods for every backend endpoint
 */

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const PREFIX = `${API_BASE}/api/v1`;

// ── Token helpers ────────────────────────────────────────────

export function getToken(): string | null {
  return localStorage.getItem('cc_token');
}

export function setToken(token: string): void {
  localStorage.setItem('cc_token', token);
}

export function clearToken(): void {
  localStorage.removeItem('cc_token');
  localStorage.removeItem('cc_user');
}

// ── Core fetch wrapper ───────────────────────────────────────

type FetchOptions = {
  method?: string;
  body?: unknown;
  formData?: URLSearchParams;
  signal?: AbortSignal;
  skipAuth?: boolean;
};

async function apiFetch<T>(path: string, opts: FetchOptions = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {};

  if (!opts.formData) {
    headers['Content-Type'] = 'application/json';
  }
  if (token && !opts.skipAuth) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${PREFIX}${path}`, {
    method: opts.method ?? 'GET',
    headers,
    body: opts.formData
      ? opts.formData
      : opts.body !== undefined
        ? JSON.stringify(opts.body)
        : undefined,
    signal: opts.signal,
  });

  // 401 → clear credentials and redirect to login
  if (res.status === 401) {
    clearToken();
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }

  // 204 No Content
  if (res.status === 204) {
    return undefined as T;
  }

  const data = await res.json();

  if (!res.ok) {
    const message = data?.detail ?? `HTTP ${res.status}`;
    throw Object.assign(new Error(message), { status: res.status, data });
  }

  return data as T;
}

// ── Auth ─────────────────────────────────────────────────────

import type {
  UserOut, TokenResponse, StudentProfileOut, StudentProfileUpdate,
  RIASECQuestionOut, AssessmentOut, ProgressResponse, SkillOut,
  StudentSkillRatingOut, SkillRatingItem, DegreeOut, RecommendationOut,
  FeedbackSubmit, GenerateRecommendationsRequest, SkillGapResponse,
  SlotWithCounsellorOut, SlotOut, BookingOut, ConsentOut, SessionNoteOut,
  NotificationOut, ExpertSubmissionOut, ExpertSubmissionCreate,
  CareerOut, CareerCreate, CareerUpdate, WeightsOut, AnalyticsSummary,
  EvaluationResult, AnswerItem,
} from '../types';

export const auth = {
  register: (body: { email: string; password: string; full_name: string }) =>
    apiFetch<UserOut>('/auth/register', { method: 'POST', body, skipAuth: true }),

  login: (email: string, password: string) => {
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);
    return apiFetch<TokenResponse>('/auth/login', {
      method: 'POST',
      formData: form,
      skipAuth: true,
    });
  },

  me: () => apiFetch<UserOut>('/auth/me'),

  deleteAccount: () => apiFetch<void>('/auth/me', { method: 'DELETE' }),
};

// ── Assessment ───────────────────────────────────────────────

export const assessment = {
  getQuestions: () =>
    apiFetch<RIASECQuestionOut[]>('/assessment/questions', { skipAuth: true }),

  getProfile: () => apiFetch<StudentProfileOut>('/assessment/profile'),

  updateProfile: (body: StudentProfileUpdate) =>
    apiFetch<StudentProfileOut>('/assessment/profile', { method: 'PATCH', body }),

  startAssessment: () =>
    apiFetch<AssessmentOut>('/assessment/start', { method: 'POST' }),

  saveProgress: (answers: AnswerItem[]) =>
    apiFetch<AssessmentOut>('/assessment/progress', {
      method: 'POST',
      body: { answers },
    }),

  getProgress: () => apiFetch<ProgressResponse>('/assessment/progress'),

  submitAssessment: (answers: AnswerItem[]) =>
    apiFetch<AssessmentOut>('/assessment/submit', {
      method: 'POST',
      body: { answers },
    }),

  getMyResults: () => apiFetch<AssessmentOut>('/assessment/my-results'),

  getSkills: () => apiFetch<SkillOut[]>('/assessment/skills'),

  rateSkills: (ratings: SkillRatingItem[]) =>
    apiFetch<StudentSkillRatingOut[]>('/assessment/skills/rate', {
      method: 'POST',
      body: { ratings },
    }),

  getMyRatings: () =>
    apiFetch<StudentSkillRatingOut[]>('/assessment/skills/my-ratings'),
};

// ── Degrees ──────────────────────────────────────────────────

export const degrees = {
  list: () => apiFetch<DegreeOut[]>('/admin/degrees', { skipAuth: true }),
};

// ── Recommendations ──────────────────────────────────────────

export const recommendations = {
  generate: (body: GenerateRecommendationsRequest) =>
    apiFetch<RecommendationOut[]>('/recommendations/generate', {
      method: 'POST',
      body,
    }),

  list: (variant = 'hybrid') =>
    apiFetch<RecommendationOut[]>(`/recommendations/?variant=${variant}`),

  feedback: (id: string, body: FeedbackSubmit) =>
    apiFetch(`/recommendations/${id}/feedback`, { method: 'POST', body }),
};

// ── Skill Gap ─────────────────────────────────────────────────

export const skillgap = {
  get: (careerId: string) =>
    apiFetch<SkillGapResponse>(`/skillgap/${careerId}`),
};

// ── Booking ───────────────────────────────────────────────────

export const booking = {
  // Slots (student)
  listAvailableSlots: (counsellorId?: string) => {
    const qs = counsellorId ? `?counsellor_id=${counsellorId}` : '';
    return apiFetch<SlotWithCounsellorOut[]>(`/booking/slots${qs}`);
  },

  // Bookings (student & counsellor)
  createBooking: (slot_id: string, grant_consent: boolean) =>
    apiFetch<BookingOut>('/booking/bookings', {
      method: 'POST',
      body: { slot_id, grant_consent },
    }),

  listBookings: () => apiFetch<BookingOut[]>('/booking/bookings'),

  cancelBooking: (id: string) =>
    apiFetch<void>(`/booking/bookings/${id}`, { method: 'DELETE' }),

  updateConsent: (id: string, granted: boolean) =>
    apiFetch<ConsentOut>(`/booking/bookings/${id}/consent`, {
      method: 'PATCH',
      body: { granted },
    }),

  getStudentResults: (bookingId: string) =>
    apiFetch<AssessmentOut>(`/booking/bookings/${bookingId}/student-results`),

  createNote: (bookingId: string, notes: string) =>
    apiFetch<SessionNoteOut>(`/booking/bookings/${bookingId}/notes`, {
      method: 'POST',
      body: { notes },
    }),

  // Counsellor slots
  createSlot: (start_time: string) =>
    apiFetch<SlotOut>('/booking/slots', { method: 'POST', body: { start_time } }),

  getMySlots: () => apiFetch<SlotOut[]>('/booking/slots/my'),

  deleteSlot: (id: string) =>
    apiFetch<void>(`/booking/slots/${id}`, { method: 'DELETE' }),

  // Notifications
  getNotifications: () => apiFetch<NotificationOut[]>('/booking/notifications'),

  markNotificationRead: (id: string) =>
    apiFetch<{ ok: boolean }>(`/booking/notifications/${id}/read`, {
      method: 'PATCH',
    }),
};

// ── Admin ─────────────────────────────────────────────────────

export const admin = {
  // Careers
  listCareers: (includeInactive = false) =>
    apiFetch<CareerOut[]>(`/admin/careers?include_inactive=${includeInactive}`),

  createCareer: (body: CareerCreate) =>
    apiFetch<CareerOut>('/admin/careers', { method: 'POST', body }),

  updateCareer: (id: string, body: CareerUpdate) =>
    apiFetch<CareerOut>(`/admin/careers/${id}`, { method: 'PATCH', body }),

  deactivateCareer: (id: string) =>
    apiFetch<{ ok: boolean }>(`/admin/careers/${id}/deactivate`, {
      method: 'DELETE',
    }),

  // Users
  listUsers: (role?: string) => {
    const qs = role ? `?role=${role}` : '';
    return apiFetch<UserOut[]>(`/admin/users${qs}`);
  },

  deactivateUser: (id: string) =>
    apiFetch<{ ok: boolean }>(`/admin/users/${id}/deactivate`, {
      method: 'PATCH',
    }),

  createUser: (body: {
    email: string;
    password: string;
    full_name: string;
    role: string;
  }) =>
    apiFetch<UserOut>('/admin/users', { method: 'POST', body }),

  // Weights
  getWeights: () => apiFetch<WeightsOut>('/admin/weights'),

  updateWeights: (body: WeightsOut) =>
    apiFetch<WeightsOut>('/admin/weights', { method: 'PUT', body }),

  // Submissions
  listSubmissions: (status?: string) => {
    const qs = status ? `?status=${status}` : '';
    return apiFetch<ExpertSubmissionOut[]>(`/admin/submissions${qs}`);
  },

  reviewSubmission: (id: string, body: { status: string; admin_comment?: string }) =>
    apiFetch<ExpertSubmissionOut>(`/admin/submissions/${id}/review`, {
      method: 'PATCH',
      body,
    }),

  // Analytics
  getAnalytics: () => apiFetch<AnalyticsSummary>('/admin/analytics'),

  getEvaluation: () => apiFetch<EvaluationResult[]>('/admin/evaluation'),
};

// ── Expert ─────────────────────────────────────────────────────

export const expert = {
  submit: (body: ExpertSubmissionCreate) =>
    apiFetch<ExpertSubmissionOut>('/expert/submissions', {
      method: 'POST',
      body,
    }),

  listMySubmissions: () =>
    apiFetch<ExpertSubmissionOut[]>('/expert/submissions'),
};
