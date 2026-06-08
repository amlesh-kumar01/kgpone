import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { AuthProvider } from './context/AuthContext';
import { WorkspaceProvider } from './context/WorkspaceContext';
import { ProtectedRoute, RoleRoute } from './components/guards/RouteGuards';

import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Marketplace from './pages/Marketplace';
import CourseWorkspace from './pages/CourseWorkspace';
import PublisherPortal from './pages/PublisherPortal';

const HomeRoute = () => {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div className="flex items-center justify-center min-h-screen bg-[#0e1511] text-[#4edea3]">Initializing...</div>;
  return user ? <Dashboard /> : <Login />;
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <WorkspaceProvider>
          <div className="min-h-screen bg-gray-50">
            <Routes>
              {/* Dynamic Home Route */}
              <Route path="/" element={<HomeRoute />} />

              {/* Protected routes (accessible to any logged-in user) */}
              <Route element={<ProtectedRoute />}>
                <Route path="/marketplace" element={<Marketplace />} />
                <Route path="/workspace/:courseId" element={<CourseWorkspace />} />
                
                {/* Publisher Portal (Role-protected) */}
                <Route element={<RoleRoute allowedRoles={['PUBLISHER', 'ADMIN']} />}>
                  <Route path="/publisher" element={<PublisherPortal />} />
                </Route>

                {/* Example of a role-protected route */}
                <Route element={<RoleRoute allowedRoles={['ADMIN']} />}>
                  <Route path="/admin" element={<div className="p-10">Admin Panel</div>} />
                </Route>
              </Route>

              {/* Fallbacks */}
              <Route path="/forbidden" element={<div className="p-10 text-center"><h1>403 - Forbidden</h1><p>You don't have permission to view this page.</p></div>} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </WorkspaceProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
