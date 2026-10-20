import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { assessment as assessmentApi } from '../../api/client';
import { PageSpinner, ErrorMessage, Alert } from '../../components/ui';
import type { SkillOut, StudentSkillRatingOut } from '../../types';
import clsx from 'clsx';

export default function SkillRatingPage() {
  const navigate = useNavigate();
  const [skills, setSkills] = useState<SkillOut[]>([]);
  const [ratings, setRatings] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [category, setCategory] = useState<string | null>(null);

  const ratedCount = Object.keys(ratings).length;
  const MIN_REQUIRED = 10;

  const categories = React.useMemo(() => {
    const cats = new Set<string>();
    skills.forEach((s) => { if (s.category) cats.add(s.category); });
    return Array.from(cats).sort();
  }, [skills]);

  const displayedSkills = category
    ? skills.filter((s) => s.category === category)
    : skills;

  useEffect(() => {
    async function load() {
      try {
        const [allSkills, myRatings] = await Promise.all([
          assessmentApi.getSkills(),
          assessmentApi.getMyRatings(),
        ]);
        setSkills(allSkills);
        const ratingMap: Record<string, number> = {};
        myRatings.forEach((r: StudentSkillRatingOut) => {
          ratingMap[r.skill_id] = r.rating;
        });
        setRatings(ratingMap);
      } catch (err: unknown) {
        setError((err as Error).message ?? 'Failed to load skills');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const setRating = (skillId: string, val: number) => {
    setRatings((prev) => ({ ...prev, [skillId]: val }));
  };

  const handleSubmit = async () => {
    if (ratedCount < MIN_REQUIRED) {
      setError(`Please rate at least ${MIN_REQUIRED} skills. You've rated ${ratedCount} so far.`);
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      const ratingsList = Object.entries(ratings).map(([skill_id, rating]) => ({
        skill_id,
        rating,
      }));
      await assessmentApi.rateSkills(ratingsList);
      navigate('/results');
    } catch (err: unknown) {
      setError((err as Error).message ?? 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <PageSpinner />;
  if (error && skills.length === 0) return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <ErrorMessage message={error} onRetry={() => window.location.reload()} />
    </div>
  );

  const ratingLabels = ['Beginner', 'Basic', 'Intermediate', 'Advanced', 'Expert'];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
      {/* Header */}
      <div className="mb-6">
        <h1 className="page-title">Rate Your Skills</h1>
        <p className="page-subtitle">
          Rate at least {MIN_REQUIRED} skills from 1 (Beginner) to 5 (Expert). Be honest — this improves your recommendations.
        </p>
      </div>

      {/* Progress */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex-1">
          <div className="h-2 bg-surface-700 rounded-full overflow-hidden">
            <div
              className={clsx(
                'h-full rounded-full transition-all duration-300',
                ratedCount >= MIN_REQUIRED ? 'bg-emerald-500' : 'bg-primary-600',
              )}
              style={{ width: `${Math.min((ratedCount / skills.length) * 100, 100)}%` }}
            />
          </div>
        </div>
        <span className={clsx('text-sm font-medium shrink-0', ratedCount >= MIN_REQUIRED ? 'text-emerald-400' : 'text-slate-400')}>
          {ratedCount} / {skills.length} rated
          {ratedCount >= MIN_REQUIRED && ' ✓'}
        </span>
      </div>

      {error && (
        <Alert type="error" onClose={() => setError('')} className="mb-4">
          {error}
        </Alert>
      )}

      {/* Category filter */}
      {categories.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6">
          <button
            onClick={() => setCategory(null)}
            className={clsx('text-xs px-3 py-1.5 rounded-full border transition-colors', !category ? 'bg-primary-700 border-primary-600 text-white' : 'border-slate-700 text-slate-400 hover:text-white')}
          >
            All ({skills.length})
          </button>
          {categories.map((cat) => {
            const count = skills.filter((s) => s.category === cat).length;
            return (
              <button
                key={cat}
                onClick={() => setCategory(cat)}
                className={clsx('text-xs px-3 py-1.5 rounded-full border transition-colors', category === cat ? 'bg-primary-700 border-primary-600 text-white' : 'border-slate-700 text-slate-400 hover:text-white')}
              >
                {cat} ({count})
              </button>
            );
          })}
        </div>
      )}

      {/* Skills grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-8">
        {displayedSkills.map((skill) => (
          <div key={skill.id} className={clsx('card-sm', ratings[skill.id] ? 'border-primary-700/40' : '')}>
            <div className="flex items-start justify-between gap-2 mb-3">
              <div>
                <p className="text-sm font-medium text-white">{skill.name}</p>
                {skill.category && (
                  <span className="text-xs text-slate-500">{skill.category}</span>
                )}
              </div>
              {ratings[skill.id] && (
                <span className="text-xs text-primary-400 font-semibold shrink-0">
                  {ratingLabels[ratings[skill.id] - 1]}
                </span>
              )}
            </div>
            <div className="flex gap-1" role="group" aria-label={`Rating for ${skill.name}`}>
              {[1, 2, 3, 4, 5].map((val) => (
                <button
                  key={val}
                  onClick={() => setRating(skill.id, val)}
                  aria-label={`${val} – ${ratingLabels[val - 1]}`}
                  className={clsx(
                    'flex-1 py-2 rounded-md text-xs font-bold transition-all border focus:outline-none focus:ring-2 focus:ring-primary-500',
                    ratings[skill.id] === val
                      ? 'bg-primary-600 border-primary-500 text-white'
                      : ratings[skill.id] && val <= ratings[skill.id]
                        ? 'bg-primary-900/40 border-primary-800 text-primary-400'
                        : 'bg-surface-900 border-slate-700 text-slate-500 hover:border-slate-500 hover:text-slate-300',
                  )}
                >
                  {val}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Submit */}
      <div className="flex items-center justify-between flex-wrap gap-4 pt-4 border-t border-slate-700/50">
        <p className="text-sm text-slate-400">
          {ratedCount < MIN_REQUIRED
            ? `Rate ${MIN_REQUIRED - ratedCount} more skill${MIN_REQUIRED - ratedCount !== 1 ? 's' : ''} to continue`
            : `You've met the minimum — keep rating for better recommendations!`}
        </p>
        <button
          onClick={handleSubmit}
          disabled={ratedCount < MIN_REQUIRED || submitting}
          className="btn-primary"
        >
          {submitting ? (
            <><span className="spinner h-4 w-4" /> Saving…</>
          ) : (
            'Save & See Results →'
          )}
        </button>
      </div>
    </div>
  );
}
