import React, { useEffect, useState } from 'react';
import { admin as adminApi, degrees as degreesApi, assessment as assessmentApi } from '../../api/client';
import { PageSpinner, ErrorMessage, Alert, EmptyState, Modal, ConfirmDialog } from '../../components/ui';
import type { CareerOut, CareerCreate, DegreeOut, SkillOut } from '../../types';
import clsx from 'clsx';

const RIASEC_FIELDS: { key: keyof CareerCreate; label: string }[] = [
  { key: 'r_score', label: 'Realistic (R)' },
  { key: 'i_score', label: 'Investigative (I)' },
  { key: 'a_score', label: 'Artistic (A)' },
  { key: 's_score', label: 'Social (S)' },
  { key: 'e_score', label: 'Enterprising (E)' },
  { key: 'c_score', label: 'Conventional (C)' },
];

const emptyForm = (): Partial<CareerCreate> => ({
  title: '',
  description: '',
  r_score: 0, i_score: 0, a_score: 0,
  s_score: 0, e_score: 0, c_score: 0,
  typical_roles: '',
  salary_range: '',
  source: '',
  required_skills: [],
  eligible_degree_ids: [],
});

export default function AdminCareersPage() {
  const [careers, setCareers] = useState<CareerOut[]>([]);
  const [degrees, setDegrees] = useState<DegreeOut[]>([]);
  const [skills, setSkills] = useState<SkillOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [includeInactive, setIncludeInactive] = useState(false);

  // Modal state
  const [editingCareer, setEditingCareer] = useState<CareerOut | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState<Partial<CareerCreate>>(emptyForm());
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');

  // Deactivate
  const [deactivateTarget, setDeactivateTarget] = useState<CareerOut | null>(null);

  useEffect(() => {
    loadData();
  }, [includeInactive]);

  async function loadData() {
    setLoading(true);
    try {
      const [careersData, degreesData, skillsData] = await Promise.all([
        adminApi.listCareers(includeInactive),
        degreesApi.list(),
        assessmentApi.getSkills(),
      ]);
      setCareers(careersData);
      setDegrees(degreesData);
      setSkills(skillsData);
    } catch (err: unknown) {
      setError((err as Error).message ?? 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }

  const openCreate = () => {
    setEditingCareer(null);
    setForm(emptyForm());
    setFormError('');
    setFormOpen(true);
  };

  const openEdit = (career: CareerOut) => {
    setEditingCareer(career);
    setForm({
      title: career.title,
      description: career.description,
      r_score: career.r_score,
      i_score: career.i_score,
      a_score: career.a_score,
      s_score: career.s_score,
      e_score: career.e_score,
      c_score: career.c_score,
      typical_roles: career.typical_roles ?? '',
      salary_range: career.salary_range ?? '',
      source: career.source ?? '',
      required_skills: career.required_skills.map((s) => ({ skill_id: s.skill_id, rating: s.required_level })),
      eligible_degree_ids: degrees.filter((d) => career.eligible_degrees.includes(d.name)).map((d) => d.id),
    });
    setFormError('');
    setFormOpen(true);
  };

  const handleSave = async () => {
    setFormError('');
    setSaving(true);
    try {
      if (editingCareer) {
        await adminApi.updateCareer(editingCareer.id, form as CareerCreate);
      } else {
        await adminApi.createCareer(form as CareerCreate);
      }
      setFormOpen(false);
      setSuccess(`Career ${editingCareer ? 'updated' : 'created'} successfully!`);
      setTimeout(() => setSuccess(''), 3000);
      await loadData();
    } catch (err: unknown) {
      setFormError((err as Error).message ?? 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async () => {
    if (!deactivateTarget) return;
    try {
      await adminApi.deactivateCareer(deactivateTarget.id);
      setDeactivateTarget(null);
      setSuccess(`Career "${deactivateTarget.title}" deactivated.`);
      setTimeout(() => setSuccess(''), 3000);
      await loadData();
    } catch (err: unknown) {
      setError((err as Error).message ?? 'Failed to deactivate');
    }
  };

  const toggleDegree = (id: string) => {
    const curr = form.eligible_degree_ids ?? [];
    setForm({ ...form, eligible_degree_ids: curr.includes(id) ? curr.filter((d) => d !== id) : [...curr, id] });
  };

  if (loading) return <PageSpinner />;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
      <div className="flex items-center justify-between flex-wrap gap-4 mb-8">
        <div>
          <h1 className="page-title">Career Management</h1>
          <p className="page-subtitle">{careers.length} career{careers.length !== 1 ? 's' : ''}</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
              className="rounded"
            />
            Show inactive
          </label>
          <button onClick={openCreate} className="btn-primary">+ Add Career</button>
        </div>
      </div>

      {error && <Alert type="error" onClose={() => setError('')} className="mb-4">{error}</Alert>}
      {success && <Alert type="success" onClose={() => setSuccess('')} className="mb-4">{success}</Alert>}

      {careers.length === 0 ? (
        <EmptyState title="No careers found" description="Add your first career to get started." action={<button onClick={openCreate} className="btn-primary">Add Career</button>} />
      ) : (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Title</th>
                <th>RIASEC Profile</th>
                <th>Skills</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {careers.map((c) => (
                <tr key={c.id}>
                  <td>
                    <div>
                      <p className="font-medium text-white">{c.title}</p>
                      {c.salary_range && <p className="text-xs text-slate-500">{c.salary_range}</p>}
                    </div>
                  </td>
                  <td>
                    <div className="flex gap-1 flex-wrap">
                      {[
                        { l: 'R', v: c.r_score }, { l: 'I', v: c.i_score },
                        { l: 'A', v: c.a_score }, { l: 'S', v: c.s_score },
                        { l: 'E', v: c.e_score }, { l: 'C', v: c.c_score },
                      ].map(({ l, v }) => (
                        <span key={l} className="text-xs px-1.5 py-0.5 rounded bg-surface-700 text-slate-400">
                          {l}:{Math.round(v)}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td>{c.required_skills.length}</td>
                  <td>
                    <span className={clsx('badge', c.is_active ? 'badge-green' : 'badge-slate')}>
                      {c.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    <div className="flex gap-2">
                      <button onClick={() => openEdit(c)} className="text-xs text-primary-400 hover:text-primary-300">Edit</button>
                      {c.is_active && (
                        <button onClick={() => setDeactivateTarget(c)} className="text-xs text-red-400 hover:text-red-300">Deactivate</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Career form modal */}
      <Modal
        open={formOpen}
        onClose={() => setFormOpen(false)}
        title={editingCareer ? `Edit: ${editingCareer.title}` : 'Add New Career'}
        size="xl"
      >
        <div className="space-y-5">
          {formError && <Alert type="error">{formError}</Alert>}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="sm:col-span-2">
              <label className="label">Title *</label>
              <input className="input" value={form.title ?? ''} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Software Engineer" />
            </div>
            <div className="sm:col-span-2">
              <label className="label">Description *</label>
              <textarea className="input resize-none" rows={3} value={form.description ?? ''} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Brief career description…" />
            </div>
            <div>
              <label className="label">Salary Range</label>
              <input className="input" value={form.salary_range ?? ''} onChange={(e) => setForm({ ...form, salary_range: e.target.value })} placeholder="e.g. RM 5,000 – RM 12,000/month" />
            </div>
            <div>
              <label className="label">Typical Roles</label>
              <input className="input" value={form.typical_roles ?? ''} onChange={(e) => setForm({ ...form, typical_roles: e.target.value })} placeholder="e.g. Junior Dev, Senior Dev" />
            </div>
          </div>

          {/* RIASEC sliders */}
          <div>
            <p className="label mb-3">RIASEC Profile Scores (0–100)</p>
            <div className="grid grid-cols-2 gap-3">
              {RIASEC_FIELDS.map(({ key, label }) => (
                <div key={key}>
                  <div className="flex justify-between mb-1">
                    <label className="text-xs text-slate-400">{label}</label>
                    <span className="text-xs text-primary-400">{form[key] ?? 0}</span>
                  </div>
                  <input
                    type="range" min={0} max={100} step={1}
                    value={form[key] as number ?? 0}
                    onChange={(e) => setForm({ ...form, [key]: parseFloat(e.target.value) })}
                    className="w-full accent-primary-500"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Eligible degrees */}
          <div>
            <p className="label mb-2">Eligible Degrees</p>
            <div className="flex flex-wrap gap-2">
              {degrees.map((d) => (
                <button
                  key={d.id}
                  type="button"
                  onClick={() => toggleDegree(d.id)}
                  className={clsx('text-xs px-2.5 py-1 rounded-full border transition-all', (form.eligible_degree_ids ?? []).includes(d.id) ? 'bg-primary-700 border-primary-600 text-white' : 'border-slate-700 text-slate-400 hover:text-white')}
                >
                  {d.short_name ?? d.name}
                </button>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2 border-t border-slate-700">
            <button onClick={() => setFormOpen(false)} className="btn-secondary">Cancel</button>
            <button onClick={handleSave} disabled={saving} className="btn-primary">
              {saving ? <><span className="spinner h-4 w-4" /> Saving…</> : editingCareer ? 'Save Changes' : 'Create Career'}
            </button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        open={!!deactivateTarget}
        title="Deactivate Career"
        description={`Are you sure you want to deactivate "${deactivateTarget?.title}"? It will no longer appear in recommendations.`}
        confirmLabel="Deactivate"
        danger
        onConfirm={handleDeactivate}
        onCancel={() => setDeactivateTarget(null)}
      />
    </div>
  );
}
