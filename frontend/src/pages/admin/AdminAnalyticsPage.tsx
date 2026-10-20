import React, { useEffect, useState } from 'react';
import { admin as adminApi } from '../../api/client';
import { PageSpinner, ErrorMessage } from '../../components/ui';
import type { AnalyticsSummary, EvaluationResult } from '../../types';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

const COLORS = ['#6166f5', '#10b981', '#f59e0b', '#ec4899', '#06b6d4', '#8b5cf6', '#f97316', '#84cc16', '#e11d48', '#0ea5e9'];

export default function AdminAnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluationResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const [a, e] = await Promise.all([adminApi.getAnalytics(), adminApi.getEvaluation()]);
        setAnalytics(a);
        setEvaluation(e);
      } catch (err: unknown) {
        setError((err as Error).message ?? 'Failed to load analytics');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <PageSpinner />;
  if (error) return <div className="max-w-5xl mx-auto px-4 py-10"><ErrorMessage message={error} onRetry={() => window.location.reload()} /></div>;
  if (!analytics) return null;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
      <h1 className="page-title mb-8">Analytics Dashboard</h1>

      {/* KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        {[
          { label: 'Total Students', value: analytics.total_students, color: 'text-primary-400' },
          { label: 'Completed Assessments', value: analytics.completed_assessments, color: 'text-emerald-400' },
          { label: 'Total Bookings', value: analytics.total_bookings, color: 'text-yellow-400' },
          { label: 'Avg Feedback Rating', value: analytics.avg_feedback_rating ? `${analytics.avg_feedback_rating.toFixed(1)} / 5` : 'N/A', color: 'text-accent-400' },
        ].map((kpi) => (
          <div key={kpi.label} className="card text-center">
            <p className={`text-3xl font-extrabold ${kpi.color}`}>{kpi.value}</p>
            <p className="text-xs text-slate-500 mt-1">{kpi.label}</p>
          </div>
        ))}
      </div>

      {/* Top careers chart */}
      {analytics.top_careers.length > 0 && (
        <div className="card mb-8">
          <h2 className="section-title mb-4">Top Recommended Careers</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics.top_careers} layout="vertical">
                <XAxis type="number" tick={{ fill: '#64748b', fontSize: 10 }} />
                <YAxis type="category" dataKey="career" tick={{ fill: '#94a3b8', fontSize: 11 }} width={140} />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#e2e8f0' }}
                />
                <Bar dataKey="count" radius={4}>
                  {analytics.top_careers.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Evaluation table */}
      {evaluation.length > 0 && (
        <div className="card">
          <h2 className="section-title mb-4">Recommendation Evaluation (FR-18)</h2>
          <p className="text-xs text-slate-500 mb-4">
            Precision@5 and nDCG@5 computed from real student feedback.
          </p>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Variant</th>
                  <th>Precision@5</th>
                  <th>nDCG@5</th>
                  <th>Mean Rating</th>
                  <th>Sample Size</th>
                </tr>
              </thead>
              <tbody>
                {evaluation.map((ev) => (
                  <tr key={ev.variant}>
                    <td className="font-medium text-white capitalize">{ev.variant.replace('_', ' ')}</td>
                    <td className="text-primary-400">{(ev.precision_at_5 * 100).toFixed(1)}%</td>
                    <td className="text-emerald-400">{(ev.ndcg_at_5 * 100).toFixed(1)}%</td>
                    <td>{ev.mean_relevance_rating?.toFixed(2) ?? 'N/A'}</td>
                    <td>{ev.sample_size}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
