import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { request } from '../services/api';

const STATUS_BADGES = {
  ACTIVE: 'badge-active',
  REVOKED: 'badge-draft',
  EXPIRED: 'badge-draft'
};

export default function ConsentDetail() {
  const { id } = useParams();
  const [consent, setConsent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [revoking, setRevoking] = useState(false);
  const [reason, setReason] = useState('');
  const [showConfirm, setShowConfirm] = useState(false);
  const [actionError, setActionError] = useState('');
  const [actionSuccess, setActionSuccess] = useState('');

  const fetchConsent = () => {
    setLoading(true);
    request(`/consent/${id}`)
      .then(data => {
        setConsent(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message || 'Failed to load consent details');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchConsent();
  }, [id]);

  const handleRevoke = async (e) => {
    e.preventDefault();
    if (!reason.trim()) {
      setActionError('Please provide a reason for revocation.');
      return;
    }

    setRevoking(true);
    setActionError('');
    setActionSuccess('');

    try {
      await request(`/consent/${id}/revoke`, {
        method: 'POST',
        body: JSON.stringify({ reason })
      });
      setActionSuccess('Consent successfully revoked.');
      setShowConfirm(false);
      setReason('');
      fetchConsent();
    } catch (err) {
      setActionError(err.message || 'Failed to revoke consent.');
    } finally {
      setRevoking(false);
    }
  };

  if (loading) return (
    <div className="page-loader" data-testid="page-loader">
      <div className="spinner" />
      <span className="text-muted">Loading consent details...</span>
    </div>
  );

  if (error || !consent) return (
    <div className="page-body">
      <div className="alert alert-error" data-testid="error-alert">⚠️ {error || 'Consent not found.'}</div>
      <Link to="/settings/consent" className="btn btn-ghost" data-testid="back-to-list-error-btn">Back to Consent Manager</Link>
    </div>
  );

  return (
    <>
      <div className="page-header">
        <div className="page-header-left">
          <h1>Consent Details</h1>
          <div className="breadcrumb">
            <Link to="/">Dashboard</Link> / <Link to="/settings/consent">Consent</Link> / {consent.id?.slice(0, 8)}...
          </div>
        </div>
        <Link to="/settings/consent" className="btn btn-ghost btn-sm" data-testid="back-to-list-header-btn">
          Back to list
        </Link>
      </div>

      <div className="page-body">
        {actionSuccess && <div className="alert alert-success" data-testid="success-alert">✅ {actionSuccess}</div>}
        {actionError && <div className="alert alert-error" data-testid="action-error-alert">⚠️ {actionError}</div>}

        <div className="grid-2">
          {/* Information Card */}
          <div className="card" data-testid="consent-details-card">
            <div className="card-header">
              <div className="card-title">Authorization Details</div>
              <span className={`badge ${STATUS_BADGES[consent.status] || ''}`} style={{
                ...(consent.status === 'REVOKED' && { background: 'var(--danger-muted)', color: '#991b1b' }),
                ...(consent.status === 'EXPIRED' && { background: 'var(--surface-2)', color: 'var(--text-2)' }),
              }}>
                {consent.status}
              </span>
            </div>

            <div className="flex-col gap-2">
              <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '0.5rem', fontSize: '0.9rem' }}>
                <span className="text-subtle font-semibold">Purpose:</span>
                <span className="text-1" data-testid="details-purpose">{consent.purpose}</span>

                <span className="text-subtle font-semibold">Scope:</span>
                <span className="text-1" data-testid="details-scope">{consent.scope}</span>

                <span className="text-subtle font-semibold">Granted:</span>
                <span className="text-1" data-testid="details-granted">{new Date(consent.granted_at).toLocaleString()}</span>

                <span className="text-subtle font-semibold">Expires:</span>
                <span className="text-1" data-testid="details-expiry">{new Date(consent.expiry_at).toLocaleString()}</span>

                <span className="text-subtle font-semibold">Artifact ID:</span>
                <span className="text-2" style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{consent.id}</span>
              </div>
            </div>
          </div>

          {/* Action Card */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">Actions</div>
            </div>

            {consent.status === 'ACTIVE' ? (
              <>
                {!showConfirm ? (
                  <div style={{ textAlign: 'center', padding: '1rem 0' }}>
                    <p className="text-2 mb-2">You can revoke this consent at any time. Revoking will immediately terminate access for all chartered accountants assigned under it.</p>
                    <button
                      className="btn btn-danger"
                      onClick={() => setShowConfirm(true)}
                      data-testid="revoke-btn"
                    >
                      Revoke Consent
                    </button>
                  </div>
                ) : (
                  <form onSubmit={handleRevoke} data-testid="revoke-form">
                    <div className="form-group">
                      <label htmlFor="reason">Reason for Revocation</label>
                      <textarea
                        id="reason"
                        rows="3"
                        placeholder="Please explain why you are revoking this consent..."
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        required
                        data-testid="revocation-reason-input"
                      />
                    </div>
                    <div className="btn-group">
                      <button
                        type="submit"
                        className="btn btn-danger"
                        disabled={revoking}
                        data-testid="confirm-revoke-btn"
                      >
                        {revoking ? 'Revoking...' : 'Confirm Revocation'}
                      </button>
                      <button
                        type="button"
                        className="btn btn-ghost"
                        onClick={() => {
                          setShowConfirm(false);
                          setActionError('');
                        }}
                        disabled={revoking}
                        data-testid="cancel-revoke-btn"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                )}
              </>
            ) : (
              <div style={{ textAlign: 'center', padding: '1rem 0', color: 'var(--text-3)' }} data-testid="inactive-consent-state">
                <span style={{ fontSize: '2rem', display: 'block', marginBottom: '0.5rem' }}>🔒</span>
                <p className="text-3">This consent is already {consent.status.toLowerCase()} and cannot be modified.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
