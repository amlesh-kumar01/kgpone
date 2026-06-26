import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Marketplace from './pages/Marketplace';

// Layouts
import AuthLayout from './layouts/AuthLayout';
import DashboardLayout from './layouts/DashboardLayout';
import AcademicLayout from './layouts/AcademicLayout';

import Departments from './pages/Departments';
import Courses from './pages/Courses';
import Documents from './pages/Documents';
import ComingSoon from './pages/ComingSoon';
import Chat from './pages/Chat';

const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, loading } = useAuth();
  
  if (loading) return <div>Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />; // or to unauthorized page
  }
  return children;
};

const AppRoutes = () => {
  const { user } = useAuth();

  return (
    <Routes>
      <Route element={<AuthLayout />}>
        <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
        <Route path="/register" element={user ? <Navigate to="/" replace /> : <Login isRegister />} />
      </Route>

      <Route element={<DashboardLayout />}>
        <Route path="/" element={
          <ProtectedRoute>
            {user?.role === 'STUDENT' ? <Dashboard /> : <Dashboard />}
          </ProtectedRoute>
        } />
        <Route element={<AcademicLayout />}>
          <Route path="/departments" element={<ProtectedRoute allowedRoles={['ADMIN', 'PUBLISHER']}><Departments /></ProtectedRoute>} />
          <Route path="/courses" element={<ProtectedRoute allowedRoles={['ADMIN', 'PUBLISHER']}><Courses /></ProtectedRoute>} />
          <Route path="/documents" element={<ProtectedRoute allowedRoles={['ADMIN', 'PUBLISHER']}><Documents /></ProtectedRoute>} />
        </Route>
        <Route path="/marketplace" element={<ProtectedRoute allowedRoles={['STUDENT']}><Marketplace /></ProtectedRoute>} />
        <Route path="/chat" element={<ProtectedRoute allowedRoles={['STUDENT', 'ADMIN', 'PUBLISHER']}><Chat /></ProtectedRoute>} />
        <Route path="/users" element={<ProtectedRoute allowedRoles={['ADMIN']}><ComingSoon title="Users" /></ProtectedRoute>} />
      </Route>
    </Routes>
  );
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
