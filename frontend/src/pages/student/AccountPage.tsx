import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { assessment as assessmentApi, degrees as degreesApi, auth as authApi } from '../../api/client';
import { PageSpinner, Alert, ConfirmDialog } from '../../components/ui';
import type { DegreeOut } from '../../types';

export default function AccountPage() {
  const { user, logout } = useAuth();
  const [degrees, setDegrees] = useState<DegreeOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const [form, setForm] = useState({
    degree_id: '',
    semester: '',
    cgpa: '',
    phone: '',
  });

  useEffect(() => {
    if (user?.role !== 'student') {
      setLoading(false);
      return;
    }
    async function load() {
      try {
        const [profileData, degreesData] = await Promise.all([
          assessmentApi.getProfile().catch(() => null),
          degreesApi.list().catch(() => []),
        ]);
        setDegrees(degreesData as DegreeOut[]);
        if (profileData) {
          setForm({
            degree_id: profileData.degree_id ?? '',
            semester: profileData.semester?.toString() ?? '',
            cgpa: profileData.cgpa?.toString() ?? '',
            phone: profileData.phone ?? '',
          });
        }
      } catch (err: unknown) {
        setError((err as Error).message ?? 'Failed to load profile');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [user]);

  const handleSave = async () => {
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      const body = {
        ...(form.degree_id ? { degree_id: form.degree_id } : {}),
        ...(form.semester ? { semester: parseInt(form.semester) } : {}),
        ...(form.cgpa ? { cgpa: parseFloat(form.cgpa) } : {}),
        ...(form.phone ? { phone: form.phone } : {}),
      };
      await assessmentApi.updateProfile(body);
      setSuccess('Profile updated successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: unknown) {
      setError((err as Error).message ?? 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await authApi.deleteAccount();
      logout();
    } catch (err: unknown) {
      setError((err as Error).message ?? 'Failed to delete account');
      setDeleting(false);
    }
  };

  if (loading) return <PageSpinner />;

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-10">
      <h1 className="page-title mb-8">Account Settings</h1>

      {/* User info */}
      <div className="card mb-6">
        <h2 className="section-title mb-4">Account Info</h2>
        <div className="space-y-3">
          <div>
            <span className="label">Full Name</span>
            <p className="text-slate-200">{user?.full_name}</p>
          </div>
          <div>
            <span className="label">Email</span>
            <p className="text-slate-200">{user?.email}</p>
          </div>
          <div>
            <span className="label">Role</span>
            <p className="text-slate-200 capitalize">{user?.role}</p>
          </div>
          <div>
            <span className="label">Member since</span>
            <p className="text-slate-200">{user?.created_at ? new Date(user.created_at).toLocaleDateString('en-MY', { year: 'numeric', month: 'long', day: 'numeric' }) : '—'}</p>
          </div>
        </div>
      </div>

      {/* Student profile */}
      {user?.role === 'student' && (
        <div className="card mb-6">
          <h2 className="section-title mb-4">Academic Profile</h2>
          <p className="text-sm text-slate-400 mb-5">
            Your academic details help improve career recommendations.
          </p>

          {error && <Alert type="error" onClose={() => setError('')} className="mb-4">{error}</Alert>}
          {success && <Alert type="success" onClose={() => setSuccess('')} className="mb-4">{success}</Alert>}

          <div className="space-y-4">
            <div>
              <label htmlFor="degree" className="label">Degree Programme</label>
              <select
                id="degree"
                value={form.degree_id}
                onChange={(e) => setForm({ ...form, degree_id: e.target.value })}
                className="input"
              >
                <option value="">— Select your degree —</option>
                {degrees.map((d) => (
                  <option key={d.id} value={d.id}>{d.name}{d.short_name ? ` (${d.short_name})` : ''}</option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="semester" className="label">Semester</label>
                <input
                  id="semester"
                  type="number"
                  min={1}
                  max={12}
                  value={form.semester}
                  onChange={(e) => setForm({ ...form, semester: e.target.value })}
                  className="input"
                  placeholder="e.g. 4"
                />
              </div>

              <div>
                <label htmlFor="cgpa" className="label">CGPA</label>
                <input
                  id="cgpa"
                  type="number"
                  min={0}
                  max={4}
                  step={0.01}
                  value={form.cgpa}
                  onChange={(e) => setForm({ ...form, cgpa: e.target.value })}
                  className="input"
                  placeholder="e.g. 3.50"
                />
              </div>
            </div>

            <div>
              <label htmlFor="phone" className="label">Phone (optional)</label>
              <input
                id="phone"
                type="tel"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                className="input"
                placeholder="+60 12-345 6789"
              />
            </div>

            <button onClick={handleSave} disabled={saving} className="btn-primary">
              {saving ? <><span className="spinner h-4 w-4" /> Saving…</> : 'Save Profile'}
            </button>
          </div>
        </div>
      )}

      {/* Danger zone */}
      <div className="card border-red-800/40 bg-red-950/20">
        <h2 className="text-base font-semibold text-red-400 mb-2">Danger Zone</h2>
        <p className="text-sm text-slate-400 mb-4">
          Permanently delete your account and all associated data. This action is irreversible.
        </p>
        <button
          onClick={() => setDeleteConfirm(true)}
          className="btn-danger text-sm"
          id="delete-account-btn"
        >
          Delete my account and data
        </button>
      </div>

      <ConfirmDialog
        open={deleteConfirm}
        title="Delete Account"
        description="This will permanently delete your account, all assessment results, bookings, and personal data. There is no way to undo this. Are you absolutely sure?"
        confirmLabel={deleting ? 'Deleting…' : 'Yes, delete everything'}
        cancelLabel="No, keep my account"
        danger
        onConfirm={handleDelete}
        onCancel={() => setDeleteConfirm(false)}
      />
    </div>
  );
}
