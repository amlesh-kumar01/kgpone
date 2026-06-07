import { AuthProvider } from './context/AuthContext';
import { WorkspaceProvider } from './context/WorkspaceContext';
import Dashboard from './pages/Dashboard';

function App() {
  return (
    <AuthProvider>
      <WorkspaceProvider>
        <div className="min-h-screen bg-gray-50">
          <Dashboard />
        </div>
      </WorkspaceProvider>
    </AuthProvider>
  );
}

export default App;
