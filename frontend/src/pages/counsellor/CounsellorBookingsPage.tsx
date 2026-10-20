import React, { useEffect, useState } from 'react';
import { booking as bookingApi } from '../../api/client';
import { PageSpinner, Alert, EmptyState, Modal } from '../../components/ui';
import type { BookingOut, AssessmentOut } from '../../types';
import clsx from 'clsx';

export default function CounsellorBookingsPage() {
  const [bookings, setBookings] = useState<BookingOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Session notes
  const [noteBookingId, setNoteBookingId] = useState<string | null>(null);
  const [noteText, setNoteText] = useState('');
  const [savingNote, setSavingNote] = useState(false);

  // Student results
  const [resultsBookingId, setResultsBookingId] = useState<string | null>(null);
  const [studentResults, setStudentResults] = useState<AssessmentOut | null>(null);
  const [loadingResults, setLoadingResults] = useState(false);
  const [resultsError, setResultsError] = useState('');

  useEffect(() => {
    loadBookings();
  }, []);

  async function loadBookings() {
    setLoading(true);
    try {
      setBookings(await bookingApi.listBookings());
    } catch (err: unknown) {
      setError((err as Error).message ?? 'Failed to load bookings');
    } finally {
      setLoading(false);
    }
  }

  const handleSaveNote = async () => {
    if (!noteBookingId || !noteText.trim()) return;
    setSavingNote(true);
    try {
      await bookingApi.createNote(noteBookingId, noteText);
      setNoteBookingId(null);
      setNoteText('');
      alert('Notes saved!');
    } catch (err: unknown) {
      setError((err as Error).message ?? 'Failed to save notes');
    } finally {
      setSavingNote(false);
    }
  };

  const handleViewResults = async (bookingId: string) => {
    setResultsBookingId(bookingId);
    setLoadingResults(true);
    setResultsError('');
    setStudentResults(null);
    try {
      const results = await bookingApi.getStudentResults(bookingId);
      setStudentResults(results);
    } catch (err: unknown) {
      const msg = (err as Error).message ?? 'Failed to load results';
      setResultsError(msg.includes('403') || msg.includes('consent')
        ? 'Student has not shared results for this booking.'
        : msg);
    } finally {
      setLoadingResults(false);
    }
  };

  const RIASEC_KEYS = ['realistic', 'investigative', 'artistic', 'social', 'enterprising', 'conventional'] as const;

  if (loading) return <PageSpinner />;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
      <h1 className="page-title mb-2">Student Bookings</h1>
      <p className="page-subtitle mb-8">View your upcoming sessions and student results (with consent).</p>

      {error && <Alert type="error" onClose={() => setError('')} className="mb-4">{error}</Alert>}

      {bookings.length === 0 ? (
        <EmptyState
          title="No bookings yet"
          description="Students will appear here once they book one of your slots."
        />
      ) : (
        <div className="space-y-4">
          {bookings.map((b) => (
            <div key={b.id} className="card">
              <div className="flex items-start justify-between flex-wrap gap-4">
                <div>
                  <p className="font-semibold text-white">{b.student_name ?? 'Student'}</p>
                  <p className="text-sm text-slate-400 mt-1">
                    {b.start_time ? new Date(b.start_time).toLocaleString('en-MY', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Time TBD'}
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className={clsx('badge', b.status === 'confirmed' ? 'badge-green' : b.status === 'cancelled' ? 'badge-red' : 'badge-slate')}>
                      {b.status}
                    </span>
                    <span className={clsx('badge', b.consent_granted ? 'badge-primary' : 'badge-slate')}>
                      {b.consent_granted ? '🔓 Results shared' : '🔒 Results private'}
                    </span>
                  </div>
                </div>

                {b.status !== 'cancelled' && (
                  <div className="flex items-center gap-2 flex-wrap">
                    <button
                      onClick={() => handleViewResults(b.id)}
                      disabled={!b.consent_granted}
                      title={!b.consent_granted ? 'Student has not granted consent' : 'View student results'}
                      className={clsx('btn-secondary text-xs', !b.consent_granted && 'opacity-40 cursor-not-allowed')}
                    >
                      View Results
                    </button>
                    <button
                      onClick={() => { setNoteBookingId(b.id); setNoteText(''); }}
                      className="btn-primary text-xs"
                    >
                      + Add Notes
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Session Notes Modal */}
      <Modal
        open={!!noteBookingId}
        onClose={() => setNoteBookingId(null)}
        title="Session Notes"
        size="md"
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-400">Record your notes for this session.</p>
          <textarea
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            rows={6}
            className="input resize-none"
            placeholder="Write your session notes here…"
          />
          <div className="flex gap-3 justify-end">
            <button onClick={() => setNoteBookingId(null)} className="btn-secondary">Cancel</button>
            <button onClick={handleSaveNote} disabled={savingNote || !noteText.trim()} className="btn-primary">
              {savingNote ? <><span className="spinner h-4 w-4" /> Saving…</> : 'Save Notes'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Student Results Modal */}
      <Modal
        open={!!resultsBookingId}
        onClose={() => { setResultsBookingId(null); setStudentResults(null); }}
        title="Student Assessment Results"
        size="md"
      >
        {loadingResults ? (
          <div className="flex justify-center py-8"><span className="spinner h-8 w-8" /></div>
        ) : resultsError ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-3">🔒</div>
            <p className="font-medium text-slate-300">Results Not Available</p>
            <p className="text-sm text-slate-500 mt-1">{resultsError}</p>
          </div>
        ) : studentResults?.riasec_score ? (
          <div className="space-y-4">
            <p className="text-sm text-slate-400">Assessment completed on {new Date(studentResults.completed_at!).toLocaleDateString()}</p>
            <div className="grid grid-cols-2 gap-3">
              {RIASEC_KEYS.map((key) => (
                <div key={key} className="card-sm">
                  <p className="text-xs text-slate-500 capitalize mb-1">{key}</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-surface-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary-600 rounded-full"
                        style={{ width: `${studentResults.riasec_score![key as keyof typeof studentResults.riasec_score]}%` }}
                      />
                    </div>
                    <span className="text-sm font-bold text-primary-400">
                      {Math.round(studentResults.riasec_score![key as keyof typeof studentResults.riasec_score] as number)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </Modal>
    </div>
  );
}
