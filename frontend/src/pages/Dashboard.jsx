import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { request } from '../services/api';
import { useAuth } from '../hooks/useAuth';

// Decode JWT payload
function decodeJwt(token) {
  try {
    const payload = token.split('.')[1];
    return JSON.parse(atob(payload));
  } catch {
    return {};
  }
}

const STATE_COLORS = {
  DRAFT: 'badge-draft',
  READY_FOR_REVIEW: 'badge-ready_for_review',
  LOCKED: 'badge-locked',
  SUBMITTED: 'badge-submitted',
};
const STATE_ICONS = { DRAFT: '✏️', READY_FOR_REVIEW: '🔍', LOCKED: '🔒', SUBMITTED: '✅' };

export default function Dashboard() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const jwtPayload = token ? decodeJwt(token) : {};
  const userName = jwtPayload.name || 'Taxpayer';
  const [profile, setProfile] = useState(null);
  const [filings, setFilings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      request('/taxpayer/profile').catch(() => null),
      fetchFilings(),
    ]).then(([prof]) => {
      setProfile(prof);
      setLoading(false);
    });
  }, []);

  const fetchFilings = async () => {
    const years = ['2023-24', '2022-23', '2024-25'];
    const results = [];
    for (const y of years) {
      try {
        const d = await request(`/filing/?financial_year=${y}`);
        results.push(d);
      } catch {}
    }
    setFilings(results);
    return results;
  };

  const stats = {
    total: filings.length,
    submitted: filings.filter(f => f.current_state === 'SUBMITTED').length,
    active: filings.filter(f => f.current_state !== 'SUBMITTED').length,
  };

  if (loading) return (
    <div className="page-loader">
      <div className="spinner" style={{ borderColor: 'var(--border)', borderTopColor: 'var(--primary)' }} />
      <span className="text-muted">Loading dashboard…</span>
    </div>
  );

  return (
    <>
      <div className="page-header">
        <div className="page-header-left">
          <h1>Dashboard</h1>
          <div className="breadcrumb">Overview of your tax filing activity</div>
        </div>
        <Link to="/filings/new" className="btn btn-primary btn-sm">
          <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" /></svg>
          New Filing
        </Link>
      </div>

      <div className="page-body">
        {error && <div className="alert alert-error">⚠️ {error}</div>}

        {/* Profile Banner */}
        {profile && (
          <div className="card" style={{ background: 'linear-gradient(135deg, #0f172a, #1e1b4b)', border: 'none', marginBottom: '1.5rem' }}>
            <div className="flex items-center justify-between">
              <div>
                <div style={{ color: 'rgba(255,255,255,0.55)', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.4rem' }}>Welcome, {userName}</div>
                <div style={{ color: '#fff', fontSize: '1.2rem', fontWeight: 800, marginBottom: '0.4rem' }}>{profile.residential_status} Taxpayer Profile</div>
                <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
                  <span style={{ background: 'rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.8)', borderRadius: '6px', padding: '0.2rem 0.6rem', fontSize: '0.75rem', fontWeight: 600 }}>
                    📋 {profile.residential_status || 'RESIDENT'}
                  </span>
                  <span style={{ background: 'rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.8)', borderRadius: '6px', padding: '0.2rem 0.6rem', fontSize: '0.75rem', fontWeight: 600 }}>
                    🏦 {profile.default_tax_regime} Regime
                  </span>
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.7rem', marginBottom: '0.3rem' }}>Profile ID</div>
                <div style={{ color: 'rgba(255,255,255,0.7)', fontFamily: 'monospace', fontSize: '0.75rem' }}>{profile.id?.slice(0, 18)}…</div>
              </div>
            </div>
          </div>
        )}

        {/* Stats */}
        <div className="grid-3" style={{ marginBottom: '2rem' }}>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'var(--primary-muted)' }}>📁</div>
            <div className="stat-content">
              <div className="stat-label">Total Filings</div>
              <div className="stat-value">{stats.total}</div>
              <div className="stat-desc">All financial years</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'var(--success-muted)' }}>✅</div>
            <div className="stat-content">
              <div className="stat-label">Submitted</div>
              <div className="stat-value" style={{ color: 'var(--success)' }}>{stats.submitted}</div>
              <div className="stat-desc">Successfully filed</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'var(--warning-muted)' }}>⏳</div>
            <div className="stat-content">
              <div className="stat-label">In Progress</div>
              <div className="stat-value" style={{ color: 'var(--warning)' }}>{stats.active}</div>
              <div className="stat-desc">Pending action</div>
            </div>
          </div>
        </div>

        {/* Recent Filings */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Recent Filings</div>
              <div className="card-subtitle">Click a filing to manage it</div>
            </div>
            <Link to="/filings" className="btn btn-ghost btn-sm">View All</Link>
          </div>

          {filings.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📂</div>
              <h3>No filings yet</h3>
              <p>Initialize your first tax filing to get started with the orchestration workflow.</p>
              <Link to="/filings/new" className="btn btn-primary mt-2">Start First Filing</Link>
            </div>
          ) : (
            filings.map(f => (
              <Link to={`/filings/${f.financial_year}`} className="filing-card" key={f.id}>
                <div className="filing-card-icon" style={{ background: 'var(--primary-muted)' }}>
                  {STATE_ICONS[f.current_state] || '📄'}
                </div>
                <div className="filing-card-info">
                  <div className="filing-card-year">FY {f.financial_year}</div>
                  <div className="filing-card-meta">ITR Filing · Case ID: {f.id?.slice(0,12)}…</div>
                </div>
                <span className={`badge ${STATE_COLORS[f.current_state] || ''}`}>
                  {f.current_state?.replace(/_/g, ' ')}
                </span>
                <svg className="filing-card-arrow" width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            ))
          )}
        </div>

        {/* Quick Actions */}
        {!profile && (
          <div className="alert alert-warning">
            ⚠️ You don't have a taxpayer profile yet. <Link to="/filings/new" className="auth-link">Create one to start filing.</Link>
          </div>
        )}
      </div>
    </>
  );
}
