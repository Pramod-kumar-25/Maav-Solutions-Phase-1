import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { request } from '../services/api';

const FilingView = () => {
  const { id } = useParams();
  const [filing, setFiling] = useState(null);
  const [entries, setEntries] = useState([]);
  const [error, setError] = useState('');
  
  const [entryForm, setEntryForm] = useState({
    type: 'INCOME',
    amount: '',
    description: ''
  });

  useEffect(() => {
    fetchFilingDetails();
    fetchEntries();
  }, [id]);

  const fetchFilingDetails = async () => {
    try {
      // Best effort GET filing
      const data = await request(`/filing/?financial_year=${id}`);
      setFiling(data);
    } catch (err) {
      // If endpoint is missing, we still rely on state from patches later
      if (!filing) setFiling({ id, current_state: 'UNKNOWN (Try transitioning state)' });
    }
  };

  const fetchEntries = async () => {
    try {
      const data = await request(`/financial/`);
      // Filter entries by the current financial year
      setEntries((data || []).filter(e => e.financial_year === id));
    } catch (err) {
      setError("Could not fetch entries: " + err.message);
    }
  };

  const handleTransition = async (newStatus) => {
    try {
      const data = await request(`/filing/${id}/transition`, {
        method: 'POST',
        body: JSON.stringify({ next_state: newStatus })
      });
      setFiling(data);
      setError('');
    } catch (err) {
      setError(err.message);
    }
  };

  const addEntry = async (e) => {
    e.preventDefault();
    try {
      await request('/financial/', {
        method: 'POST',
        body: JSON.stringify({
          entry_type: entryForm.type,
          category: 'GENERAL',
          amount: parseFloat(entryForm.amount),
          financial_year: id,
          entry_date: new Date().toISOString().split('T')[0],
          description: entryForm.description
        })
      });
      setEntryForm({ ...entryForm, amount: '', description: '' });
      fetchEntries();
      setError('');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="container">
      <div className="header">
        <h1>Filing Management</h1>
        <Link to="/" className="btn btn-secondary">Back to Dashboard</Link>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{margin: 0}}>Case ID: <span style={{fontSize: '1rem', color: 'var(--text-secondary)'}}>{id}</span></h2>
            {filing?.financial_year && <p style={{marginTop: '0.5rem'}}>FY: {filing.financial_year}</p>}
          </div>
          <span className={`badge ${filing?.current_state?.toLowerCase() || 'draft'}`}>
            {filing?.current_state || 'LOADING'}
          </span>
        </div>

        <div style={{ marginTop: '2rem', display: 'flex', gap: '0.5rem' }}>
          <button className="btn" onClick={() => handleTransition('READY_FOR_REVIEW')} disabled={filing?.current_state !== 'DRAFT'}>Mark READY</button>
          <button className="btn" onClick={() => handleTransition('LOCKED')} disabled={filing?.current_state !== 'READY_FOR_REVIEW'}>Approve (LOCK)</button>
          <button className="btn" onClick={() => handleTransition('SUBMITTED')} disabled={filing?.current_state !== 'LOCKED'}>Mark SUBMITTED</button>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h2>Add Financial Entry</h2>
          <form onSubmit={addEntry} style={{ marginTop: '1rem' }}>
            <div className="form-group">
              <label>Entry Type</label>
              <select value={entryForm.type} onChange={e => setEntryForm({...entryForm, type: e.target.value})}>
                <option value="INCOME">INCOME</option>
                <option value="EXPENSE">EXPENSE</option>
              </select>
            </div>
            <div className="form-group">
              <label>Amount (₹)</label>
              <input type="number" step="0.01" required value={entryForm.amount} onChange={e => setEntryForm({...entryForm, amount: e.target.value})} />
            </div>
            <div className="form-group">
              <label>Description</label>
              <input type="text" required value={entryForm.description} onChange={e => setEntryForm({...entryForm, description: e.target.value})} />
            </div>
            <button type="submit" className="btn">Add Record</button>
          </form>
        </div>

        <div className="card">
          <h2>Financial Ledger</h2>
          {entries.length === 0 ? (
            <p style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>No entries aggregated yet.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Amount</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {entries.map(entry => (
                  <tr key={entry.id}>
                    <td><span className="badge" style={{backgroundColor: entry.entry_type === 'INCOME' ? '#d1fae5' : '#fee2e2', color: entry.entry_type === 'INCOME' ? '#065f46' : '#991b1b'}}>{entry.entry_type}</span></td>
                    <td>₹{entry.amount}</td>
                    <td>{entry.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};

export default FilingView;
