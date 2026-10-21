import { Link, Route, Routes } from 'react-router-dom';
import Navbar from './components/Navbar';
import ProtectedRoute from './routes/ProtectedRoute';

import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import { PrivacyPage, DisclaimerPage } from './pages/LegalPages';

import DashboardPage from './pages/student/DashboardPage';
import AssessmentPage from './pages/student/AssessmentPage';
import SkillRatingPage from './pages/student/SkillRatingPage';
import ResultsPage from './pages/student/ResultsPage';
import SkillGapPage from './pages/student/SkillGapPage';
import BookingPage from './pages/student/BookingPage';
import AccountPage from './pages/student/AccountPage';

import CounsellorSlotsPage from './pages/counsellor/CounsellorSlotsPage';
import CounsellorBookingsPage from './pages/counsellor/CounsellorBookingsPage';

import AdminAnalyticsPage from './pages/admin/AdminAnalyticsPage';
import AdminCareersPage from './pages/admin/AdminCareersPage';

function Placeholder({ title }: { title: string }) {
  return (
    <div className="max-w-3xl mx-auto px-4 py-24 text-center">
      <h1 className="text-2xl font-bold mb-2">{title}</h1>
      <p className="text-slate-400">This page is not implemented yet.</p>
    </div>
  );
}

function Unauthorized() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-24 text-center">
      <h1 className="text-2xl font-bold mb-2">Access denied</h1>
      <p className="text-slate-400 mb-6">You do not have permission to view this page.</p>
      <Link to="/" className="btn-primary">Go home</Link>
    </div>
  );
}

function NotFound() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-24 text-center">
      <h1 className="text-2xl font-bold mb-2">Page not found</h1>
      <Link to="/" className="btn-primary mt-4 inline-block">Go home</Link>
    </div>
  );
}

export default function App() {
  return (
    <>
      <Navbar />
      <Routes>
        {/* Public */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/disclaimer" element={<DisclaimerPage />} />
        <Route path="/unauthorized" element={<Unauthorized />} />

        {/* Any logged-in user */}
        <Route element={<ProtectedRoute />}>
          <Route path="/account" element={<AccountPage />} />
        </Route>

        {/* Student */}
        <Route element={<ProtectedRoute allowedRoles={['student']} />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/assessment" element={<AssessmentPage />} />
          <Route path="/assessment/skills" element={<SkillRatingPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/skillgap/:careerId" element={<SkillGapPage />} />
          <Route path="/booking" element={<BookingPage />} />
        </Route>

        {/* Counsellor */}
        <Route element={<ProtectedRoute allowedRoles={['counsellor']} />}>
          <Route path="/counsellor/slots" element={<CounsellorSlotsPage />} />
          <Route path="/counsellor/bookings" element={<CounsellorBookingsPage />} />
        </Route>

        {/* Admin */}
        <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
          <Route path="/admin/analytics" element={<AdminAnalyticsPage />} />
          <Route path="/admin/careers" element={<AdminCareersPage />} />
          <Route path="/admin/users" element={<Placeholder title="Users" />} />
          <Route path="/admin/weights" element={<Placeholder title="Weights" />} />
          <Route path="/admin/submissions" element={<Placeholder title="Submissions" />} />
          <Route path="/admin/evaluation" element={<Placeholder title="Evaluation" />} />
        </Route>

        {/* Expert */}
        <Route element={<ProtectedRoute allowedRoles={['expert']} />}>
          <Route path="/expert/submit" element={<Placeholder title="Submit Update" />} />
          <Route path="/expert/submissions" element={<Placeholder title="My Submissions" />} />
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
}
