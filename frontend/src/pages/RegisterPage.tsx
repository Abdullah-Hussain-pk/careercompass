import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Alert } from '../components/ui';

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      await register(email, password, fullName);
      navigate('/dashboard', { replace: true });
    } catch (err: unknown) {
      const msg = (err as { message?: string })?.message ?? 'Registration failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-6 text-white font-bold text-xl hover:text-primary-400 transition-colors">
            <span className="w-10 h-10 rounded-xl bg-primary-600 flex items-center justify-center text-lg font-black">C</span>
            CareerCompass
          </Link>
          <h1 className="text-2xl font-bold text-white">Create your account</h1>
          <p className="text-slate-400 text-sm mt-1">Free for students — start your career journey today</p>
        </div>

        <div className="card">
          {error && (
            <Alert type="error" onClose={() => setError('')} className="mb-4">
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit} noValidate>
            <div className="space-y-4">
              <div>
                <label htmlFor="full-name" className="label">Full name</label>
                <input
                  id="full-name"
                  type="text"
                  autoComplete="name"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="input"
                  placeholder="Ahmad bin Abdullah"
                />
              </div>

              <div>
                <label htmlFor="email" className="label">Email address</label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input"
                  placeholder="you@university.edu"
                />
              </div>

              <div>
                <label htmlFor="password" className="label">Password</label>
                <input
                  id="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input"
                  placeholder="At least 8 characters"
                />
              </div>

              <div>
                <label htmlFor="confirm-password" className="label">Confirm password</label>
                <input
                  id="confirm-password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="input"
                  placeholder="Re-enter password"
                />
              </div>

              <p className="text-xs text-slate-500 pt-1">
                By creating an account you agree to our{' '}
                <Link to="/privacy" className="text-primary-400 hover:underline">Privacy Policy</Link> and{' '}
                <Link to="/disclaimer" className="text-primary-400 hover:underline">Disclaimer</Link>.
              </p>

              <button
                id="register-submit"
                type="submit"
                disabled={loading}
                className="btn-primary w-full py-3 text-base"
              >
                {loading ? (
                  <><span className="spinner h-4 w-4" /> Creating account…</>
                ) : (
                  'Create account'
                )}
              </button>
            </div>
          </form>

          <p className="text-center text-sm text-slate-400 mt-5">
            Already have an account?{' '}
            <Link to="/login" className="text-primary-400 hover:text-primary-300 font-medium">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
