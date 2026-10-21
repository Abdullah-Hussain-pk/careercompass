import React, { useEffect, useState } from 'react';
import { booking as bookingApi } from '../../api/client';
import { PageSpinner, EmptyState, Alert, ConfirmDialog } from '../../components/ui';
import type { SlotWithCounsellorOut, BookingOut } from '../../types';
import clsx from 'clsx';

type Step = 1 | 2 | 3 | 4;

export default function BookingPage() {
  const [slots, setSlots] = useState<SlotWithCounsellorOut[]>([]);
  const [bookings, setBookings] = useState<BookingOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Booking flow state
  const [step, setStep] = useState<Step>(1);
  const [selectedSlot, setSelectedSlot] = useState<SlotWithCounsellorOut | null>(null);
  const [grantConsent, setGrantConsent] = useState(false);
  const [booking, setBooking] = useState(false);
  const [bookingSuccess, setBookingSuccess] = useState<BookingOut | null>(null);

  // Cancel state
  const [cancelTarget, setCancelTarget] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);

  // Group slots by counsellor
  const counsellors = React.useMemo(() => {
    const map = new Map<string, { name: string; slots: SlotWithCounsellorOut[] }>();
    slots.forEach((s) => {
      if (!map.has(s.counsellor_id)) {
        map.set(s.counsellor_id, { name: s.counsellor_name, slots: [] });
      }
      map.get(s.counsellor_id)!.slots.push(s);
    });
    return Array.from(map.entries()).map(([id, val]) => ({ id, ...val }));
  }, [slots]);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [slotsData, bookingsData] = await Promise.all([
        bookingApi.listAvailableSlots(),
        bookingApi.listBookings(),
      ]);
      setSlots(slotsData);
      setBookings(bookingsData);
    } catch (err: unknown) {
      setError((err as Error).message ?? 'Failed to load booking data');
    } finally {
      setLoading(false);
    }
  }

  const handleBook = async () => {
    if (!selectedSlot) return;
    setBooking(true);
    setError('');
    try {
      const result = await bookingApi.createBooking(selectedSlot.id, grantConsent);
      setBookingSuccess(result);
      setStep(4);
      await loadData();
    } catch (err: unknown) {
      setError((err as Error).message ?? 'Booking failed');
    } finally {
      setBooking(false);
    }
  };

  const handleCancel = async () => {
    if (!cancelTarget) return;
    setCancelling(true);
    try {
      await bookingApi.cancelBooking(cancelTarget);
      await loadData();
    } catch (err: unknown) {
      setError((err as Error).message ?? 'Cancellation failed');
    } finally {
      setCancelling(false);
      setCancelTarget(null);
    }
  };

  const handleConsentToggle = async (bookingId: string, granted: boolean) => {
    try {
      await bookingApi.updateConsent(bookingId, granted);
      setBookings((prev) =>
        prev.map((b) => (b.id === bookingId ? { ...b, consent_granted: granted } : b)),
      );
    } catch (err: unknown) {
      setError((err as Error).message ?? 'Failed to update consent');
    }
  };

  const resetFlow = () => {
    setStep(1);
    setSelectedSlot(null);
    setGrantConsent(false);
    setBookingSuccess(null);
    setError('');
  };

  if (loading) return <PageSpinner />;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
      <h1 className="page-title mb-2">Book a Counsellor Session</h1>
      <p className="page-subtitle mb-8">
        Connect with a professional career counsellor for personalised guidance.
      </p>

      {error && <Alert type="error" onClose={() => setError('')} className="mb-6">{error}</Alert>}

      {/* Booking flow */}
      <div className="card mb-10">
        {/* Step indicators */}
        <div className="flex items-center justify-between mb-8">
          {(['Pick Slot', 'Confirm', 'Consent', 'Done'] as const).map((label, i) => {
            const stepNum = (i + 1) as Step;
            return (
              <React.Fragment key={label}>
                <div className="flex flex-col items-center gap-1">
                  <div
                    className={clsx(
                      'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-all',
                      step > stepNum ? 'bg-emerald-600 border-emerald-500 text-white'
                        : step === stepNum ? 'bg-primary-700 border-primary-500 text-white'
                          : 'bg-surface-900 border-slate-600 text-slate-600',
                    )}
                  >
                    {step > stepNum ? '✓' : stepNum}
                  </div>
                  <span className={clsx('text-xs hidden sm:block', step === stepNum ? 'text-white' : 'text-slate-500')}>
                    {label}
                  </span>
                </div>
                {i < 3 && <div className={clsx('flex-1 h-0.5 mx-2', step > stepNum ? 'bg-emerald-600' : 'bg-slate-700')} />}
              </React.Fragment>
            );
          })}
        </div>

        {/* Step 1: Pick slot */}
        {step === 1 && (
          <div>
            <h2 className="section-title mb-4">Choose a Time Slot</h2>
            {counsellors.length === 0 ? (
              <EmptyState
                title="No slots available"
                description="No counsellors have posted available time slots yet. Check back soon."
              />
            ) : (
              <div className="space-y-6">
                {counsellors.map((c) => (
                  <div key={c.id}>
                    <h3 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
                      <div className="w-7 h-7 rounded-full bg-emerald-800 flex items-center justify-center text-xs font-bold text-emerald-300">
                        {c.name.charAt(0)}
                      </div>
                      {c.name}
                    </h3>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                      {c.slots.map((slot) => (
                        <button
                          key={slot.id}
                          onClick={() => {
                            setSelectedSlot(slot);
                            setStep(2);
                          }}
                          className={clsx(
                            'p-3 rounded-lg border text-left text-sm transition-all',
                            selectedSlot?.id === slot.id
                              ? 'border-primary-500 bg-primary-900/30 text-white'
                              : 'border-slate-700 hover:border-primary-600 text-slate-300 hover:text-white',
                          )}
                        >
                          <p className="font-medium">{new Date(slot.start_time).toLocaleDateString('en-MY', { weekday: 'short', month: 'short', day: 'numeric' })}</p>
                          <p className="text-slate-500 text-xs mt-0.5">
                            {new Date(slot.start_time).toLocaleTimeString('en-MY', { hour: '2-digit', minute: '2-digit' })} –{' '}
                            {new Date(slot.end_time).toLocaleTimeString('en-MY', { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Step 2: Confirm */}
        {step === 2 && selectedSlot && (
          <div>
            <h2 className="section-title mb-4">Confirm Your Booking</h2>
            <div className="rounded-xl border border-slate-700 bg-surface-900 p-4 mb-6 space-y-2">
              <p className="text-sm text-slate-400">Counsellor: <span className="text-white font-medium">{selectedSlot.counsellor_name}</span></p>
              <p className="text-sm text-slate-400">Date: <span className="text-white font-medium">{new Date(selectedSlot.start_time).toLocaleDateString('en-MY', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span></p>
              <p className="text-sm text-slate-400">Time: <span className="text-white font-medium">{new Date(selectedSlot.start_time).toLocaleTimeString('en-MY', { hour: '2-digit', minute: '2-digit' })} – {new Date(selectedSlot.end_time).toLocaleTimeString('en-MY', { hour: '2-digit', minute: '2-digit' })}</span></p>
              <p className="text-sm text-slate-400">Duration: <span className="text-white font-medium">30 minutes</span></p>
            </div>
            <div className="flex gap-3">
              <button onClick={() => setStep(1)} className="btn-secondary">← Back</button>
              <button onClick={() => setStep(3)} className="btn-primary">Continue →</button>
            </div>
          </div>
        )}

        {/* Step 3: Consent */}
        {step === 3 && (
          <div>
            <h2 className="section-title mb-2">Share Your Results?</h2>
            <p className="text-sm text-slate-400 mb-6">
              You can optionally allow the counsellor to view your RIASEC assessment results and recommendations.
              This helps them provide more tailored advice. You can change this at any time.
            </p>
            <div
              onClick={() => setGrantConsent((v) => !v)}
              className={clsx(
                'flex items-start gap-4 p-4 rounded-xl border cursor-pointer transition-all mb-6',
                grantConsent ? 'border-primary-600 bg-primary-900/20' : 'border-slate-700 hover:border-slate-500',
              )}
            >
              <div className={clsx('w-5 h-5 rounded border-2 shrink-0 mt-0.5 transition-all flex items-center justify-center', grantConsent ? 'bg-primary-600 border-primary-500' : 'border-slate-500')}>
                {grantConsent && <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
              </div>
              <div>
                <p className="text-sm font-medium text-white">Share my assessment results with the counsellor</p>
                <p className="text-xs text-slate-500 mt-0.5">The counsellor will be able to view your RIASEC scores and career recommendations for this session only.</p>
              </div>
            </div>
            <div className="flex gap-3">
              <button onClick={() => setStep(2)} className="btn-secondary">← Back</button>
              <button onClick={handleBook} disabled={booking} className="btn-primary">
                {booking ? <><span className="spinner h-4 w-4" /> Booking…</> : 'Confirm Booking →'}
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Done */}
        {step === 4 && bookingSuccess && (
          <div className="text-center py-4">
            <div className="w-16 h-16 rounded-full bg-emerald-700 flex items-center justify-center mx-auto mb-4 text-3xl">✓</div>
            <h2 className="text-xl font-bold text-white mb-2">Booking Confirmed!</h2>
            <p className="text-slate-400 text-sm mb-1">
              Session with counsellor on{' '}
              <strong className="text-white">
                {bookingSuccess.start_time
                  ? new Date(bookingSuccess.start_time).toLocaleString('en-MY')
                  : 'TBD'}
              </strong>
            </p>
            <p className="text-xs text-slate-500 mb-6">You'll receive a notification reminder before your session.</p>
            <button onClick={resetFlow} className="btn-secondary">Book Another →</button>
          </div>
        )}
      </div>

      {/* Existing bookings */}
      <div>
        <h2 className="section-title mb-4">Your Bookings</h2>
        {bookings.length === 0 ? (
          <EmptyState title="No bookings yet" description="Book your first counsellor session above." />
        ) : (
          <div className="space-y-3">
            {bookings.map((b) => (
              <div key={b.id} className="card-sm">
                <div className="flex items-start justify-between flex-wrap gap-3">
                  <div>
                    <p className="font-medium text-white text-sm">
                      {b.counsellor_name ?? 'Counsellor'}
                    </p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {b.start_time ? new Date(b.start_time).toLocaleString('en-MY') : 'Time TBD'}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className={clsx('badge', b.status === 'confirmed' ? 'badge-green' : b.status === 'cancelled' ? 'badge-red' : 'badge-slate')}>
                        {b.status}
                      </span>
                      {b.consent_granted !== null && (
                        <span className={clsx('badge', b.consent_granted ? 'badge-primary' : 'badge-slate')}>
                          {b.consent_granted ? 'Results shared' : 'Results private'}
                        </span>
                      )}
                    </div>
                  </div>

                  {b.status !== 'cancelled' && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleConsentToggle(b.id, !b.consent_granted)}
                        className="text-xs btn-ghost px-2 py-1"
                      >
                        {b.consent_granted ? 'Revoke consent' : 'Grant consent'}
                      </button>
                      <button
                        onClick={() => setCancelTarget(b.id)}
                        className="text-xs text-red-400 hover:text-red-300 px-2 py-1"
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <ConfirmDialog
        open={!!cancelTarget}
        title="Cancel Booking"
        description="Are you sure you want to cancel this booking? This action cannot be undone."
        confirmLabel={cancelling ? 'Cancelling…' : 'Yes, cancel'}
        danger
        onConfirm={handleCancel}
        onCancel={() => setCancelTarget(null)}
      />
    </div>
  );
}
