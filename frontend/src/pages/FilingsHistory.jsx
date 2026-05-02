import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { request } from '../services/api';

const YEARS = ['2023-24', '2022-23', '2024-25'];

const STATE_COLORS = {
  DRAFT: 'badge-draft',
  READY_FOR_REVIEW: 'badge-ready_for_review',
  LOCKED: 'badge-locked',
  SUBMITTED: 'badge-submitted',
};
const STATE_ICONS = { DRAFT: '✏️', READY_FOR_REVIEW: '🔍', LOCKED: '🔒', SUBMITTED: '✅' };

export default function FilingsHistory() {
  const navigate = useNavigate();
  const [filings, setFilings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAll = async () => {
      const results = [];
      for (const y of YEARS) {
        try {
          const d = await request(`/filing/?financial_year=${y}`);
          results.push(d);
        } catch {}
      }
      setFilings(results);
      setLoading(false);
    };
    fetchAll();
  }, []);

  if (loading) return (
    <div className="page-loader">
      <div className="spinner" style={{ borderColor: 'var(--border)', borderTopColor: 'var(--primary)' }} />
      <span className="text-muted">Loading filings…</span>
    </div>
  );

  return (
    <>
      <div className="page-header">
        <div className="page-header-left">
          <h1>My Filings</h1>
          <div className="breadcrumb">
            <Link to="/">Dashboard</Link> › All Filings
          </div>
        </div>
        <Link to="/filings/new" className="btn btn-primary btn-sm">
          <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
          </svg>
          New Filing
        </Link>
      </div>

      <div className="page-body">
        {filings.length === 0 ? (
          <div className="card">
            <div className="empty-state">
              <div className="empty-icon">📂</div>
              <h3>No filings found</h3>
              <p>You haven't initialized any tax filings yet. Start one to begin the orchestration workflow.</p>
              <Link to="/filings/new" className="btn btn-primary mt-2">Initialize First Filing</Link>
            </div>
          </div>
        ) : (
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <div className="card-title">All Filing Cases</div>
                <div className="card-subtitle">{filings.length} filing{filings.length !== 1 ? 's' : ''} found</div>
              </div>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Financial Year</th>
                  <th>Case ID</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filings.map(f => (
                  <tr key={f.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/filings/${f.financial_year}`)}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                        <span style={{ fontSize: '1.2rem' }}>{STATE_ICONS[f.current_state] || '📄'}</span>
                        <div>
                          <div style={{ fontWeight: 700, color: 'var(--text-1)' }}>FY {f.financial_year}</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-3)' }}>ITR Filing</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <code style={{ fontSize: '0.78rem', color: 'var(--text-2)', background: 'var(--surface-2)', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
                        {f.id?.slice(0, 16)}…
                      </code>
                    </td>
                    <td>
                      <span className={`badge ${STATE_COLORS[f.current_state] || ''}`}>
                        {f.current_state?.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-2)', fontSize: '0.85rem' }}>
                      {f.created_at ? new Date(f.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
                    </td>
                    <td>
                      <button className="btn btn-ghost btn-sm" onClick={(e) => { e.stopPropagation(); navigate(`/filings/${f.financial_year}`); }}>
                        Open →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
