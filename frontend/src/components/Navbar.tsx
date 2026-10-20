import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import NotificationBell from './NotificationBell';
import clsx from 'clsx';

const NAV_LINKS: Record<string, { label: string; href: string }[]> = {
  student: [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Assessment', href: '/assessment' },
    { label: 'Results', href: '/results' },
    { label: 'Book Session', href: '/booking' },
  ],
  counsellor: [
    { label: 'My Slots', href: '/counsellor/slots' },
    { label: 'Bookings', href: '/counsellor/bookings' },
  ],
  admin: [
    { label: 'Analytics', href: '/admin/analytics' },
    { label: 'Careers', href: '/admin/careers' },
    { label: 'Users', href: '/admin/users' },
    { label: 'Weights', href: '/admin/weights' },
    { label: 'Submissions', href: '/admin/submissions' },
    { label: 'Evaluation', href: '/admin/evaluation' },
  ],
  expert: [
    { label: 'Submit Update', href: '/expert/submit' },
    { label: 'My Submissions', href: '/expert/submissions' },
  ],
};

export default function Navbar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = React.useState(false);

  const links = user ? NAV_LINKS[user.role] ?? [] : [];

  const roleColor: Record<string, string> = {
    student: 'text-primary-400',
    counsellor: 'text-emerald-400',
    admin: 'text-red-400',
    expert: 'text-yellow-400',
  };

  return (
    <nav className="sticky top-0 z-50 bg-surface-900/80 backdrop-blur border-b border-slate-700/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link
            to="/"
            className="flex items-center gap-2.5 font-bold text-white hover:text-primary-400 transition-colors"
          >
            <span className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center text-white text-lg font-black">
              C
            </span>
            <span className="hidden sm:block text-lg">CareerCompass</span>
          </Link>

          {/* Desktop Nav Links */}
          {user && (
            <div className="hidden md:flex items-center gap-1">
              {links.map((link) => (
                <Link
                  key={link.href}
                  to={link.href}
                  className={clsx(
                    'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    location.pathname.startsWith(link.href)
                      ? 'bg-primary-900/50 text-primary-300'
                      : 'text-slate-400 hover:text-white hover:bg-surface-800',
                  )}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          )}

          {/* Right side */}
          <div className="flex items-center gap-2">
            {user ? (
              <>
                <NotificationBell />
                <div className="relative">
                  <button
                    id="user-menu-btn"
                    onClick={() => setMenuOpen((o) => !o)}
                    className="flex items-center gap-2 btn-ghost rounded-lg px-3 py-2"
                    aria-label="User menu"
                    aria-expanded={menuOpen}
                  >
                    <div className="w-7 h-7 rounded-full bg-primary-700 flex items-center justify-center text-white text-xs font-bold shrink-0">
                      {user.full_name.charAt(0).toUpperCase()}
                    </div>
                    <div className="hidden sm:block text-left">
                      <div className="text-sm font-medium text-white leading-tight truncate max-w-[120px]">
                        {user.full_name}
                      </div>
                      <div className={clsx('text-xs capitalize', roleColor[user.role])}>
                        {user.role}
                      </div>
                    </div>
                    <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {menuOpen && (
                    <>
                      <div
                        className="fixed inset-0 z-10"
                        onClick={() => setMenuOpen(false)}
                      />
                      <div className="absolute right-0 mt-1 w-48 bg-surface-800 border border-slate-700 rounded-xl shadow-2xl z-20 overflow-hidden animate-fade-in">
                        <Link
                          to="/account"
                          className="flex items-center gap-2 px-4 py-3 text-sm text-slate-300 hover:bg-surface-700 hover:text-white"
                          onClick={() => setMenuOpen(false)}
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                          Account
                        </Link>
                        <hr className="border-slate-700" />
                        <button
                          onClick={() => { setMenuOpen(false); logout(); }}
                          className="w-full flex items-center gap-2 px-4 py-3 text-sm text-red-400 hover:bg-red-900/20 hover:text-red-300"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                          </svg>
                          Sign out
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <Link to="/login" className="btn-ghost text-sm">
                  Sign in
                </Link>
                <Link to="/register" className="btn-primary text-sm">
                  Get Started
                </Link>
              </div>
            )}

            {/* Mobile menu toggle */}
            {user && (
              <button
                className="md:hidden btn-ghost p-2"
                onClick={() => setMenuOpen((o) => !o)}
                aria-label="Toggle mobile menu"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            )}
          </div>
        </div>

        {/* Mobile Nav */}
        {user && menuOpen && (
          <div className="md:hidden pb-3 animate-fade-in">
            {links.map((link) => (
              <Link
                key={link.href}
                to={link.href}
                onClick={() => setMenuOpen(false)}
                className={clsx(
                  'block px-3 py-2 rounded-md text-sm font-medium',
                  location.pathname.startsWith(link.href)
                    ? 'bg-primary-900/50 text-primary-300'
                    : 'text-slate-400 hover:text-white',
                )}
              >
                {link.label}
              </Link>
            ))}
          </div>
        )}
      </div>
    </nav>
  );
}
