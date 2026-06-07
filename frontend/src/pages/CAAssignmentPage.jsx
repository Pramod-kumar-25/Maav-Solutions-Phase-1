import React, { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { request } from '../services/api';
import { useAuth } from '../hooks/useAuth';

export default function CAAssignmentPage() {
  const { year } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  
  // States
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  
  const [filing, setFiling] = useState(null);
  const [cas, setCas] = useState([]);
  const [selectedCA, setSelectedCA] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Consent Form
  const [consentForm, setConsentForm] = useState({
    purpose: `ITR delegation for FY ${year}`,
    scope: 'FULL_ACCESS',
    expiry_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] // 30 days default
  });

  // Current User details from Token
  let currentUserId = '';
  if (token) {
    try {
      const payload = token.split('.')[1];
      const jwtPayload = JSON.parse(atob(payload));
      currentUserId = jwtPayload.sub || jwtPayload.id || '';
    } catch {}
  }

  useEffect(() => {
    fetchData();
  }, [year]);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      // 1. Fetch Filing details
      let filingData;
      try {
        filingData = await request(`/filing/?financial_year=${year}`);
      } catch (err) {
        throw new Error(`Filing Case for FY ${year} not found. Please initialize a case first.`);
      }
      setFiling(filingData);

      // Verify if filing is eligible
      if (filingData.current_state !== 'DRAFT' && filingData.current_state !== 'READY_FOR_REVIEW') {
        throw new Error(`Cannot assign CA to this filing. Filing is in state: ${filingData.current_state}. Assignment is only permitted during DRAFT or READY_FOR_REVIEW.`);
      }

      // 2. Fetch CAs
      const caList = await request('/auth/cas');
      setCas(caList || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectCA = (ca) => {
    setError('');
    // Validation: Self assignment
    if (ca.id === currentUserId) {
      setError("Validation Error: Self-assignment is not permitted.");
      return;
    }
    setSelectedCA(ca);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      // 1. Validate Form Fields
      if (!selectedCA) {
        throw new Error("Validation Error: Please select a Chartered Accountant (CA) first.");
      }
      if (!consentForm.purpose.trim()) {
        throw new Error("Validation Error: Consent purpose cannot be empty.");
      }
      if (consentForm.purpose.trim().length > 50) {
        throw new Error("Validation Error: Consent purpose cannot exceed 50 characters.");
      }
      if (!consentForm.expiry_at) {
        throw new Error("Validation Error: Consent expiry date is required.");
      }

      const expiryDate = new Date(consentForm.expiry_at);
      if (expiryDate <= new Date()) {
        throw new Error("Validation Error: Consent expiry date must be in the future.");
      }

      if (!filing || (filing.current_state !== 'DRAFT' && filing.current_state !== 'READY_FOR_REVIEW')) {
        throw new Error("Validation Error: Filing case is not in a valid state for assignment.");
      }

      // 2. Create Consent Artifact
      const consentPayload = {
        purpose: consentForm.purpose.trim(),
        scope: consentForm.scope,
        expiry_at: new Date(consentForm.expiry_at).toISOString()
      };
      const createdConsent = await request('/consent/', {
        method: 'POST',
        body: JSON.stringify(consentPayload)
      });

      // 3. Create CA Assignment
      const assignmentPayload = {
        filing_id: filing.id,
        ca_user_id: selectedCA.id,
        consent_id: createdConsent.id
      };
      await request('/consent/assignments', {
        method: 'POST',
        body: JSON.stringify(assignmentPayload)
      });

      setSuccess(true);
    } catch (err) {
      setError(err.message || "An error occurred during CA delegation.");
    } finally {
      setSubmitting(false);
    }
  };

  const filteredCAs = cas.filter(ca => 
    ca.legal_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ca.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="page-loader" data-testid="page-loader">
        <div className="spinner" style={{ borderColor: 'var(--border)', borderTopColor: 'var(--primary)' }} />
        <span className="text-muted">Loading available CAs…</span>
      </div>
    );
  }

  if (success) {
    return (
      <div className="page-body" data-testid="success-state">
        <div className="card" style={{ maxWidth: '600px', margin: '3rem auto', textAlign: 'center', padding: '3rem 2rem' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1.5rem' }}>🤝</div>
          <h2 style={{ marginBottom: '1rem', color: 'var(--success)' }}>CA Assignment Successful!</h2>
          <p style={{ color: 'var(--text-2)', marginBottom: '2rem', lineHeight: '1.6' }}>
            You have successfully granted consent and delegated the filing for **FY {year}** to <strong>{selectedCA?.legal_name}</strong> ({selectedCA?.email}).
          </p>
          <button 
            className="btn btn-primary btn-full" 
            onClick={() => navigate(`/filings/${year}`)}
          >
            Go to Filing Details
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Page Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h1>Delegate to Chartered Accountant</h1>
          <div className="breadcrumb">
            <Link to="/">Dashboard</Link> › <Link to={`/filings/${year}`}>FY {year} Filing</Link> › Delegate
          </div>
        </div>
      </div>

      <div className="page-body">
        {error && (
          <div className="alert alert-error" data-testid="error-alert">
            ⚠️ {error}
          </div>
        )}

        <div className="grid-2">
          {/* Left Column: CA List */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ marginBottom: '1.5rem' }}>
              <div className="card-title">Select a Chartered Accountant</div>
              <div className="card-subtitle">Choose from active, verified CA accounts</div>
            </div>

            {/* Search Input */}
            <div className="form-group">
              <input
                type="text"
                placeholder="🔍 Search CA by name or email..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                data-testid="ca-search-input"
              />
            </div>

            {filteredCAs.length === 0 ? (
              <div className="empty-state" style={{ padding: '3rem 1rem' }} data-testid="empty-ca-state">
                <div className="empty-icon">👥</div>
                <h3>No CAs Available</h3>
                <p>No active Chartered Accountants matched your search criteria.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '400px', overflowY: 'auto' }} data-testid="ca-list-container">
                {filteredCAs.map(ca => {
                  const isSelected = selectedCA?.id === ca.id;
                  return (
                    <div 
                      key={ca.id}
                      onClick={() => handleSelectCA(ca)}
                      style={{
                        padding: '1rem',
                        border: isSelected ? '2px solid var(--primary)' : '1px solid var(--border)',
                        background: isSelected ? 'var(--primary-muted)' : 'var(--surface)',
                        borderRadius: 'var(--radius-sm)',
                        cursor: 'pointer',
                        display: 'flex',
                        justifyContent: 'between',
                        alignItems: 'center',
                        transition: 'all 0.2s'
                      }}
                      data-testid={`ca-item-${ca.id}`}
                    >
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-1)' }}>{ca.legal_name}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-3)' }}>{ca.email}</div>
                      </div>
                      <div>
                        {isSelected ? (
                          <span className="badge badge-active" style={{ fontSize: '0.7rem' }}>Selected</span>
                        ) : (
                          <span className="badge badge-expired" style={{ fontSize: '0.7rem' }}>Select</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right Column: Consent Form */}
          <div className="card">
            <div style={{ marginBottom: '1.5rem' }}>
              <div className="card-title">Define Consent & Delegate</div>
              <div className="card-subtitle">Grant access permissions for the selected CA</div>
            </div>

            <form onSubmit={handleSubmit} data-testid="consent-form">
              {/* Selected CA Alert */}
              {selectedCA ? (
                <div className="alert alert-info" style={{ marginBottom: '1.5rem' }} data-testid="selected-ca-banner">
                  Selected CA: <strong>{selectedCA.legal_name}</strong> ({selectedCA.email})
                </div>
              ) : (
                <div className="alert alert-warning" style={{ marginBottom: '1.5rem' }}>
                  Please select a CA from the left panel to begin delegation.
                </div>
              )}

              <div className="form-group">
                <label>Filing Details</label>
                <input 
                  type="text" 
                  disabled 
                  value={`FY ${year} Filing Case (${filing?.id ? filing.id.slice(0, 18) + '...' : ''})`} 
                />
              </div>

              <div className="form-group">
                <label>Consent Purpose</label>
                <input
                  type="text"
                  required
                  maxLength={50}
                  placeholder="e.g. Audit review and submission"
                  value={consentForm.purpose}
                  onChange={e => setConsentForm({ ...consentForm, purpose: e.target.value })}
                  data-testid="consent-purpose-input"
                />
              </div>

              <div className="form-group">
                <label>Access Scope</label>
                <select
                  value={consentForm.scope}
                  onChange={e => setConsentForm({ ...consentForm, scope: e.target.value })}
                  data-testid="consent-scope-select"
                >
                  <option value="FULL_ACCESS">Full Access (Read, Edit, Transition)</option>
                  <option value="READ_ONLY">Read Only (Review entries & flags)</option>
                </select>
              </div>

              <div className="form-group">
                <label>Consent Expiry Date</label>
                <input
                  type="date"
                  required
                  value={consentForm.expiry_at}
                  onChange={e => setConsentForm({ ...consentForm, expiry_at: e.target.value })}
                  data-testid="consent-expiry-input"
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-full btn-lg"
                disabled={submitting || !selectedCA}
                data-testid="submit-assignment-btn"
                style={{ marginTop: '1.5rem' }}
              >
                {submitting ? (
                  <><div className="spinner" />Authorizing Delegation...</>
                ) : (
                  'Confirm & Authorize Delegation'
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}
