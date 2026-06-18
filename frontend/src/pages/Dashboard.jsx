import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import ThemeToggle from '../components/ThemeToggle';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await logout();
      navigate('/');
    } catch (error) {
      console.error("Failed to log out", error);
      setIsLoggingOut(false);
    }
  };

  return (
    <div className="bg-theme-bg text-theme-text min-h-screen flex flex-col antialiased selection:bg-theme-accent-light selection:text-theme-accent-dark transition-colors duration-300">
      <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
      
      {/* Top Navigation Bar */}
      <header className="flex items-center justify-between px-8 py-6 border-b border-theme-border transition-colors duration-300">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-theme-accent-light border border-theme-accent-light shadow-[0_0_15px_rgba(78,222,163,0.1)] transition-colors duration-300">
            <span aria-hidden="true" className="material-symbols-outlined text-theme-accent text-[24px]">terminal</span>
          </div>
          <h1 className="font-sans text-[22px] font-semibold leading-[1.2] tracking-[-0.01em] text-theme-accent">Academic Nexus</h1>
        </div>

        <div className="flex items-center gap-6">
          <ThemeToggle />
          <div className="flex flex-col items-end">
            <span className="text-sm font-medium text-theme-text">{user?.email}</span>
            <span className="text-xs text-theme-text-muted flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-theme-accent inline-block shadow-[0_0_8px_rgba(78,222,163,0.6)]"></span>
              {user?.role} Access
            </span>
          </div>
          
          <button 
            onClick={handleLogout}
            disabled={isLoggingOut}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all duration-300 bg-theme-border text-theme-text-strong hover:bg-theme-border-strong hover:text-theme-text border border-theme-border hover:border-theme-accent disabled:opacity-50"
          >
            {isLoggingOut ? (
              <span className="material-symbols-outlined text-[20px] animate-spin">refresh</span>
            ) : (
              <span className="material-symbols-outlined text-[20px]">logout</span>
            )}
            Sign Out
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-6xl w-full mx-auto p-8 flex flex-col gap-8">
        
        {/* Welcome Banner */}
        <section className="relative overflow-hidden rounded-3xl bg-theme-surface border border-theme-border p-10 shadow-lg transition-colors duration-300">
          <div className="absolute top-0 right-0 w-96 h-96 bg-theme-accent-light rounded-full blur-[100px] pointer-events-none -translate-y-1/2 translate-x-1/3 transition-colors duration-300"></div>
          
          <h2 className="text-3xl font-semibold mb-2 text-theme-text relative z-10">
            Welcome back, {user?.email.split('@')[0]}
          </h2>
          <p className="text-theme-text-muted max-w-2xl text-lg relative z-10">
            Your personal research workspace is ready. Access your courses, browse the marketplace, and continue your academic journey.
          </p>
        </section>

        {/* Feature Navigation Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          
          {/* Card 1: Marketplace */}
          <div 
            onClick={() => navigate('/marketplace')}
            className="group rounded-2xl bg-theme-surface border border-theme-border p-6 hover:border-theme-accent transition-all duration-300 cursor-pointer shadow-sm hover:shadow-[0_0_20px_rgba(78,222,163,0.05)]"
          >
            <div className="w-12 h-12 rounded-xl bg-theme-accent-light flex items-center justify-center mb-4 group-hover:bg-theme-accent-light/50 transition-colors">
              <span className="material-symbols-outlined text-theme-accent">account_tree</span>
            </div>
            <h3 className="text-xl font-medium text-theme-text mb-2">Marketplace</h3>
            <p className="text-theme-text-muted text-sm leading-relaxed">
              Explore interconnected courses and prerequisites through the interactive React Flow visual graph.
            </p>
          </div>

          {/* Card 2: Course Workspace */}
          <div 
            onClick={() => navigate('/workspace/CS30002')}
            className="group rounded-2xl bg-theme-surface border border-theme-border p-6 hover:border-theme-accent transition-all duration-300 cursor-pointer shadow-sm hover:shadow-[0_0_20px_rgba(78,222,163,0.05)]"
          >
            <div className="w-12 h-12 rounded-xl bg-theme-accent-light flex items-center justify-center mb-4 group-hover:bg-theme-accent-light/50 transition-colors">
              <span className="material-symbols-outlined text-theme-accent">splitscreen</span>
            </div>
            <h3 className="text-xl font-medium text-theme-text mb-2">Course Workspace</h3>
            <p className="text-theme-text-muted text-sm leading-relaxed">
              Dive into your active courses with the Gemini-style split-pane reader and chat assistant.
            </p>
          </div>

          {/* Card 3: Dynamic Publisher Portal or Progress Analytics */}
          {user?.role === 'ADMIN' || user?.role === 'PUBLISHER' ? (
            <div 
              onClick={() => navigate('/publisher')}
              className="group rounded-2xl bg-theme-surface border border-theme-border p-6 hover:border-theme-accent transition-all duration-300 cursor-pointer shadow-sm hover:shadow-[0_0_20px_rgba(78,222,163,0.05)]"
            >
              <div className="w-12 h-12 rounded-xl bg-theme-accent-light flex items-center justify-center mb-4 group-hover:bg-theme-accent-light/50 transition-colors">
                <span className="material-symbols-outlined text-theme-accent">publish</span>
              </div>
              <h3 className="text-xl font-medium text-theme-text mb-2">Publisher Portal</h3>
              <p className="text-theme-text-muted text-sm leading-relaxed">
                Upload study materials, manage syllabus references, and configure course dependencies.
              </p>
            </div>
          ) : (
            <div 
              onClick={() => alert("Progress Analytics module is coming soon!")}
              className="group rounded-2xl bg-theme-surface border border-theme-border p-6 hover:border-theme-accent transition-all duration-300 cursor-pointer shadow-sm hover:shadow-[0_0_20px_rgba(78,222,163,0.05)]"
            >
              <div className="w-12 h-12 rounded-xl bg-theme-accent-light flex items-center justify-center mb-4 group-hover:bg-theme-accent-light/50 transition-colors">
                <span className="material-symbols-outlined text-theme-accent">analytics</span>
              </div>
              <h3 className="text-xl font-medium text-theme-text mb-2">Progress Analytics</h3>
              <p className="text-theme-text-muted text-sm leading-relaxed">
                Track your learning milestones, completed modules, and mastery over complex topics.
              </p>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
