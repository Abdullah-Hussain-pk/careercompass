import React, { useState, useEffect, useRef } from 'react';
import { booking as bookingApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { NotificationOut } from '../types';

export default function NotificationBell() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<NotificationOut[]>([]);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const unread = notifications.filter((n) => !n.is_read).length;

  useEffect(() => {
    if (!user) return;
    bookingApi.getNotifications().then(setNotifications).catch(() => {});
    const interval = setInterval(() => {
      bookingApi.getNotifications().then(setNotifications).catch(() => {});
    }, 30_000);
    return () => clearInterval(interval);
  }, [user]);

  const markRead = async (id: string) => {
    try {
      await bookingApi.markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)),
      );
    } catch {
      // Marking as read is best-effort; the list refreshes on the next poll.
    }
  };

  return (
    <div className="relative" ref={ref}>
      <button
        id="notification-bell"
        onClick={() => setOpen((o) => !o)}
        className="relative p-2 rounded-lg text-slate-400 hover:text-white hover:bg-surface-800 transition-colors"
        aria-label={`Notifications${unread > 0 ? ` (${unread} unread)` : ''}`}
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unread > 0 && (
          <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 rounded-full text-xs text-white flex items-center justify-center font-bold leading-none">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 mt-1 w-80 bg-surface-800 border border-slate-700 rounded-xl shadow-2xl z-20 overflow-hidden animate-fade-in">
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
              <h3 className="text-sm font-semibold text-white">Notifications</h3>
              {unread > 0 && (
                <span className="badge-red">{unread} new</span>
              )}
            </div>
            <div className="max-h-80 overflow-y-auto">
              {notifications.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-8">No notifications</p>
              ) : (
                notifications.map((n) => (
                  <div
                    key={n.id}
                    className={`px-4 py-3 border-b border-slate-700/50 cursor-pointer hover:bg-surface-700 transition-colors ${!n.is_read ? 'bg-primary-900/20' : ''}`}
                    onClick={() => markRead(n.id)}
                  >
                    <p className="text-sm text-slate-300 leading-snug">{n.message}</p>
                    <p className="text-xs text-slate-500 mt-1">
                      {new Date(n.created_at).toLocaleString()}
                      {!n.is_read && (
                        <span className="ml-2 w-1.5 h-1.5 rounded-full bg-primary-400 inline-block align-middle" />
                      )}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
