import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import NewFiling from './pages/NewFiling';
import FilingDetail from './pages/FilingDetail';
import FilingsHistory from './pages/FilingsHistory';
import ConsentDashboard from './pages/ConsentDashboard';
import ConsentDetail from './pages/ConsentDetail';
import CAAssignmentPage from './pages/CAAssignmentPage';

const PrivateRoute = ({ children }) => {
  const { token } = useAuth();
  return token ? children : <Navigate to="/login" replace />;
};

export const TaxpayerRoute = ({ children }) => {
  const { token } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  try {
    const payload = token.split('.')[1];
    const jwtPayload = JSON.parse(atob(payload));
    const role = jwtPayload.primary_role || jwtPayload.role;
    if (role === 'INDIVIDUAL') {
      return children;
    }
  } catch {}
  return <Navigate to="/" replace />;
};

const AppRoutes = () => {
  const { token } = useAuth();
  return (
    <Routes>
      <Route path="/login" element={!token ? <Login /> : <Navigate to="/" replace />} />
      <Route path="/register" element={!token ? <Register /> : <Navigate to="/" replace />} />
      <Route element={<PrivateRoute><Layout /></PrivateRoute>}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/filings" element={<FilingsHistory />} />
        <Route path="/filings/new" element={<NewFiling />} />
        <Route path="/filings/:year" element={<FilingDetail />} />
        <Route path="/filings/:year/delegate" element={<TaxpayerRoute><CAAssignmentPage /></TaxpayerRoute>} />
        <Route path="/settings/consent" element={<TaxpayerRoute><ConsentDashboard /></TaxpayerRoute>} />
        <Route path="/settings/consent/:id" element={<TaxpayerRoute><ConsentDetail /></TaxpayerRoute>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}
