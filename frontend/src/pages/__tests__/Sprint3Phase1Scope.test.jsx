import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import Register from '../Register';
import Layout from '../../components/Layout';
import App, { TaxpayerRoute } from '../../App';
import { useAuth } from '../../hooks/useAuth';

// Mock request API
vi.mock('../../services/api', () => ({
  request: vi.fn(() => Promise.resolve({})),
}));

// Mock useAuth
vi.mock('../../hooks/useAuth', () => ({
  useAuth: vi.fn(),
}));

describe('Sprint 3: Phase-1 Scope Lock', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe('Registration Form Role Options', () => {
    it('exposes INDIVIDUAL and CA role options but hides BUSINESS', () => {
      useAuth.mockReturnValue({
        register: vi.fn(),
      });

      render(
        <MemoryRouter>
          <Register />
        </MemoryRouter>
      );

      const selectElement = screen.getByRole('combobox');
      const options = Array.from(selectElement.options).map(opt => opt.value);

      expect(options).toContain('INDIVIDUAL');
      expect(options).toContain('CA');
      expect(options).not.toContain('BUSINESS');
    });
  });

  describe('TaxpayerRoute Guard Visibility', () => {
    it('allows INDIVIDUAL taxpayer role to pass through', () => {
      // Mock token for INDIVIDUAL
      useAuth.mockReturnValue({
        token: 'header.eyJzdWIiOiJ1c2VyLTEyMyIsInByaW1hcnlfcm9sZSI6IklORElWSURVQUwifQ==.signature',
      });

      render(
        <MemoryRouter initialEntries={['/test-taxpayer']}>
          <Routes>
            <Route path="/test-taxpayer" element={
              <TaxpayerRoute>
                <div data-testid="protected-content">Access Granted</div>
              </TaxpayerRoute>
            } />
            <Route path="/" element={<div data-testid="dashboard">Dashboard</div>} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
      expect(screen.queryByTestId('dashboard')).not.toBeInTheDocument();
    });

    it('redirects/blocks BUSINESS role from accessing taxpayer routes', () => {
      // Mock token for BUSINESS
      useAuth.mockReturnValue({
        token: 'header.eyJzdWIiOiJ1c2VyLTEyMyIsInByaW1hcnlfcm9sZSI6IkJVU0lORVNTIn0=.signature',
      });

      render(
        <MemoryRouter initialEntries={['/test-taxpayer']}>
          <Routes>
            <Route path="/test-taxpayer" element={
              <TaxpayerRoute>
                <div data-testid="protected-content">Access Granted</div>
              </TaxpayerRoute>
            } />
            <Route path="/" element={<div data-testid="dashboard">Redirected Dashboard</div>} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      expect(screen.getByTestId('dashboard')).toBeInTheDocument();
    });
  });

  describe('Layout Navigation Visibility', () => {
    it('shows Consent Manager link in navigation for INDIVIDUAL', async () => {
      useAuth.mockReturnValue({
        token: 'header.eyJzdWIiOiJ1c2VyLTEyMyIsInByaW1hcnlfcm9sZSI6IklORElWSURVQUwifQ==.signature',
        logout: vi.fn(),
      });

      render(
        <MemoryRouter>
          <Layout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Consent Manager/i)).toBeInTheDocument();
      });
    });

    it('hides Consent Manager link in navigation for BUSINESS', async () => {
      useAuth.mockReturnValue({
        token: 'header.eyJzdWIiOiJ1c2VyLTEyMyIsInByaW1hcnlfcm9sZSI6IkJVU0lORVNTIn0=.signature',
        logout: vi.fn(),
      });

      render(
        <MemoryRouter>
          <Layout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.queryByText(/Consent Manager/i)).not.toBeInTheDocument();
      });
    });
  });
});
