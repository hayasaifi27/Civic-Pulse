import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import { Landing } from './pages/Landing';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { CitizenDashboard } from './pages/CitizenDashboard';
import { SubmitReport } from './pages/SubmitReport';
import { ReportDetail } from './pages/ReportDetail';
import { MapView } from './pages/MapView';
import { MainLayout } from './layouts/MainLayout';
import { AuthLayout } from './layouts/AuthLayout';

function PrivateRoute({ children, allowedRoles }: { children: React.ReactNode; allowedRoles?: string[] }) {
  const { user, isLoading } = useAuth();
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-civic-teal border-t-transparent" />
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return <>{children}</>;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-civic-teal border-t-transparent" />
      </div>
    );
  }
  
  if (user) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
        <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
      </Route>
      
      <Route element={<MainLayout />}>
        <Route path="/dashboard" element={<PrivateRoute><CitizenDashboard /></PrivateRoute>} />
        <Route path="/submit" element={<PrivateRoute allowedRoles={['citizen']}><SubmitReport /></PrivateRoute>} />
        <Route path="/reports/:id" element={<PrivateRoute><ReportDetail /></PrivateRoute>} />
        <Route path="/map" element={<PrivateRoute allowedRoles={['citizen', 'admin', 'supervisor']}><MapView /></PrivateRoute>} />
        <Route path="/my-reports" element={<PrivateRoute allowedRoles={['citizen']}><CitizenDashboard /></PrivateRoute>} />
      </Route>
      
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}