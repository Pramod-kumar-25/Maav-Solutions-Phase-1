import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { request } from '../services/api';

const STEPS = [
  { key: 'DRAFT', label: 'Draft', icon: '✏️', desc: 'Adding financial entries' },
  { key: 'READY_FOR_REVIEW', label: 'Ready for Review', icon: '🔍', desc: 'Entries finalized' },
  { key: 'LOCKED', label: 'Locked', icon: '🔒', desc: 'Taxpayer approved' },
  { key: 'SUBMITTED', label: 'Submitted', icon: '✅', desc: 'Filed to IT Dept.' },
];
const STATE_ORDER = ['DRAFT', 'READY_FOR_REVIEW', 'LOCKED', 'SUBMITTED'];
const STATE_NEXT = { DRAFT: 'READY_FOR_REVIEW', READY_FOR_REVIEW: 'LOCKED', LOCKED: 'SUBMITTED' };
const TRANSITION_LABELS = {
  DRAFT: { label: 'Mark Ready for Review', icon: '🔍', cls: 'btn-primary' },
  READY_FOR_REVIEW: { label: 'Approve & Lock Filing', icon: '🔒', cls: 'btn-primary' },
  LOCKED: { label: 'Submit to IT Department', icon: '🚀', cls: 'btn-success' },
};

export default function FilingDetail() {
  const { year } = useParams();
  const [filing, setFiling] = useState(null);
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [transitioning, setTransitioning] = useState(false);
  const [addingEntry, setAddingEntry] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const [entryForm, setEntryForm] = useState({ type: 'INCOME', amount: '', description: '', category: 'GENERAL' });
  const [flags, setFlags] = useState([]);
  const [runningCompliance, setRunningCompliance] = useState(false);
  const [complianceMsg, setComplianceMsg] = useState('');

  useEffect(() => {
    fetchAll();
  }, [year]);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [f, e, fl] = await Promise.all([
        request(`/filing/?financial_year=${year}`),
        request('/financial/').then(d => (d || []).filter(e => e.financial_year === year)).catch(() => []),
        request(`/compliance/?financial_year=${year}`).catch(() => []),
      ]);
      setFiling(f);
      setEntries(e);
      setFlags(fl || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTransition = async () => {
    const nextState = STATE_NEXT[filing.current_state];
    if (!nextState) return;
    setTransitioning(true); setError(''); setSuccessMsg('');
    try {
      const data = await request(`/filing/${year}/transition`, {
        method: 'POST',
        body: JSON.stringify({ next_state: nextState }),
      });
      setFiling(data);
      setSuccessMsg(`✅ Successfully moved to ${nextState.replace(/_/g, ' ')}`);
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch (err) { setError(err.message); }
    finally { setTransitioning(false); }
  };

  const handleAddEntry = async (e) => {
    e.preventDefault();
    setAddingEntry(true); setError('');
    try {
      await request('/financial/', {
        method: 'POST',
        body: JSON.stringify({
          entry_type: entryForm.type,
          category: entryForm.category || 'GENERAL',
          amount: parseFloat(entryForm.amount),
          financial_year: year,
          entry_date: new Date().toISOString().split('T')[0],
          description: entryForm.description,
        }),
      });
      setEntryForm({ type: 'INCOME', amount: '', description: '', category: 'GENERAL' });
      const e2 = await request('/financial/').then(d => (d || []).filter(e => e.financial_year === year));
      setEntries(e2);
    } catch (err) { setError(err.message); }
    finally { setAddingEntry(false); }
  };

  const handleDeleteEntry = async (id) => {
    if (isTerminal) return;
    if (!window.confirm('Are you sure you want to delete this record?')) return;
    try {
      await request(`/financial/${id}`, { method: 'DELETE' });
      setEntries(entries.filter(e => e.id !== id));
    } catch (err) { setError(err.message); }
  };

  const handleRunCompliance = async () => {
    setRunningCompliance(true); setComplianceMsg(''); setError('');
    try {
      await request('/compliance/evaluate', {
        method: 'POST',
        body: JSON.stringify({ financial_year: year }),
      });
      const fl = await request(`/compliance/?financial_year=${year}`);
      setFlags(fl || []);
      const newFlags = (fl || []).filter(f => !f.is_resolved);
      setComplianceMsg(newFlags.length > 0
        ? `⚠️ ${newFlags.length} compliance flag(s) detected!`
        : '✅ No compliance violations found.');
    } catch (err) { setError(err.message); }
    finally { setRunningCompliance(false); }
  };

  const handleResolveFlag = async (flagId) => {
    try {
      await request(`/compliance/${flagId}/resolve`, {
        method: 'POST',
        body: JSON.stringify({ resolution_notes: 'Manually reviewed and resolved.' }),
      });
      const fl = await request(`/compliance/?financial_year=${year}`);
      setFlags(fl || []);
    } catch (err) { setError(err.message); }
  };

  const currentStateIdx = STATE_ORDER.indexOf(filing?.current_state);
  const isTerminal = filing?.current_state === 'SUBMITTED';
  const totalIncome = entries.filter(e => e.entry_type === 'INCOME').reduce((s, e) => s + parseFloat(e.amount || 0), 0);
  const totalExpense = entries.filter(e => e.entry_type === 'EXPENSE').reduce((s, e) => s + parseFloat(e.amount || 0), 0);

  if (loading) return (
    <div className="page-loader">
      <div className="spinner" style={{ borderColor: 'var(--border)', borderTopColor: 'var(--primary)' }} />
      <span className="text-muted">Loading filing…</span>
    </div>
  );

  if (!filing && !loading) return (
    <>
      <div className="page-header">
        <div className="page-header-left">
          <h1>Filing Not Found</h1>
          <div className="breadcrumb"><Link to="/">Dashboard</Link> › <Link to="/filings">Filings</Link> › {year}</div>
        </div>
      </div>
      <div className="page-body">
        <div className="card">
          <div className="empty-state">
            <div className="empty-icon">🔍</div>
            <h3>No filing found for FY {year}</h3>
            <p>This filing case doesn't exist yet. Initialize one to start the workflow.</p>
            <Link to="/filings/new" className="btn btn-primary mt-2">Initialize Filing</Link>
          </div>
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* Page Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h1>FY {year} Filing</h1>
          <div className="breadcrumb">
            <Link to="/">Dashboard</Link> › <Link to="/filings">Filings</Link> › {year}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <span className={`badge badge-${filing.current_state?.toLowerCase()}`} style={{ fontSize: '0.8rem', padding: '0.4rem 1rem' }}>
            {filing.current_state?.replace(/_/g, ' ')}
          </span>
        </div>
      </div>

      <div className="page-body">
        {error && <div className="alert alert-error">⚠️ {error}</div>}
        {successMsg && <div className="alert alert-success">{successMsg}</div>}

        {/* State Machine Stepper */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Filing Lifecycle</div>
              <div className="card-subtitle">Orchestration workflow — forward-only state machine</div>
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-3)' }}>
              Case ID: <code style={{ background: 'var(--surface-2)', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>{filing.id?.slice(0, 18)}…</code>
            </div>
          </div>

          {/* Stepper */}
          <div className="stepper" style={{ marginBottom: '1.5rem' }}>
            {STEPS.map((s, i) => (
              <div key={s.key} className={`step ${i < currentStateIdx ? 'done' : ''} ${i === currentStateIdx ? 'active' : ''}`}>
                <div className="step-dot">{i < currentStateIdx ? '✓' : s.icon}</div>
                <div className="step-label">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Transition Button */}
          {!isTerminal && TRANSITION_LABELS[filing.current_state] && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', background: 'var(--surface-2)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>Next Action</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-2)', marginTop: '0.15rem' }}>
                  {STEPS[currentStateIdx + 1]?.desc || 'Complete next step'}
                </div>
              </div>
              <button
                className={`btn ${TRANSITION_LABELS[filing.current_state].cls}`}
                onClick={handleTransition}
                disabled={transitioning}
              >
                {transitioning
                  ? <><div className="spinner" />Processing…</>
                  : <>{TRANSITION_LABELS[filing.current_state].icon} {TRANSITION_LABELS[filing.current_state].label}</>
                }
              </button>
            </div>
          )}

          {isTerminal && (
            <div className="alert alert-success">
              🎉 This filing has been successfully submitted. No further actions required.
              {filing.submitted_at && <span style={{ marginLeft: '0.5rem', opacity: 0.7, fontSize: '0.8rem' }}>
                Submitted on {new Date(filing.submitted_at).toLocaleString('en-IN')}
              </span>}
            </div>
          )}
        </div>

        {/* Summary Stats */}
        {entries.length > 0 && (
          <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
            <div className="stat-card">
              <div className="stat-icon" style={{ background: 'var(--success-muted)' }}>💰</div>
              <div className="stat-content">
                <div className="stat-label">Total Income</div>
                <div className="stat-value" style={{ fontSize: '1.3rem', color: 'var(--success)' }}>
                  ₹{totalIncome.toLocaleString('en-IN')}
                </div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon" style={{ background: 'var(--danger-muted)' }}>💸</div>
              <div className="stat-content">
                <div className="stat-label">Total Expenses</div>
                <div className="stat-value" style={{ fontSize: '1.3rem', color: 'var(--danger)' }}>
                  ₹{totalExpense.toLocaleString('en-IN')}
                </div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon" style={{ background: 'var(--primary-muted)' }}>📊</div>
              <div className="stat-content">
                <div className="stat-label">Net Taxable</div>
                <div className="stat-value" style={{ fontSize: '1.3rem', color: 'var(--primary)' }}>
                  ₹{(totalIncome - totalExpense).toLocaleString('en-IN')}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Two-column: Add Entry + Ledger */}
        <div className="grid-2">
          {/* Add Financial Entry */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Add Financial Entry</div>
                <div className="card-subtitle">Record income or expense for this FY</div>
              </div>
            </div>
            {isTerminal ? (
              <div className="alert alert-info">🔒 Filing is submitted. No new entries can be added.</div>
            ) : (
              <form onSubmit={handleAddEntry}>
                <div className="form-group">
                  <label>Entry Type</label>
                  <select value={entryForm.type} onChange={e => setEntryForm({ ...entryForm, type: e.target.value })}>
                    <option value="INCOME">💰 Income</option>
                    <option value="EXPENSE">💸 Expense</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Amount (₹)</label>
                  <input type="number" step="0.01" min="0" required placeholder="0.00"
                    value={entryForm.amount}
                    onChange={e => setEntryForm({ ...entryForm, amount: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Category</label>
                  <select value={entryForm.category} onChange={e => setEntryForm({ ...entryForm, category: e.target.value })}>
                    <option value="GENERAL">General</option>
                    <option value="SALARY">Salary</option>
                    <option value="BUSINESS">Business</option>
                    <option value="PROFESSION">Profession</option>
                    <option value="FREELANCE">Freelance</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Description</label>
                  <input type="text" required placeholder="e.g., Consulting Fee, Monthly Salary…"
                    value={entryForm.description}
                    onChange={e => setEntryForm({ ...entryForm, description: e.target.value })} />
                </div>
                <button type="submit" className="btn btn-primary" disabled={addingEntry}>
                  {addingEntry ? <><div className="spinner" />Adding…</> : '+ Add Record'}
                </button>
              </form>
            )}
          </div>

          {/* Financial Ledger */}
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border)' }}>
              <div className="card-title">Financial Ledger</div>
              <div className="card-subtitle">{entries.length} entr{entries.length !== 1 ? 'ies' : 'y'} for FY {year}</div>
            </div>

            {entries.length === 0 ? (
              <div className="empty-state" style={{ padding: '3rem 1.5rem' }}>
                <div className="empty-icon">📋</div>
                <h3>No entries yet</h3>
                <p>Add income and expense records using the form on the left.</p>
              </div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Amount</th>
                    <th>Description</th>
                    {!isTerminal && <th>Action</th>}
                  </tr>
                </thead>
                <tbody>
                  {entries.map(e => (
                    <tr key={e.id}>
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                          <span style={{
                            display: 'inline-flex', alignItems: 'center', gap: '0.3rem',
                            padding: '0.2rem 0.6rem', borderRadius: '100px', fontSize: '0.72rem', fontWeight: 700,
                            background: e.entry_type === 'INCOME' ? 'var(--success-muted)' : 'var(--danger-muted)',
                            color: e.entry_type === 'INCOME' ? '#065f46' : '#991b1b',
                            width: 'fit-content'
                          }}>
                            {e.entry_type === 'INCOME' ? '💰' : '💸'} {e.entry_type}
                          </span>
                          <span style={{ fontSize: '0.65rem', color: 'var(--text-3)', marginTop: '0.2rem', paddingLeft: '0.4rem' }}>
                            🏷️ {e.category || 'GENERAL'}
                          </span>
                        </div>
                      </td>
                      <td style={{ fontWeight: 700, color: e.entry_type === 'INCOME' ? 'var(--success)' : 'var(--danger)' }}>
                        {e.entry_type === 'EXPENSE' ? '-' : '+'}₹{parseFloat(e.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td style={{ color: 'var(--text-2)', fontSize: '0.85rem' }}>{e.description}</td>
                      {!isTerminal && (
                        <td>
                          <button
                            className="btn btn-ghost btn-sm"
                            style={{ color: 'var(--danger)', padding: '0.2rem' }}
                            onClick={() => handleDeleteEntry(e.id)}
                            title="Delete Record"
                          >
                            <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* ── COMPLIANCE ENGINE SECTION ── */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">🛡️ Compliance Engine</div>
              <div className="card-subtitle">Run automated compliance checks against your financial entries</div>
            </div>
            <button
              className="btn btn-primary btn-sm"
              onClick={handleRunCompliance}
              disabled={runningCompliance}
            >
              {runningCompliance ? <><div className="spinner" />Evaluating…</> : '▶ Run Compliance Check'}
            </button>
          </div>

          {complianceMsg && (
            <div className={`alert ${complianceMsg.startsWith('✅') ? 'alert-success' : 'alert-warning'}`} style={{ marginBottom: '1rem' }}>
              {complianceMsg}
            </div>
          )}

          {flags.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-3)', fontSize: '0.875rem' }}>
              No compliance flags yet. Click "Run Compliance Check" to evaluate your entries.
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Severity</th>
                  <th>Description</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {flags.map(f => (
                  <tr key={f.id}>
                    <td><code style={{ background: 'var(--surface-2)', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.8rem' }}>{f.flag_code}</code></td>
                    <td>
                      <span style={{
                        padding: '0.2rem 0.6rem', borderRadius: '100px', fontSize: '0.72rem', fontWeight: 700,
                        background: f.severity === 'CRITICAL' ? 'var(--danger-muted)' : f.severity === 'HIGH' ? 'var(--warning-muted)' : 'var(--primary-muted)',
                        color: f.severity === 'CRITICAL' ? '#991b1b' : f.severity === 'HIGH' ? '#92400e' : 'var(--primary)',
                      }}>
                        {f.severity === 'CRITICAL' ? '🔴' : f.severity === 'HIGH' ? '🟠' : '🟡'} {f.severity}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.83rem', color: 'var(--text-2)', maxWidth: 300 }}>{f.description}</td>
                    <td>
                      <span style={{
                        padding: '0.2rem 0.6rem', borderRadius: '100px', fontSize: '0.72rem', fontWeight: 600,
                        background: f.is_resolved ? 'var(--success-muted)' : 'var(--danger-muted)',
                        color: f.is_resolved ? '#065f46' : '#991b1b',
                      }}>
                        {f.is_resolved ? '✅ Resolved' : '🔴 Open'}
                      </span>
                    </td>
                    <td>
                      {!f.is_resolved && (
                        <button className="btn btn-ghost btn-sm" onClick={() => handleResolveFlag(f.id)}>
                          Resolve
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </>
  );
}
