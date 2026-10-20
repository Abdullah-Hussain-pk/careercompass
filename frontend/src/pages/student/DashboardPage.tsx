import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { assessment as assessmentApi } from '../api/client';
import { PageSpinner } from '../components/ui';
import clsx from 'clsx';

type StepStatus = 'done' | 'active' | 'pending';

const STEPS = [
  { id: 'profile', label: 'Profile', icon: '👤', desc: 'Set up your academic details' },
  { id: 'assessment', label: 'Interest Test', icon: '🧠', desc: 'Take the 48-question RIASEC test' },
  { id: 'skills', label: 'Skills', icon: '⚡', desc: 'Rate at least 10 skills' },
  { id: 'results', label: 'Results', icon: '🎯', desc: 'Get your career recommendations' },
  { id: 'booking', label: 'Book Session', icon: '🗓️', desc: 'Optional counsellor session' },
];

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState<{
    hasProfile: boolean;
    hasAssessment: boolean;
    hasSkills: boolean;
    hasResults: boolean;
  }>({ hasProfile: false, hasAssessment: false, hasSkills: false, hasResults: false });

  useEffect(() => {
    async function loadProgress() {
      try {
        const [profileRes, progressRes, ratingsRes, resultsRes] = await Promise.allSettled([
          assessmentApi.getProfile(),
          assessmentApi.getProgress(),
          assessmentApi.getMyRatings(),
          assessmentApi.getMyResults(),
        ]);

        setProgress({
          hasProfile:
            profileRes.status === 'fulfilled' &&
            !!(profileRes.value.degree_id || profileRes.value.semester || profileRes.value.cgpa),
          hasAssessment:
            progressRes.status === 'fulfilled' && progressRes.value.assessment_id !== null,
          hasSkills:
            ratingsRes.status === 'fulfilled' && ratingsRes.value.length >= 10,
          hasResults: resultsRes.status === 'fulfilled',
        });
      } catch {
        // ignore errors
      } finally {
        setLoading(false);
      }
    }
    loadProgress();
  }, []);

  const stepStatuses = (): StepStatus[] => {
    const { hasProfile, hasAssessment, hasSkills, hasResults } = progress;
    // Determine current active step
    if (!hasProfile) return ['active', 'pending', 'pending', 'pending', 'pending'];
    if (!hasAssessment) return ['done', 'active', 'pending', 'pending', 'pending'];
    if (!hasSkills) return ['done', 'done', 'active', 'pending', 'pending'];
    if (!hasResults) return ['done', 'done', 'done', 'active', 'pending'];
    return ['done', 'done', 'done', 'done', 'active'];
  };

  const stepHrefs = [
    '/account',
    '/assessment',
    '/assessment/skills',
    '/results',
    '/booking',
  ];

  const statuses = stepStatuses();
  const activeStep = statuses.findIndex((s) => s === 'active');

  if (loading) return <PageSpinner />;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
      {/* Welcome header */}
      <div className="mb-10">
        <h1 className="page-title">
          Welcome back, {user?.full_name.split(' ')[0]}! 👋
        </h1>
        <p className="page-subtitle">
          {progress.hasResults
            ? 'Your career recommendations are ready. Continue exploring below.'
            : 'Complete the steps below to get your personalised career recommendations.'}
        </p>
      </div>

      {/* Stepper */}
      <div className="card mb-8">
        <h2 className="section-title mb-6">Your Journey</h2>
        <div className="relative">
          {/* Progress line */}
          <div className="absolute left-5 top-6 bottom-6 w-0.5 bg-slate-700" />
          <div
            className="absolute left-5 top-6 w-0.5 bg-primary-600 transition-all duration-700"
            style={{ height: `${(activeStep / (STEPS.length - 1)) * 100}%` }}
          />

          <div className="space-y-4 relative">
            {STEPS.map((step, i) => {
              const status = statuses[i];
              return (
                <div key={step.id} className="flex items-start gap-5">
                  {/* Step indicator */}
                  <div
                    className={clsx(
                      'relative z-10 w-10 h-10 rounded-full flex items-center justify-center shrink-0 border-2 transition-all duration-300',
                      status === 'done' && 'bg-emerald-600 border-emerald-500 text-white',
                      status === 'active' && 'bg-primary-700 border-primary-500 text-white animate-pulse-slow',
                      status === 'pending' && 'bg-surface-900 border-slate-600 text-slate-600',
                    )}
                  >
                    {status === 'done' ? (
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      <span className="text-sm">{step.icon}</span>
                    )}
                  </div>

                  {/* Step content */}
                  <div className="flex-1 pb-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <p
                          className={clsx(
                            'font-semibold text-sm',
                            status === 'active' ? 'text-white' : status === 'done' ? 'text-slate-300' : 'text-slate-600',
                          )}
                        >
                          {step.label}
                        </p>
                        <p className={clsx('text-xs mt-0.5', status === 'pending' ? 'text-slate-700' : 'text-slate-500')}>
                          {step.desc}
                        </p>
                      </div>
                      {status !== 'pending' && (
                        <Link
                          to={stepHrefs[i]}
                          className={clsx(
                            'text-xs font-medium shrink-0 ml-4',
                            status === 'active' ? 'text-primary-400 hover:text-primary-300' : 'text-slate-500 hover:text-slate-300',
                          )}
                        >
                          {status === 'done' ? 'Review →' : 'Start →'}
                        </Link>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Quick action card */}
      {activeStep >= 0 && activeStep < STEPS.length && (
        <div className="card bg-gradient-to-br from-primary-900/40 to-surface-800 border-primary-700/40">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <p className="text-xs text-primary-300 font-semibold uppercase tracking-wider mb-1">Next Step</p>
              <h3 className="text-lg font-bold text-white">{STEPS[activeStep].label}</h3>
              <p className="text-sm text-slate-400 mt-0.5">{STEPS[activeStep].desc}</p>
            </div>
            <Link to={stepHrefs[activeStep]} className="btn-primary shrink-0">
              Continue →
            </Link>
          </div>
        </div>
      )}

      {/* Quick stats */}
      {progress.hasResults && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
          {[
            { label: 'Assessment', value: 'Complete', color: 'text-emerald-400' },
            { label: 'Skills rated', value: '10+', color: 'text-primary-400' },
            { label: 'Top careers', value: '10', color: 'text-yellow-400' },
            { label: 'Booking', value: 'Available', color: 'text-accent-400' },
          ].map((stat) => (
            <div key={stat.label} className="card-sm text-center">
              <p className={`text-xl font-bold ${stat.color}`}>{stat.value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{stat.label}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
