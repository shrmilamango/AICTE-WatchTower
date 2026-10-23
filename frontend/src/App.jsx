import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth/AuthContext';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';

import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Applications } from './pages/Applications';
import { ApplicationDetail } from './pages/ApplicationDetail';
import { TasksQueue } from './pages/TasksQueue';
import { EvcPortal } from './pages/EvcPortal';
import { CompliancePortal } from './pages/CompliancePortal';
import { RiskMatrix } from './pages/RiskMatrix';
import { AuditTrail } from './pages/AuditTrail';
import { AdminConfig } from './pages/AdminConfig';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '60px 24px', textAlign: 'center', maxWidth: '600px', margin: '40px auto', background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}>
          <h2 style={{ color: '#dc2626', marginBottom: '8px', fontSize: '1.4rem' }}>Application Render Notice</h2>
          <p style={{ color: '#475569', fontSize: '0.9rem', marginBottom: '20px' }}>
            A temporary issue occurred while rendering this view: {this.state.error?.message || 'Unknown error'}
          </p>
          <button
            onClick={() => { this.setState({ hasError: false }); window.location.href = '/dashboard'; }}
            className="btn btn-primary"
          >
            Reload Dashboard
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

// Protected Route Guard (Rule 1.2: Role-based route guard)
const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', color: 'var(--text-muted)' }}>Loading AICTE Watchtower...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div style={{ padding: '60px 20px', textAlign: 'center' }}>
        <h2 style={{ color: '#dc2626', marginBottom: '8px' }}>403 — Unauthorized Resource Access</h2>
        <p style={{ color: 'var(--text-secondary)' }}>Your role '{user.role}' does not have sufficient clearance to view this module.</p>
      </div>
    );
  }

  return children;
};

// Main App Layout Shell
const AppLayout = ({ children }) => {
  return (
    <ErrorBoundary>
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Navbar />
        <div style={{ display: 'flex', flex: 1 }}>
          <Sidebar />
          <main style={{
            flex: 1,
            padding: '28px 32px',
            maxWidth: '1440px',
            margin: '0 auto',
            width: '100%',
            overflowX: 'hidden'
          }}>
            {children}
          </main>
        </div>
      </div>
    </ErrorBoundary>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <Dashboard />
                </AppLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/applications"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <Applications />
                </AppLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/applications/:id"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <ApplicationDetail />
                </AppLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/tasks"
            element={
              <ProtectedRoute allowedRoles={['SCRUTINY_OFFICER', 'EVC_COORDINATOR', 'COMMITTEE_MEMBER', 'AUTHORISED_OFFICIAL', 'ADMIN', 'AUDITOR']}>
                <AppLayout>
                  <TasksQueue />
                </AppLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/evc"
            element={
              <ProtectedRoute allowedRoles={['EVC_COORDINATOR', 'ADMIN', 'AUTHORISED_OFFICIAL', 'AUDITOR']}>
                <AppLayout>
                  <EvcPortal />
                </AppLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/committee"
            element={
              <ProtectedRoute allowedRoles={['COMMITTEE_MEMBER', 'ADMIN', 'AUTHORISED_OFFICIAL', 'AUDITOR']}>
                <AppLayout>
                  <TasksQueue />
                </AppLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/compliance"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <CompliancePortal />
                </AppLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/risk"
            element={
              <ProtectedRoute allowedRoles={['SCRUTINY_OFFICER', 'EVC_COORDINATOR', 'COMMITTEE_MEMBER', 'AUTHORISED_OFFICIAL', 'ADMIN', 'AUDITOR']}>
                <AppLayout>
                  <RiskMatrix />
                </AppLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/audit"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'AUDITOR']}>
                <AppLayout>
                  <AuditTrail />
                </AppLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/config"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <AppLayout>
                  <AdminConfig />
                </AppLayout>
              </ProtectedRoute>
            }
          />

          {/* Catch-all redirect to Dashboard */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
