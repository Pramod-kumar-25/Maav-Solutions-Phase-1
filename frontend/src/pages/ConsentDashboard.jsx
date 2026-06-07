import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { request } from '../services/api';

const STATUS_BADGES = {
  ACTIVE: 'badge-active',
  REVOKED: 'badge-draft',
  EXPIRED: 'badge-draft'
};

export default function ConsentDashboard() {
  const [consents, setConsents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    request('/consent/')
      .then(data => {
        setConsents(data || []);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message || 'Failed to load consents');
        setLoading(false);
      });
  }, []);

  const activeConsents = consents.filter(c => c.status === 'ACTIVE');
  const revokedConsents = consents.filter(c => c.status === 'REVOKED');
  const expiredConsents = consents.filter(c => c.status === 'EXPIRED');

  if (loading) return (
    <div className="page-loader" data-testid="page-loader">
      <div className="spinner" />
      <span className="text-muted">Loading consents...</span>
    </div>
  );

  return (
    <>
      <div className="page-header">
        <div className="page-header-left">
          <h1>Consent Manager</h1>
          <div className="breadcrumb">
            <Link to="/">Dashboard</Link> / Settings / Consent
          </div>
        </div>
      </div>

      <div className="page-body">
        {error && <div className="alert alert-error" data-testid="error-alert">⚠️ {error}</div>}

        {/* Stats */}
        <div className="grid-3" style={{ marginBottom: '2rem' }}>
          <div className="stat-card" data-testid="stat-active">
            <div className="stat-icon" style={{ background: 'var(--success-muted)' }}>🛡️</div>
            <div className="stat-content">
              <div className="stat-label">Active Consents</div>
              <div className="stat-value" style={{ color: 'var(--success)' }}>{activeConsents.length}</div>
              <div className="stat-desc">Authorized access</div>
            </div>
          </div>
          <div className="stat-card" data-testid="stat-revoked">
            <div className="stat-icon" style={{ background: 'var(--danger-muted)' }}>🚫</div>
            <div className="stat-content">
              <div className="stat-label">Revoked Consents</div>
              <div className="stat-value" style={{ color: 'var(--danger)' }}>{revokedConsents.length}</div>
              <div className="stat-desc">Access cancelled</div>
            </div>
          </div>
          <div className="stat-card" data-testid="stat-expired">
            <div className="stat-icon" style={{ background: 'var(--surface-2)' }}>⏳</div>
            <div className="stat-content">
              <div className="stat-label">Expired Consents</div>
              <div className="stat-value" style={{ color: 'var(--text-2)' }}>{expiredConsents.length}</div>
              <div className="stat-desc">Past validity date</div>
            </div>
          </div>
        </div>

        {/* List Card */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">All Consent Artifacts</div>
              <div className="card-subtitle">Manage authorization for chartered accountants and external access</div>
            </div>
          </div>

          {consents.length === 0 ? (
            <div className="empty-state" data-testid="empty-state">
              <div className="empty-icon">🛡️</div>
              <h3>No consents granted</h3>
              <p>You have not authorized any external access to your taxpayer profiles or filings yet.</p>
            </div>
          ) : (
            <div className="consent-list" data-testid="consent-list">
              {consents.map(c => (
                <Link to={`/settings/consent/${c.id}`} className="filing-card" key={c.id} data-testid={`consent-card-${c.id}`}>
                  <div className="filing-card-icon" style={{ background: c.status === 'ACTIVE' ? 'var(--success-muted)' : 'var(--surface-2)' }}>
                    {c.status === 'ACTIVE' ? '🔑' : '🔒'}
                  </div>
                  <div className="filing-card-info">
                    <div className="filing-card-year">{c.purpose}</div>
                    <div className="filing-card-meta">Scope: {c.scope} · Expiry: {new Date(c.expiry_at).toLocaleDateString()}</div>
                  </div>
                  <span className={`badge ${STATUS_BADGES[c.status] || ''}`} style={{
                    ...(c.status === 'REVOKED' && { background: 'var(--danger-muted)', color: '#991b1b' }),
                    ...(c.status === 'EXPIRED' && { background: 'var(--surface-2)', color: 'var(--text-2)' }),
                  }}>
                    {c.status}
                  </span>
                  <svg className="filing-card-arrow" width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
