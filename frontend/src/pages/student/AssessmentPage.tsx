import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { assessment as assessmentApi } from '../../api/client';
import { PageSpinner, ErrorMessage, Alert } from '../../components/ui';
import type { RIASECQuestionOut, AnswerItem } from '../../types';
import clsx from 'clsx';

const PAGE_SIZE = 6;

const LABELS = ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'];

export default function AssessmentPage() {
  const navigate = useNavigate();
  const [questions, setQuestions] = useState<RIASECQuestionOut[]>([]);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [currentPage, setCurrentPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);

  const totalPages = Math.ceil(questions.length / PAGE_SIZE);
  const pageQuestions = questions.slice(
    currentPage * PAGE_SIZE,
    (currentPage + 1) * PAGE_SIZE,
  );
  const answeredCount = Object.keys(answers).length;
  const progressPct = questions.length > 0 ? (answeredCount / questions.length) * 100 : 0;
  const currentPageAnswered = pageQuestions.every((q) => answers[q.id] !== undefined);

  useEffect(() => {
    async function init() {
      try {
        const [qs, prog] = await Promise.all([
          assessmentApi.getQuestions(),
          assessmentApi.getProgress(),
        ]);
        setQuestions(qs);
        if (prog.saved_answers) {
          setAnswers(prog.saved_answers as Record<string, number>);
          // Resume: jump to first incomplete page
          const firstUnanswered = qs.findIndex((q) => !(q.id in (prog.saved_answers ?? {})));
          if (firstUnanswered !== -1) {
            setCurrentPage(Math.floor(firstUnanswered / PAGE_SIZE));
          }
        }
        // Start session if needed
        if (!prog.assessment_id) {
          await assessmentApi.startAssessment();
        }
      } catch (err: unknown) {
        setError((err as Error).message ?? 'Failed to load questions');
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  const setAnswer = (questionId: string, val: number) => {
    setAnswers((prev) => ({ ...prev, [questionId]: val }));
    setSaveSuccess(false);
  };

  const saveProgress = useCallback(async () => {
    const items: AnswerItem[] = Object.entries(answers).map(([question_id, answer]) => ({
      question_id,
      answer,
    }));
    if (items.length === 0) return;
    setSaving(true);
    try {
      await assessmentApi.saveProgress(items);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch {
      // silently ignore save errors
    } finally {
      setSaving(false);
    }
  }, [answers]);

  const handleNext = async () => {
    await saveProgress();
    setCurrentPage((p) => Math.min(p + 1, totalPages - 1));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handlePrev = () => {
    setCurrentPage((p) => Math.max(p - 1, 0));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSubmit = async () => {
    if (answeredCount < 48) {
      setError(`Please answer all 48 questions. You have ${answeredCount}/48 answered.`);
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      const items: AnswerItem[] = Object.entries(answers).map(([question_id, answer]) => ({
        question_id,
        answer,
      }));
      await assessmentApi.submitAssessment(items);
      navigate('/assessment/skills');
    } catch (err: unknown) {
      setError((err as Error).message ?? 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <PageSpinner />;
  if (error && questions.length === 0) return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <ErrorMessage message={error} onRetry={() => window.location.reload()} />
    </div>
  );

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-10">
      {/* Header */}
      <div className="mb-6">
        <h1 className="page-title">RIASEC Interest Test</h1>
        <p className="page-subtitle">
          Rate how much each statement applies to you on a scale of 1–5.
        </p>
      </div>

      {/* Progress */}
      <div className="mb-8">
        <div className="flex items-center justify-between text-sm mb-2">
          <span className="text-slate-400">
            {answeredCount} / {questions.length} answered
          </span>
          <span className="text-slate-400">
            Page {currentPage + 1} of {totalPages}
          </span>
        </div>
        <div className="h-2 bg-surface-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary-600 to-primary-400 rounded-full transition-all duration-500"
            style={{ width: `${progressPct}%` }}
          />
        </div>
        {saveSuccess && (
          <p className="text-xs text-emerald-400 mt-1.5">✓ Progress saved</p>
        )}
      </div>

      {/* Error */}
      {error && (
        <Alert type="error" onClose={() => setError('')} className="mb-6">
          {error}
        </Alert>
      )}

      {/* Questions */}
      <div className="space-y-4">
        {pageQuestions.map((q, idx) => (
          <QuestionCard
            key={q.id}
            question={q}
            index={currentPage * PAGE_SIZE + idx + 1}
            value={answers[q.id]}
            onChange={(val) => setAnswer(q.id, val)}
          />
        ))}
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between mt-8 pt-6 border-t border-slate-700/50">
        <button
          onClick={handlePrev}
          disabled={currentPage === 0}
          className="btn-secondary"
        >
          ← Previous
        </button>

        <div className="flex items-center gap-2">
          {Array.from({ length: totalPages }, (_, i) => (
            <button
              key={i}
              onClick={() => setCurrentPage(i)}
              className={clsx(
                'w-2 h-2 rounded-full transition-all',
                i === currentPage ? 'bg-primary-500 w-4' : 'bg-slate-600 hover:bg-slate-400',
              )}
              aria-label={`Go to page ${i + 1}`}
            />
          ))}
        </div>

        {currentPage < totalPages - 1 ? (
          <button
            onClick={handleNext}
            disabled={!currentPageAnswered || saving}
            className="btn-primary"
          >
            {saving ? <span className="spinner h-4 w-4" /> : 'Next →'}
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={answeredCount < 48 || submitting}
            className="btn-primary"
          >
            {submitting ? (
              <><span className="spinner h-4 w-4" /> Submitting…</>
            ) : (
              'Submit Test 🎉'
            )}
          </button>
        )}
      </div>
    </div>
  );
}

function QuestionCard({
  question,
  index,
  value,
  onChange,
}: {
  question: RIASECQuestionOut;
  index: number;
  value: number | undefined;
  onChange: (val: number) => void;
}) {
  const typeColors: Record<string, string> = {
    R: 'text-orange-400 bg-orange-900/30',
    I: 'text-blue-400 bg-blue-900/30',
    A: 'text-purple-400 bg-purple-900/30',
    S: 'text-emerald-400 bg-emerald-900/30',
    E: 'text-yellow-400 bg-yellow-900/30',
    C: 'text-cyan-400 bg-cyan-900/30',
  };

  return (
    <div className={clsx('card transition-all', value ? 'border-primary-700/40' : '')}>
      <div className="flex items-start justify-between gap-3 mb-5">
        <p className="text-slate-200 text-sm leading-relaxed flex-1">
          <span className="text-slate-500 text-xs mr-2">Q{index}.</span>
          {question.question_text}
        </p>
        <span
          className={clsx(
            'shrink-0 text-xs font-bold px-2 py-0.5 rounded-full',
            typeColors[question.riasec_type] ?? 'text-slate-400 bg-slate-800',
          )}
        >
          {question.riasec_type}
        </span>
      </div>

      {/* Rating buttons */}
      <div className="flex gap-2" role="group" aria-label={`Rating for question ${index}`}>
        {[1, 2, 3, 4, 5].map((val) => (
          <button
            key={val}
            onClick={() => onChange(val)}
            aria-label={`${val} – ${LABELS[val - 1]}`}
            className={clsx(
              'flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all border focus:outline-none focus:ring-2 focus:ring-primary-500',
              value === val
                ? 'bg-primary-600 border-primary-500 text-white'
                : 'bg-surface-900 border-slate-700 text-slate-400 hover:border-primary-600 hover:text-white',
            )}
          >
            {val}
          </button>
        ))}
      </div>
      <div className="flex justify-between text-xs text-slate-600 mt-1.5">
        <span>Strongly Disagree</span>
        <span>Strongly Agree</span>
      </div>
    </div>
  );
}
