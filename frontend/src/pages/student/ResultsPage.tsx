import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Cell,
} from 'recharts';
import { recommendations as recApi, assessment as assessmentApi } from '../../api/client';
import { PageSpinner, ErrorMessage, Alert, EmptyState } from '../../components/ui';
import type { RecommendationOut, AssessmentOut } from '../../types';
import clsx from 'clsx';

const VARIANTS = [
  { id: 'hybrid', label: 'Hybrid' },
  { id: 'interest_only', label: 'Interest Only' },
  { id: 'skill_only', label: 'Skills Only' },
] as const;

type Variant = 'hybrid' | 'interest_only' | 'skill_only';

const RIASEC_LABELS: Record<string, string> = {
  realistic: 'Realistic',
  investigative: 'Investigative',
  artistic: 'Artistic',
  social: 'Social',
  enterprising: 'Enterprising',
  conventional: 'Conventional',
};

export default function ResultsPage() {
  const navigate = useNavigate();
  const [recs, setRecs] = useState<RecommendationOut[]>([]);
  const [assessment, setAssessment] = useState<AssessmentOut | null>(null);
  const [variant, setVariant] = useState<Variant>('hybrid');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [feedbackMap, setFeedbackMap] = useState<Record<string, boolean | null>>({});

  async function loadRecs(v: Variant, generate = false) {
    setLoading(true);
    setError('');
    try {
      let data: RecommendationOut[] = [];
      if (generate) {
        data = await recApi.generate({ variant: v });
      } else {
        data = await recApi.list(v);
        if (data.length === 0) {
          data = await recApi.generate({ variant: v });
        }
      }
      setRecs(data);
      const fbMap: Record<string, boolean | null> = {};
      data.forEach((r) => { fbMap[r.id] = r.is_relevant; });
      setFeedbackMap(fbMap);
    } catch (err: unknown) {
      setError((err as Error).message ?? 'Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    async function init() {
      try {
        const ass = await assessmentApi.getMyResults();
        setAssessment(ass);
        await loadRecs(variant);
      } catch (err: unknown) {
        const msg = (err as Error).message ?? '';
        if (msg.includes('No completed assessment')) {
          setError('complete-assessment');
        } else {
          setError(msg);
        }
        setLoading(false);
      }
    }
    init();
  }, []);

  const handleVariantChange = async (v: Variant) => {
    setVariant(v);
    await loadRecs(v);
  };

  const handleRegenerate = async () => {
    setGenerating(true);
    await loadRecs(variant, true);
    setGenerating(false);
  };

  const handleFeedback = async (recId: string, isRelevant: boolean) => {
    try {
      await recApi.feedback(recId, { is_relevant: isRelevant });
      setFeedbackMap((prev) => ({ ...prev, [recId]: isRelevant }));
    } catch {}
  };

  if (loading) return <PageSpinner />;

  if (error === 'complete-assessment') {
    return (
      <div className="max-w-3xl mx-auto px-4 py-10">
        <EmptyState
          title="Complete your assessment first"
          description="You need to finish the RIASEC test and rate your skills before viewing recommendations."
          action={
            <Link to="/assessment" className="btn-primary">
              Start Assessment →
            </Link>
          }
        />
      </div>
    );
  }

  const riasecRadarData = assessment?.riasec_score
    ? Object.entries(RIASEC_LABELS).map(([key, label]) => ({
        dimension: label,
        value: Math.round(assessment!.riasec_score![key as keyof typeof assessment.riasec_score] as number ?? 0),
      }))
    : [];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4 mb-8">
        <div>
          <h1 className="page-title">Career Recommendations</h1>
          <p className="page-subtitle">Based on your RIASEC profile and skill ratings</p>
        </div>
        <button
          onClick={handleRegenerate}
          disabled={generating || loading}
          className="btn-secondary text-sm"
        >
          {generating ? <span className="spinner h-4 w-4" /> : '🔄'} Regenerate
        </button>
      </div>

      {error && error !== 'complete-assessment' && (
        <Alert type="error" className="mb-6">{error}</Alert>
      )}

      {/* Variant switcher */}
      <div className="flex flex-wrap gap-2 mb-6">
        {VARIANTS.map((v) => (
          <button
            key={v.id}
            onClick={() => handleVariantChange(v.id)}
            className={clsx(
              'text-sm px-4 py-2 rounded-lg border font-medium transition-all',
              variant === v.id
                ? 'bg-primary-700 border-primary-600 text-white'
                : 'border-slate-700 text-slate-400 hover:text-white hover:border-slate-500',
            )}
          >
            {v.label}
          </button>
        ))}
      </div>

      {/* RIASEC Profile */}
      {riasecRadarData.length > 0 && (
        <div className="card mb-8">
          <h2 className="section-title mb-4">Your RIASEC Profile</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={riasecRadarData}>
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis
                  dataKey="dimension"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                />
                <Radar
                  name="Score"
                  dataKey="value"
                  stroke="#6166f5"
                  fill="#6166f5"
                  fillOpacity={0.3}
                  strokeWidth={2}
                />
                <Tooltip
                  contentStyle={{
                    background: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    color: '#e2e8f0',
                  }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Results */}
      {recs.length === 0 ? (
        <EmptyState
          title="No recommendations yet"
          description="Try regenerating with your current data."
          action={
            <button onClick={handleRegenerate} className="btn-primary" disabled={generating}>
              {generating ? <span className="spinner h-4 w-4" /> : 'Generate Now'}
            </button>
          }
        />
      ) : (
        <div className="space-y-4">
          {recs.map((rec) => (
            <CareerCard
              key={rec.id}
              rec={rec}
              riasecProfile={assessment?.riasec_score}
              feedback={feedbackMap[rec.id] ?? null}
              onFeedback={(isRelevant) => handleFeedback(rec.id, isRelevant)}
            />
          ))}
        </div>
      )}

      {/* Disclaimer */}
      <div className="mt-8 p-4 rounded-lg bg-yellow-900/10 border border-yellow-700/30">
        <p className="text-xs text-yellow-300/80">
          ⚠️ These recommendations are guidance only and not a final decision. Always discuss your options with a qualified career counsellor.
        </p>
      </div>
    </div>
  );
}

function CareerCard({
  rec,
  riasecProfile,
  feedback,
  onFeedback,
}: {
  rec: RecommendationOut;
  riasecProfile: AssessmentOut['riasec_score'];
  feedback: boolean | null;
  onFeedback: (isRelevant: boolean) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const matchPct = Math.round(rec.match_score * 100);

  const factorData = [
    { name: 'Interest', value: Math.round(rec.factor_breakdown.interest_contribution * 100) },
    { name: 'Skills', value: Math.round(rec.factor_breakdown.skill_contribution * 100) },
    { name: 'Degree', value: Math.round(rec.factor_breakdown.degree_contribution * 100) },
  ];

  const careerRadarData = riasecProfile
    ? Object.entries(RIASEC_LABELS).map(([key, label]) => ({
        dimension: label,
        you: Math.round((riasecProfile[key as keyof typeof riasecProfile] as number) ?? 0),
      }))
    : [];

  return (
    <div className="card hover:border-primary-700/40 transition-all">
      {/* Card header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-700 to-accent-600 flex items-center justify-center text-white font-bold text-sm shrink-0">
            #{rec.rank}
          </div>
          <div>
            <h3 className="font-semibold text-white text-base">{rec.career_title}</h3>
            <div className="flex items-center gap-2 mt-1">
              <div className="h-1.5 w-24 bg-surface-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-primary-600 to-primary-400 rounded-full"
                  style={{ width: `${matchPct}%` }}
                />
              </div>
              <span className="text-sm font-semibold text-primary-400">{matchPct}% match</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Feedback buttons */}
          <button
            onClick={() => onFeedback(true)}
            aria-label="Mark as relevant"
            className={clsx(
              'p-2 rounded-lg border text-sm transition-all',
              feedback === true
                ? 'bg-emerald-700 border-emerald-600 text-white'
                : 'border-slate-700 text-slate-400 hover:border-emerald-600 hover:text-emerald-400',
            )}
          >
            👍
          </button>
          <button
            onClick={() => onFeedback(false)}
            aria-label="Mark as not relevant"
            className={clsx(
              'p-2 rounded-lg border text-sm transition-all',
              feedback === false
                ? 'bg-red-800 border-red-700 text-white'
                : 'border-slate-700 text-slate-400 hover:border-red-600 hover:text-red-400',
            )}
          >
            👎
          </button>

          <Link to={`/skillgap/${rec.career_id}`} className="btn-secondary text-xs px-3 py-2">
            Skill Gap →
          </Link>

          <button
            onClick={() => setExpanded((e) => !e)}
            className="btn-ghost text-xs px-3 py-2"
          >
            {expanded ? 'Less ▲' : 'More ▼'}
          </button>
        </div>
      </div>

      {/* Explanations */}
      <div className="mt-4 space-y-1.5">
        {rec.factor_breakdown.top3_explanation.map((exp, i) => (
          <p key={i} className="text-xs text-slate-400 flex gap-2">
            <span className="text-primary-500 shrink-0">•</span>
            {exp}
          </p>
        ))}
        {rec.factor_breakdown.is_cold_start && (
          <p className="text-xs text-yellow-400/80">
            ⚡ Cold-start recommendation – based primarily on your interest profile.
          </p>
        )}
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="mt-5 pt-5 border-t border-slate-700/50 grid grid-cols-1 md:grid-cols-2 gap-6 animate-fade-in">
          {/* Factor breakdown bars */}
          <div>
            <h4 className="text-sm font-medium text-slate-300 mb-3">Score Breakdown</h4>
            <div className="h-40">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={factorData} layout="vertical">
                  <XAxis type="number" domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 10 }} />
                  <YAxis type="category" dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} width={50} />
                  <Tooltip
                    contentStyle={{
                      background: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#e2e8f0',
                    }}
                    formatter={(val: number) => [`${val}%`]}
                  />
                  <Bar dataKey="value" radius={4}>
                    <Cell fill="#6166f5" />
                    <Cell fill="#10b981" />
                    <Cell fill="#f59e0b" />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Interest Similarity', val: `${Math.round(rec.factor_breakdown.interest_similarity * 100)}%` },
              { label: 'Skill Coverage', val: `${Math.round(rec.factor_breakdown.skill_coverage * 100)}%` },
              { label: 'Degree Eligibility', val: `${Math.round(rec.factor_breakdown.degree_eligibility * 100)}%` },
              { label: 'Overall Match', val: `${matchPct}%` },
            ].map(({ label, val }) => (
              <div key={label} className="card-sm text-center">
                <p className="text-lg font-bold text-primary-400">{val}</p>
                <p className="text-xs text-slate-500 mt-0.5">{label}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
