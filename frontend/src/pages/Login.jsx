import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(form.email, form.password);
      navigate('/');
    } catch (err) {
      setError(err.message || 'Invalid credentials. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      {/* Brand Panel */}
      <div className="auth-brand">
        <div className="auth-brand-content">
          <div className="auth-brand-logo">M</div>
          <h2>MaaV Solutions</h2>
          <p>India's intelligent tax filing orchestration platform for individuals, businesses, and chartered accountants.</p>
          <div className="auth-features">
            <div className="auth-feature">
              <div className="auth-feature-icon">🔒</div>
              <div className="auth-feature-text">
                <strong>Bank-Grade Security</strong>
                <span>SHA-256 evidence snapshots on every action</span>
              </div>
            </div>
            <div className="auth-feature">
              <div className="auth-feature-icon">⚙️</div>
              <div className="auth-feature-text">
                <strong>ITR Determination Engine</strong>
                <span>Automated rule-based ITR type selection</span>
              </div>
            </div>
            <div className="auth-feature">
              <div className="auth-feature-icon">📋</div>
              <div className="auth-feature-text">
                <strong>Full Audit Trail</strong>
                <span>Immutable log of every state transition</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Form Panel */}
      <div className="auth-form-panel">
        <div className="auth-form-box">
          <h3>Welcome back</h3>
          <p className="subtitle">Sign in to your account to continue</p>

          {error && (
            <div className="alert alert-error">⚠️ {error}</div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Email Address</label>
              <input
                type="email"
                placeholder="you@example.com"
                required
                value={form.email}
                onChange={e => setForm({ ...form, email: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                placeholder="••••••••"
                required
                value={form.password}
                onChange={e => setForm({ ...form, password: e.target.value })}
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary btn-full btn-lg"
              disabled={loading}
              style={{ marginTop: '0.5rem' }}
            >
              {loading ? <><div className="spinner" />Signing in…</> : 'Sign In'}
            </button>
          </form>

          <div className="divider">or</div>
          <p style={{ textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-2)' }}>
            Don't have an account?{' '}
            <Link to="/register" className="auth-link">Create account</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
