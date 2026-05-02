import React, { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { request } from '../services/api';

const Icons = {
  home: (
    <svg className="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
    </svg>
  ),
  filings: (
    <svg className="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  ),
  new: (
    <svg className="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
    </svg>
  ),
  logout: (
    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
    </svg>
  ),
};

// Decode JWT payload (no library needed — base64 decode middle segment)
function decodeJwt(token) {
  try {
    const payload = token.split('.')[1];
    return JSON.parse(atob(payload));
  } catch {
    return {};
  }
}

export default function Layout() {
  const { logout, token } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);

  // Decode role directly from JWT — always accurate, no extra API call
  const jwtPayload = token ? decodeJwt(token) : {};
  const primaryRole = jwtPayload.primary_role || jwtPayload.role || 'Individual';

  useEffect(() => {
    request('/taxpayer/profile')
      .then(setProfile)
      .catch(() => setProfile(null));
  }, [token]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Show Name from JWT, fallback to PAN from profile, then fallback to email
  const displayName = jwtPayload.name || profile?.pan || jwtPayload.email || 'Taxpayer';
  const initials = displayName.slice(0, 2).toUpperCase();

  // Residential status: only show if profile actually exists
  const residentialLabel = profile?.residential_status
    ? ` · ${profile.residential_status}`
    : ' · No Profile Yet';

  return (
    <div className="app-shell">
      {/* ── SIDEBAR ── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-logo-mark">
            <div className="logo-icon">M</div>
            <div className="logo-text">
              <strong>MaaV Solutions</strong>
              <span>Tax Filing Platform</span>
            </div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="sidebar-section">
            <div className="sidebar-section-label">Main</div>
            <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              {Icons.home}
              Dashboard
            </NavLink>
            <NavLink to="/filings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              {Icons.filings}
              My Filings
            </NavLink>
          </div>

          <div className="sidebar-section">
            <div className="sidebar-section-label">Actions</div>
            <NavLink to="/filings/new" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              {Icons.new}
              New Filing
            </NavLink>
          </div>
        </nav>

        <div className="sidebar-footer">
          <div className="user-chip">
            <div className="user-avatar">{initials}</div>
            <div className="user-info">
              <div className="user-name">{displayName}</div>
              <div className="user-role">{primaryRole}{residentialLabel}</div>
            </div>
            <button className="logout-btn" onClick={handleLogout} title="Logout">
              {Icons.logout}
            </button>
          </div>
        </div>
      </aside>

      {/* ── MAIN ── */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
