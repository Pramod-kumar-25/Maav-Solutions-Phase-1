import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ConsentDashboard from '../ConsentDashboard';
import ConsentDetail from '../ConsentDetail';
import { request } from '../../services/api';

// Mock the API service
vi.mock('../../services/api', () => ({
  request: vi.fn(),
}));

describe('Consent Management Workspace', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe('ConsentDashboard Component', () => {
    it('renders loading state initially', () => {
      request.mockReturnValue(new Promise(() => {})); // Never resolves
      render(
        <MemoryRouter>
          <ConsentDashboard />
        </MemoryRouter>
      );
      expect(screen.getByTestId('page-loader')).toBeInTheDocument();
    });

    it('renders empty state when there are no consents', async () => {
      request.mockResolvedValue([]);
      render(
        <MemoryRouter>
          <ConsentDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.queryByTestId('page-loader')).not.toBeInTheDocument();
      });

      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
      expect(screen.getByText('No consents granted')).toBeInTheDocument();
    });

    it('renders error state on API failure', async () => {
      request.mockRejectedValue(new Error('Network Error'));
      render(
        <MemoryRouter>
          <ConsentDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.queryByTestId('page-loader')).not.toBeInTheDocument();
      });

      expect(screen.getByTestId('error-alert')).toHaveTextContent('Network Error');
    });

    it('renders dashboard with stats and list of consents', async () => {
      const mockConsents = [
        {
          id: '11111111-1111-1111-1111-111111111111',
          purpose: 'Tax Preparation 2025',
          scope: 'FULL_ACCESS',
          status: 'ACTIVE',
          expiry_at: '2026-12-31T23:59:59Z',
          granted_at: '2025-01-01T10:00:00Z',
        },
        {
          id: '22222222-2222-2222-2222-222222222222',
          purpose: 'Auditing 2024',
          scope: 'READ_ONLY',
          status: 'REVOKED',
          expiry_at: '2026-12-31T23:59:59Z',
          granted_at: '2025-01-01T10:00:00Z',
        },
        {
          id: '33333333-3333-3333-3333-333333333333',
          purpose: 'Old Tax Prep',
          scope: 'LIMITED',
          status: 'EXPIRED',
          expiry_at: '2025-01-01T23:59:59Z',
          granted_at: '2024-01-01T10:00:00Z',
        },
      ];

      request.mockResolvedValue(mockConsents);

      render(
        <MemoryRouter>
          <ConsentDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.queryByTestId('page-loader')).not.toBeInTheDocument();
      });

      // Check stats cards values
      expect(screen.getByTestId('stat-active')).toHaveTextContent('1');
      expect(screen.getByTestId('stat-revoked')).toHaveTextContent('1');
      expect(screen.getByTestId('stat-expired')).toHaveTextContent('1');

      // Check list entries
      expect(screen.getByText('Tax Preparation 2025')).toBeInTheDocument();
      expect(screen.getByText('Auditing 2024')).toBeInTheDocument();
      expect(screen.getByText('Old Tax Prep')).toBeInTheDocument();

      expect(screen.getByTestId('consent-card-11111111-1111-1111-1111-111111111111')).toBeInTheDocument();
    });
  });

  describe('ConsentDetail Component', () => {
    const mockActiveConsent = {
      id: '12345678-1234-1234-1234-1234567890ab',
      purpose: 'Tax Preparation 2025',
      scope: 'FULL_ACCESS',
      status: 'ACTIVE',
      expiry_at: '2026-12-31T23:59:59Z',
      granted_at: '2025-01-01T10:00:00Z',
    };

    const mockRevokedConsent = {
      ...mockActiveConsent,
      status: 'REVOKED',
    };

    it('renders loading state initially', () => {
      request.mockReturnValue(new Promise(() => {}));
      render(
        <MemoryRouter initialEntries={['/settings/consent/12345678-1234-1234-1234-1234567890ab']}>
          <Routes>
            <Route path="/settings/consent/:id" element={<ConsentDetail />} />
          </Routes>
        </MemoryRouter>
      );
      expect(screen.getByTestId('page-loader')).toBeInTheDocument();
    });

    it('renders consent detail info', async () => {
      request.mockResolvedValue(mockActiveConsent);

      render(
        <MemoryRouter initialEntries={['/settings/consent/12345678-1234-1234-1234-1234567890ab']}>
          <Routes>
            <Route path="/settings/consent/:id" element={<ConsentDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.queryByTestId('page-loader')).not.toBeInTheDocument();
      });

      expect(screen.getByTestId('details-purpose')).toHaveTextContent('Tax Preparation 2025');
      expect(screen.getByTestId('details-scope')).toHaveTextContent('FULL_ACCESS');
      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
      expect(screen.getByTestId('revoke-btn')).toBeInTheDocument();
    });

    it('shows inactive message when consent is already revoked', async () => {
      request.mockResolvedValue(mockRevokedConsent);

      render(
        <MemoryRouter initialEntries={['/settings/consent/12345678-1234-1234-1234-1234567890ab']}>
          <Routes>
            <Route path="/settings/consent/:id" element={<ConsentDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.queryByTestId('page-loader')).not.toBeInTheDocument();
      });

      expect(screen.getByTestId('inactive-consent-state')).toBeInTheDocument();
      expect(screen.queryByTestId('revoke-btn')).not.toBeInTheDocument();
    });

    it('executes revocation flow successfully', async () => {
      // 1. Initial GET
      request.mockResolvedValueOnce(mockActiveConsent);

      render(
        <MemoryRouter initialEntries={['/settings/consent/12345678-1234-1234-1234-1234567890ab']}>
          <Routes>
            <Route path="/settings/consent/:id" element={<ConsentDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.queryByTestId('page-loader')).not.toBeInTheDocument();
      });

      // 2. Click revoke button to show confirmation form
      fireEvent.click(screen.getByTestId('revoke-btn'));
      expect(screen.getByTestId('revoke-form')).toBeInTheDocument();

      // 3. Fill and submit revocation reason
      const input = screen.getByTestId('revocation-reason-input');
      fireEvent.change(input, { target: { value: 'Revoking due to audit completion' } });

      // Mock the POST request (revocation API call)
      request.mockResolvedValueOnce({ message: 'Success' });
      // Mock subsequent GET request (refreshed data showing REVOKED status)
      request.mockResolvedValueOnce(mockRevokedConsent);

      fireEvent.click(screen.getByTestId('confirm-revoke-btn'));

      await waitFor(() => {
        expect(screen.getByTestId('success-alert')).toHaveTextContent('Consent successfully revoked.');
      });

      // Verification of POST payload
      expect(request).toHaveBeenCalledWith('/consent/12345678-1234-1234-1234-1234567890ab/revoke', {
        method: 'POST',
        body: JSON.stringify({ reason: 'Revoking due to audit completion' })
      });
    });

    it('displays error when revocation fails', async () => {
      request.mockResolvedValueOnce(mockActiveConsent);

      render(
        <MemoryRouter initialEntries={['/settings/consent/12345678-1234-1234-1234-1234567890ab']}>
          <Routes>
            <Route path="/settings/consent/:id" element={<ConsentDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.queryByTestId('page-loader')).not.toBeInTheDocument();
      });

      fireEvent.click(screen.getByTestId('revoke-btn'));

      const input = screen.getByTestId('revocation-reason-input');
      fireEvent.change(input, { target: { value: 'Revoking due to audit completion' } });

      // Mock revocation POST request failure
      request.mockRejectedValueOnce(new Error('Revocation failed: invalid state'));

      fireEvent.click(screen.getByTestId('confirm-revoke-btn'));

      await waitFor(() => {
        expect(screen.getByTestId('action-error-alert')).toHaveTextContent('Revocation failed: invalid state');
      });
    });
  });
});
