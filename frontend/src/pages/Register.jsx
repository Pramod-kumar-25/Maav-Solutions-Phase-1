import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    pan: '', legal_name: '', email: '',
    mobile: '', password: '', primary_role: 'INDIVIDUAL'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await register(form);
      navigate('/login');
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
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
          <h2>Join MaaV Solutions</h2>
          <p>Get started with India's most intelligent tax filing orchestration platform in minutes.</p>
          <div className="auth-features">
            <div className="auth-feature">
              <div className="auth-feature-icon">📄</div>
              <div className="auth-feature-text">
                <strong>ITR-1 to ITR-4</strong>
                <span>Automatic form selection based on income profile</span>
              </div>
            </div>
            <div className="auth-feature">
              <div className="auth-feature-icon">🤖</div>
              <div className="auth-feature-text">
                <strong>Smart Determination Engine</strong>
                <span>Rules-based ITR type with locked compliance</span>
              </div>
            </div>
            <div className="auth-feature">
              <div className="auth-feature-icon">🏢</div>
              <div className="auth-feature-text">
                <strong>CA Collaboration</strong>
                <span>Multi-role workflow with approval gates</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Form Panel */}
      <div className="auth-form-panel">
        <div className="auth-form-box">
          <h3>Create your account</h3>
          <p className="subtitle">Fill in your details to get started</p>

          {error && <div className="alert alert-error">⚠️ {error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="grid-2" style={{ gap: '1rem' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>PAN Number</label>
                <input
                  type="text" maxLength={10} placeholder="ABCDE1234F"
                  required value={form.pan}
                  onChange={e => setForm({ ...form, pan: e.target.value.toUpperCase() })}
                />
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Role</label>
                <select value={form.primary_role} onChange={e => setForm({ ...form, primary_role: e.target.value })}>
                  <option value="INDIVIDUAL">Individual</option>
                  <option value="BUSINESS">Business</option>
                  <option value="CA">CA</option>
                </select>
              </div>
            </div>

            <div className="form-group mt-2">
              <label>Legal Name (as per PAN)</label>
              <input
                type="text" placeholder="Full Name"
                required value={form.legal_name}
                onChange={e => setForm({ ...form, legal_name: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Email Address</label>
              <input
                type="email" placeholder="you@example.com"
                required value={form.email}
                onChange={e => setForm({ ...form, email: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Mobile Number</label>
              <input
                type="tel" placeholder="9876543210" maxLength={10}
                required value={form.mobile}
                onChange={e => setForm({ ...form, mobile: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input
                type="password" placeholder="Minimum 8 characters"
                required value={form.password}
                onChange={e => setForm({ ...form, password: e.target.value })}
              />
            </div>

            <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading}>
              {loading ? <><div className="spinner" />Creating account…</> : 'Create Account'}
            </button>
          </form>

          <div className="divider">or</div>
          <p style={{ textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-2)' }}>
            Already have an account?{' '}
            <Link to="/login" className="auth-link">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
