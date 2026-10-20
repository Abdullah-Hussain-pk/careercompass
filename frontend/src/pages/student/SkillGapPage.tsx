import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { skillgap as skillgapApi } from '../../api/client';
import { PageSpinner, ErrorMessage, EmptyState } from '../../components/ui';
import type { SkillGapResponse } from '../../types';

export default function SkillGapPage() {
  const { careerId } = useParams<{ careerId: string }>();
  const [data, setData] = useState<SkillGapResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!careerId) return;
    skillgapApi
      .get(careerId)
      .then(setData)
      .catch((err: Error) => setError(err.message ?? 'Failed to load skill gap'))
      .finally(() => setLoading(false));
  }, [careerId]);

  if (loading) return <PageSpinner />;
  if (error) return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <ErrorMessage message={error} />
      <Link to="/results" className="btn-secondary mt-4">← Back to Results</Link>
    </div>
  );
  if (!data) return null;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4 mb-8">
        <div>
          <Link to="/results" className="text-xs text-slate-500 hover:text-slate-300 mb-2 inline-block">
            ← Back to Results
          </Link>
          <h1 className="page-title">Skill Gap: {data.career_title}</h1>
          <p className="page-subtitle">
            {data.gaps.length} skill{data.gaps.length !== 1 ? 's' : ''} to develop for this career
          </p>
        </div>
      </div>

      {data.gaps.length === 0 ? (
        <EmptyState
          title="No skill gaps found!"
          description="Your current skill levels meet all the requirements for this career. 🎉"
          action={<Link to="/booking" className="btn-primary">Book a Session</Link>}
        />
      ) : (
        <div className="space-y-6">
          {/* Gap summary */}
          <div className="card">
            <h2 className="section-title mb-4">Skill Gaps Overview</h2>
            <div className="space-y-3">
              {data.gaps.map((gap) => (
                <div key={gap.skill_id}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-slate-200">{gap.skill_name}</span>
                    <span className="text-xs text-slate-400">
                      Level {gap.student_level} → {gap.required_level} needed (gap: {gap.gap})
                    </span>
                  </div>
                  <div className="h-2 bg-surface-700 rounded-full overflow-hidden flex">
                    <div
                      className="h-full bg-emerald-600 rounded-l-full"
                      style={{ width: `${(gap.student_level / gap.required_level) * 100}%` }}
                    />
                    <div
                      className="h-full bg-red-700/50"
                      style={{ width: `${(gap.gap / gap.required_level) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Roadmap */}
          <div>
            <h2 className="section-title mb-4">Learning Roadmap</h2>
            <div className="space-y-4">
              {data.roadmap.map((milestone, i) => (
                <div key={milestone.skill_id} className="card">
                  <div className="flex items-start gap-4">
                    <div className="w-8 h-8 rounded-full bg-primary-800 border border-primary-700 flex items-center justify-center text-primary-300 font-bold text-sm shrink-0">
                      {i + 1}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <h3 className="font-semibold text-white">{milestone.skill_name}</h3>
                        <span className="badge-red">Gap: {milestone.gap}</span>
                      </div>

                      {milestone.resources.length > 0 ? (
                        <div className="mt-3 space-y-2">
                          <p className="text-xs text-slate-500 uppercase tracking-wider">Learning Resources</p>
                          {milestone.resources.map((res) => (
                            <a
                              key={res.id}
                              href={res.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center justify-between p-3 rounded-lg bg-surface-900 border border-slate-700 hover:border-primary-600 transition-colors group"
                            >
                              <div>
                                <p className="text-sm text-slate-200 group-hover:text-white font-medium">{res.title}</p>
                                {res.provider && (
                                  <p className="text-xs text-slate-500">{res.provider}</p>
                                )}
                              </div>
                              <div className="flex items-center gap-2">
                                {res.is_free && (
                                  <span className="badge-green">Free</span>
                                )}
                                <svg className="w-4 h-4 text-slate-500 group-hover:text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                </svg>
                              </div>
                            </a>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-slate-600 mt-2">No resources available yet for this skill.</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="mt-8 flex gap-4">
        <Link to="/results" className="btn-secondary">← Back to Results</Link>
        <Link to="/booking" className="btn-primary">Book a Counsellor Session →</Link>
      </div>
    </div>
  );
}
