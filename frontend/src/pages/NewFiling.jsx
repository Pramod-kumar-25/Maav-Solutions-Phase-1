import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { request } from '../services/api';

const STEPS = ['Profile Setup', 'ITR Determination', 'Initialize Case'];

export default function NewFiling() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Step 0: profile
  const [profile, setProfile] = useState(null);
  const [profileForm, setProfileForm] = useState({
    days_in_india_current_fy: 182,
    days_in_india_last_4_years: 400,
    has_foreign_income: false,
    default_tax_regime: 'NEW',
    aadhaar_link_status: true,
  });

  // Step 1: ITR Determination
  const [fy, setFy] = useState('2023-24');
  const [determination, setDetermination] = useState(null);

  // Step 2: Filing case
  const [created, setCreated] = useState(false);

  useEffect(() => {
    request('/taxpayer/profile')
      .then(p => { setProfile(p); setStep(1); })
      .catch(() => setStep(0));
  }, []);

  const createProfile = async (e) => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      const p = await request('/taxpayer/profile', { method: 'POST', body: JSON.stringify(profileForm) });
      setProfile(p);
      setStep(1);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const determineThenLock = async (e) => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      const itr = await request(`/itr/determine?force=true`, { method: 'POST', body: JSON.stringify({ financial_year: fy }) });
      await request(`/itr/${fy}/lock`, { method: 'POST' });
      setDetermination(itr);
      setStep(2);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const createFiling = async () => {
    setLoading(true); setError('');
    try {
      // Check if filing case already exists first
      try {
        await request(`/filing/?financial_year=${fy}`);
        // Already exists, just navigate
        navigate(`/filings/${fy}`);
        return;
      } catch {}

      await request('/filing/', {
        method: 'POST',
        body: JSON.stringify({ financial_year: fy, itr_determination_id: determination.id }),
      });
      setCreated(true);
      setTimeout(() => navigate(`/filings/${fy}`), 1400);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const stepDone = (i) => i < step;
  const stepActive = (i) => i === step;

  return (
    <>
      <div className="page-header">
        <div className="page-header-left">
          <h1>New Tax Filing</h1>
          <div className="breadcrumb">
            <Link to="/">Dashboard</Link> › <Link to="/filings">Filings</Link> › New
          </div>
        </div>
      </div>

      <div className="page-body" style={{ maxWidth: 680, margin: '0 auto' }}>
        {/* Stepper */}
        <div className="stepper">
          {STEPS.map((label, i) => (
            <div key={i} className={`step ${stepDone(i) ? 'done' : ''} ${stepActive(i) ? 'active' : ''}`}>
              <div className="step-dot">
                {stepDone(i) ? '✓' : i + 1}
              </div>
              <div className="step-label">{label}</div>
            </div>
          ))}
        </div>

        {error && <div className="alert alert-error">⚠️ {error}</div>}

        {/* ── STEP 0: Taxpayer Profile ── */}
        {step === 0 && (
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Taxpayer Profile</div>
                <div className="card-subtitle">This is required once to determine your residential status</div>
              </div>
            </div>
            <form onSubmit={createProfile}>
              <div className="grid-2">
                <div className="form-group">
                  <label>Days in India (Current FY)</label>
                  <input type="number" required value={profileForm.days_in_india_current_fy}
                    onChange={e => setProfileForm({ ...profileForm, days_in_india_current_fy: +e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Days in India (Last 4 Years)</label>
                  <input type="number" required value={profileForm.days_in_india_last_4_years}
                    onChange={e => setProfileForm({ ...profileForm, days_in_india_last_4_years: +e.target.value })} />
                </div>
              </div>
              <div className="grid-2">
                <div className="form-group">
                  <label>Tax Regime</label>
                  <select value={profileForm.default_tax_regime}
                    onChange={e => setProfileForm({ ...profileForm, default_tax_regime: e.target.value })}>
                    <option value="NEW">New Regime (Section 115BAC)</option>
                    <option value="OLD">Old Regime</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Aadhaar Linked?</label>
                  <select value={String(profileForm.aadhaar_link_status)}
                    onChange={e => setProfileForm({ ...profileForm, aadhaar_link_status: e.target.value === 'true' })}>
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                  </select>
                </div>
              </div>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? <><div className="spinner" />Saving…</> : 'Save Profile & Continue →'}
              </button>
            </form>
          </div>
        )}

        {/* ── STEP 1: ITR Determination ── */}
        {step === 1 && (
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">ITR Determination</div>
                <div className="card-subtitle">The engine will automatically determine the correct ITR form for your financial year</div>
              </div>
            </div>

            {profile && (
              <div className="alert alert-success mb-2">
                ✅ Profile ready: <strong>{profile.residential_status}</strong> · <strong>{profile.default_tax_regime} Regime</strong>
              </div>
            )}

            <form onSubmit={determineThenLock}>
              <div className="form-group">
                <label>Financial Year</label>
                <select value={fy} onChange={e => setFy(e.target.value)}>
                  <option value="2023-24">FY 2023-24 (AY 2024-25)</option>
                  <option value="2022-23">FY 2022-23 (AY 2023-24)</option>
                  <option value="2024-25">FY 2024-25 (AY 2025-26)</option>
                </select>
              </div>

              <div className="alert alert-info">
                ℹ️ The ITR engine will analyze your profile and compliance data to determine whether ITR-1, ITR-2, ITR-3, or ITR-4 applies. The result will be cryptographically locked.
              </div>

              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? <><div className="spinner" />Determining ITR…</> : '🔍 Run ITR Determination →'}
              </button>
            </form>
          </div>
        )}

        {/* ── STEP 2: Create Filing Case ── */}
        {step === 2 && (
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Initialize Filing Case</div>
                <div className="card-subtitle">Your ITR type is determined and locked. Ready to create the filing.</div>
              </div>
            </div>

            {determination && (
              <div style={{
                background: 'var(--primary-muted)', border: '1px solid rgba(99,102,241,0.2)',
                borderRadius: 'var(--radius-sm)', padding: '1.25rem', marginBottom: '1.5rem'
              }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>
                  🔒 Locked Determination
                </div>
                <div className="grid-2" style={{ gap: '1rem' }}>
                  <div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-3)', marginBottom: '0.2rem' }}>ITR TYPE</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--primary)' }}>{determination.itr_type}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-3)', marginBottom: '0.2rem' }}>FINANCIAL YEAR</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-1)' }}>{fy}</div>
                  </div>
                </div>
              </div>
            )}

            {created ? (
              <div className="alert alert-success">
                ✅ Filing case created! Redirecting to Filing Management…
              </div>
            ) : (
              <button className="btn btn-success btn-lg btn-full" onClick={createFiling} disabled={loading}>
                {loading ? <><div className="spinner" />Creating Filing…</> : '🚀 Initialize Filing Case'}
              </button>
            )}
          </div>
        )}
      </div>
    </>
  );
}
