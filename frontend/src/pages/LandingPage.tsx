import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const FEATURES = [
  {
    icon: '🧠',
    title: 'RIASEC Interest Test',
    description:
      'Complete our 48-question psychometric assessment to discover your personality-based career interests across 6 dimensions.',
  },
  {
    icon: '📊',
    title: 'Skill Gap Analysis',
    description:
      'See exactly which skills you need for each career, and get a personalised learning roadmap with curated resources.',
  },
  {
    icon: '🤖',
    title: 'AI-Powered Recommendations',
    description:
      'Our hybrid recommender engine matches you to top careers using your interests, skills, and academic background.',
  },
  {
    icon: '🗓️',
    title: 'Counsellor Booking',
    description:
      'Book 1-on-1 sessions with professional career counsellors. You control what they can see about your results.',
  },
  {
    icon: '💡',
    title: 'Explainable Results',
    description:
      'Every recommendation comes with 3 plain-language reasons and visual breakdowns — no black-box decisions.',
  },
  {
    icon: '🔒',
    title: 'Privacy First',
    description:
      'Consent-based data sharing. Delete your account and all data at any time. Built for Malaysian students.',
  },
];

const STEPS = [
  { step: '1', label: 'Create account', desc: 'Free signup in under a minute' },
  { step: '2', label: 'Take the RIASEC test', desc: '48 questions, ~15 minutes' },
  { step: '3', label: 'Rate your skills', desc: 'At least 10 skills from our library' },
  { step: '4', label: 'Get recommendations', desc: 'Your top 10 careers, explained' },
  { step: '5', label: 'Book a counsellor', desc: 'Optional — share results with consent' },
];

export default function LandingPage() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-950 via-surface-900 to-surface-950" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-primary-800/20 via-transparent to-transparent" />
        <div className="relative max-w-5xl mx-auto px-4 sm:px-6 py-20 lg:py-32 text-center">
          <div className="inline-flex items-center gap-2 bg-primary-900/40 border border-primary-700/40 rounded-full px-4 py-1.5 text-primary-300 text-xs font-medium mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-primary-400 animate-pulse" />
            Guidance only — not a final decision. Always talk to a counsellor.
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white leading-tight mb-6">
            Discover Your{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-400 to-accent-400">
              Ideal Career
            </span>{' '}
            Path
          </h1>
          <p className="text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            CareerCompass combines a psychometric interest test, skill-gap analysis, and an
            explainable AI recommender to help Pakistani students navigate their future with confidence.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            {user ? (
              <Link to="/dashboard" className="btn-primary text-base px-8 py-3">
                Go to Dashboard →
              </Link>
            ) : (
              <>
                <Link to="/register" className="btn-primary text-base px-8 py-3 shadow-lg shadow-primary-900/50">
                  Get Started Free
                </Link>
                <Link to="/login" className="btn-secondary text-base px-8 py-3">
                  Sign In
                </Link>
              </>
            )}
          </div>
          <p className="mt-4 text-xs text-slate-600">
            This tool provides guidance only. Career decisions should involve a qualified counsellor.
          </p>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-20">
        <div className="text-center mb-14">
          <h2 className="text-3xl font-bold text-white mb-3">Everything you need</h2>
          <p className="text-slate-400 max-w-xl mx-auto">
            A complete career exploration platform — from discovery to action.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="card hover:border-primary-700/60 hover:bg-surface-700/50 transition-all duration-300 group"
            >
              <div className="text-3xl mb-4">{f.icon}</div>
              <h3 className="text-base font-semibold text-white mb-2 group-hover:text-primary-300 transition-colors">
                {f.title}
              </h3>
              <p className="text-sm text-slate-400 leading-relaxed">{f.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="bg-surface-800/40 border-y border-slate-700/30">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-20">
          <h2 className="text-3xl font-bold text-white text-center mb-12">How it works</h2>
          <div className="space-y-4">
            {STEPS.map((s, i) => (
              <div key={i} className="flex items-start gap-5">
                <div className="w-10 h-10 rounded-full bg-primary-700 flex items-center justify-center text-white font-bold shrink-0 shadow-lg shadow-primary-900/50">
                  {s.step}
                </div>
                <div>
                  <p className="font-semibold text-white">{s.label}</p>
                  <p className="text-sm text-slate-400">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
          {!user && (
            <div className="text-center mt-12">
              <Link to="/register" className="btn-primary text-base px-8 py-3">
                Start Your Journey
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* Disclaimer */}
      <section className="max-w-3xl mx-auto px-4 sm:px-6 py-14 text-center">
        <div className="card border-yellow-700/30 bg-yellow-900/10">
          <h3 className="text-base font-semibold text-yellow-300 mb-2">⚠️ Important Disclaimer</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            CareerCompass provides <strong className="text-slate-300">guidance only</strong> and does not
            constitute professional career advice. All recommendations are based on self-reported data and
            algorithmic matching. Results should be used as a starting point for exploration — not as a final
            decision. We strongly encourage you to{' '}
            <strong className="text-slate-300">consult a qualified career counsellor</strong> before making
            major academic or career decisions.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-8">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-500">
          <span>© 2026 CareerCompass. All rights reserved.</span>
          <div className="flex gap-6">
            <Link to="/privacy" className="hover:text-slate-300">Privacy Policy</Link>
            <Link to="/disclaimer" className="hover:text-slate-300">Disclaimer</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
