import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import CAAssignmentPage from '../CAAssignmentPage';
import { request } from '../../services/api';

// Mock API request utility
vi.mock('../../services/api', () => ({
  request: vi.fn(),
}));

// Mock useAuth to simulate a logged-in Taxpayer (sub: "user-123")
vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({
    token: 'header.eyJzdWIiOiJ1c2VyLTEyMyIsInByaW1hcnlfcm9sZSI6IklORElWSURVQUwifQ==.signature',
  }),
}));

describe('CA Assignment Workflow', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  const mockFiling = {
    id: 'filing-123-uuid',
    user_id: 'user-123',
    financial_year: '2025-26',
    current_state: 'DRAFT',
  };

  const mockCAs = [
    { id: 'ca-1-uuid', legal_name: 'CA Vikram Sen', email: 'vikram@ca.com' },
    { id: 'ca-2-uuid', legal_name: 'CA Amit Sharma', email: 'amit@ca.com' },
    { id: 'user-123', legal_name: 'Self CA', email: 'maav@gmail.com' }, // Matches sub/id of current taxpayer
  ];

  it('renders loading state initially', () => {
    request.mockReturnValue(new Promise(() => {})); // Never resolves
    render(
      <MemoryRouter initialEntries={['/filings/2025-26/delegate']}>
        <Routes>
          <Route path="/filings/:year/delegate" element={<CAAssignmentPage />} />
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByTestId('page-loader')).toBeInTheDocument();
  });

  it('renders empty CA list when no CAs are registered', async () => {
    request.mockResolvedValueOnce(mockFiling); // GET /filing/
    request.mockResolvedValueOnce([]); // GET /auth/cas

    render(
      <MemoryRouter initialEntries={['/filings/2025-26/delegate']}>
        <Routes>
          <Route path="/filings/:year/delegate" element={<CAAssignmentPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.queryByTestId('page-loader')).not.toBeInTheDocument();
    });

    expect(screen.getByTestId('empty-ca-state')).toBeInTheDocument();
    expect(screen.getByText('No CAs Available')).toBeInTheDocument();
  });

  it('prevents self-assignment and shows clear error feedback', async () => {
    request.mockResolvedValueOnce(mockFiling);
    request.mockResolvedValueOnce(mockCAs);

    render(
      <MemoryRouter initialEntries={['/filings/2025-26/delegate']}>
        <Routes>
          <Route path="/filings/:year/delegate" element={<CAAssignmentPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.queryByTestId('page-loader')).not.toBeInTheDocument();
    });

    // Click self-assignment CA item (ID matches our mocked sub "user-123")
    const selfItem = screen.getByTestId('ca-item-user-123');
    fireEvent.click(selfItem);

    expect(screen.getByTestId('error-alert')).toHaveTextContent('Self-assignment is not permitted.');
  });

  it('handles validation error for expired expiry date', async () => {
    request.mockResolvedValueOnce(mockFiling);
    request.mockResolvedValueOnce(mockCAs);

    render(
      <MemoryRouter initialEntries={['/filings/2025-26/delegate']}>
        <Routes>
          <Route path="/filings/:year/delegate" element={<CAAssignmentPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.queryByTestId('page-loader')).not.toBeInTheDocument();
    });

    // Select valid CA
    fireEvent.click(screen.getByTestId('ca-item-ca-1-uuid'));

    // Set an expired date in input
    const dateInput = screen.getByTestId('consent-expiry-input');
    fireEvent.change(dateInput, { target: { value: '2020-01-01' } });

    // Submit form
    fireEvent.submit(screen.getByTestId('consent-form'));

    await waitFor(() => {
      expect(screen.getByTestId('error-alert')).toHaveTextContent('Consent expiry date must be in the future.');
    });
  });

  it('completes the consent creation and CA assignment flow successfully', async () => {
    request.mockResolvedValueOnce(mockFiling); // GET /filing/
    request.mockResolvedValueOnce(mockCAs); // GET /auth/cas

    render(
      <MemoryRouter initialEntries={['/filings/2025-26/delegate']}>
        <Routes>
          <Route path="/filings/:year/delegate" element={<CAAssignmentPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.queryByTestId('page-loader')).not.toBeInTheDocument();
    });

    // Select valid CA
    fireEvent.click(screen.getByTestId('ca-item-ca-1-uuid'));
    expect(screen.getByTestId('selected-ca-banner')).toHaveTextContent('CA Vikram Sen');

    // Fill purpose
    const purposeInput = screen.getByTestId('consent-purpose-input');
    fireEvent.change(purposeInput, { target: { value: 'ITR review for FY 2025-26' } });

    // Mock Consent Creation API POST response
    request.mockResolvedValueOnce({
      id: 'consent-789-uuid',
      purpose: 'ITR review for FY 2025-26',
      scope: 'FULL_ACCESS',
      status: 'ACTIVE',
    });

    // Mock CA Assignment API POST response
    request.mockResolvedValueOnce({
      id: 'assignment-999-uuid',
      status: 'ACTIVE',
    });

    // Get the date input value before submitting because the element will be unmounted in success state
    const dateInputVal = screen.getByTestId('consent-expiry-input').value;

    // Submit form
    fireEvent.submit(screen.getByTestId('consent-form'));

    await waitFor(() => {
      expect(screen.getByTestId('success-state')).toBeInTheDocument();
    });

    // Assert API endpoints were hit correctly
    expect(request).toHaveBeenNthCalledWith(3, '/consent/', {
      method: 'POST',
      body: JSON.stringify({
        purpose: 'ITR review for FY 2025-26',
        scope: 'FULL_ACCESS',
        expiry_at: new Date(dateInputVal).toISOString(),
      }),
    });

    expect(request).toHaveBeenNthCalledWith(4, '/consent/assignments', {
      method: 'POST',
      body: JSON.stringify({
        filing_id: 'filing-123-uuid',
        ca_user_id: 'ca-1-uuid',
        consent_id: 'consent-789-uuid',
      }),
    });
  });

  it('handles delegation API errors cleanly', async () => {
    request.mockResolvedValueOnce(mockFiling);
    request.mockResolvedValueOnce(mockCAs);

    render(
      <MemoryRouter initialEntries={['/filings/2025-26/delegate']}>
        <Routes>
          <Route path="/filings/:year/delegate" element={<CAAssignmentPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.queryByTestId('page-loader')).not.toBeInTheDocument();
    });

    // Select valid CA
    fireEvent.click(screen.getByTestId('ca-item-ca-1-uuid'));

    // Mock Consent Creation API failure
    request.mockRejectedValueOnce(new Error('Internal database integrity constraint failed'));

    // Submit form
    fireEvent.submit(screen.getByTestId('consent-form'));

    await waitFor(() => {
      expect(screen.getByTestId('error-alert')).toHaveTextContent('Internal database integrity constraint failed');
    });
  });
});
