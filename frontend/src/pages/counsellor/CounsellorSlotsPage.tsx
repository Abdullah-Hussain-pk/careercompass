import React, { useEffect, useState } from 'react';
import { booking as bookingApi } from '../../api/client';
import { PageSpinner, ErrorMessage, Alert, EmptyState, ConfirmDialog } from '../../components/ui';
import type { SlotOut } from '../../types';
import clsx from 'clsx';

export default function CounsellorSlotsPage() {
  const [slots, setSlots] = useState<SlotOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [creating, setCreating] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  // New slot form
  const [startTime, setStartTime] = useState('');

  useEffect(() => {
    loadSlots();
  }, []);

  async function loadSlots() {
    setLoading(true);
    try {
      setSlots(await bookingApi.getMySlots());
    } catch (err: unknown) {
      setError((err as Error).message ?? 'Failed to load slots');
    } finally {
      setLoading(false);
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!startTime) return;
    setCreating(true);
    setError('');
    try {
      await bookingApi.createSlot(new Date(startTime).toISOString());
      setSuccess('Slot created successfully!');
      setStartTime('');
      setTimeout(() => setSuccess(''), 3000);
      await loadSlots();
    } catch (err: unknown) {
      setError((err as Error).message ?? 'Failed to create slot');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await bookingApi.deleteSlot(deleteTarget);
      await loadSlots();
    } catch (err: unknown) {
      setError((err as Error).message ?? 'Failed to delete slot');
    } finally {
      setDeleting(false);
      setDeleteTarget(null);
    }
  };

  if (loading) return <PageSpinner />;

  const upcomingSlots = slots.filter((s) => new Date(s.start_time) > new Date());
  const pastSlots = slots.filter((s) => new Date(s.start_time) <= new Date());

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
      <h1 className="page-title mb-2">Manage Availability</h1>
      <p className="page-subtitle mb-8">Create 30-minute slots for student bookings.</p>

      {error && <Alert type="error" onClose={() => setError('')} className="mb-4">{error}</Alert>}
      {success && <Alert type="success" onClose={() => setSuccess('')} className="mb-4">{success}</Alert>}

      {/* Create slot form */}
      <div className="card mb-8">
        <h2 className="section-title mb-4">Add New Slot</h2>
        <form onSubmit={handleCreate} className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-48">
            <label htmlFor="slot-time" className="label">Start Time</label>
            <input
              id="slot-time"
              type="datetime-local"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              required
              min={new Date().toISOString().slice(0, 16)}
              className="input"
            />
            <p className="text-xs text-slate-500 mt-1">Session duration is automatically 30 minutes.</p>
          </div>
          <button type="submit" disabled={creating || !startTime} className="btn-primary">
            {creating ? <><span className="spinner h-4 w-4" /> Creating…</> : '+ Add Slot'}
          </button>
        </form>
      </div>

      {/* Upcoming slots */}
      <div className="mb-8">
        <h2 className="section-title mb-4">Upcoming Slots ({upcomingSlots.length})</h2>
        {upcomingSlots.length === 0 ? (
          <EmptyState title="No upcoming slots" description="Create your first availability slot above." />
        ) : (
          <div className="space-y-2">
            {upcomingSlots.map((slot) => (
              <div key={slot.id} className="card-sm flex items-center justify-between flex-wrap gap-3">
                <div>
                  <p className="font-medium text-white text-sm">
                    {new Date(slot.start_time).toLocaleDateString('en-MY', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {new Date(slot.start_time).toLocaleTimeString('en-MY', { hour: '2-digit', minute: '2-digit' })} –{' '}
                    {new Date(slot.end_time).toLocaleTimeString('en-MY', { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={clsx('badge', slot.is_booked ? 'badge-primary' : 'badge-green')}>
                    {slot.is_booked ? 'Booked' : 'Available'}
                  </span>
                  {!slot.is_booked && (
                    <button
                      onClick={() => setDeleteTarget(slot.id)}
                      className="text-xs text-red-400 hover:text-red-300"
                    >
                      Delete
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Past slots */}
      {pastSlots.length > 0 && (
        <div>
          <h2 className="section-title mb-4 text-slate-500">Past Slots</h2>
          <div className="space-y-2 opacity-50">
            {pastSlots.slice(0, 5).map((slot) => (
              <div key={slot.id} className="card-sm flex items-center justify-between">
                <p className="text-sm text-slate-400">
                  {new Date(slot.start_time).toLocaleDateString('en-MY')} · {new Date(slot.start_time).toLocaleTimeString('en-MY', { hour: '2-digit', minute: '2-digit' })}
                </p>
                <span className={clsx('badge', slot.is_booked ? 'badge-slate' : 'badge-slate')}>
                  {slot.is_booked ? 'Was booked' : 'Unused'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Slot"
        description="Are you sure you want to delete this availability slot?"
        confirmLabel={deleting ? 'Deleting…' : 'Delete Slot'}
        danger
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
