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
    <div className="bg-[#060d13] text-white min-h-screen flex flex-col antialiased selection:bg-[#00D2FF]/20 selection:text-[#00D2FF] font-sans transition-colors duration-300">
      <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
      <style dangerouslySetInnerHTML={{
        __html: `
          body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: #060d13;
          }
          .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 24;
          }
          .cyan-glow {
            box-shadow: 0 0 30px rgba(0, 210, 255, 0.05);
          }
          .cyan-border-glow:hover {
            box-shadow: 0 0 20px rgba(0, 210, 255, 0.15);
            border-color: #00D2FF;
          }
        `
      }} />

      {/* Top Header */}
      <header className="flex items-center justify-between px-8 py-5 border-b border-[#1e2d3d] bg-[#0D1520]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-[#00D2FF]/10 border border-[#00D2FF]/30 shadow-[0_0_15px_rgba(0,210,255,0.1)]">
            <span className="material-symbols-outlined text-[#00D2FF] text-[24px]">terminal</span>
          </div>
          <div className="flex items-center gap-1 font-bold text-xl tracking-tight">
            <span>Kgp</span>
            <span className="text-[#00D2FF]">One</span>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <ThemeToggle />
          
          <div className="flex flex-col items-end border-r border-[#1e2d3d] pr-5">
            <span className="text-sm font-medium text-white">{user?.email}</span>
            <span className="text-[10px] text-[#6B7280] tracking-wider uppercase font-semibold flex items-center gap-1.5 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00FF88] inline-block shadow-[0_0_6px_#00FF88]"></span>
              {user?.role} Session
            </span>
          </div>
          
          <button 
            onClick={handleLogout}
            disabled={isLoggingOut}
            className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-xs tracking-wider uppercase transition-all duration-200 bg-[#060d13] text-[#9CA3AF] border border-[#1e2d3d] hover:bg-[#0D1520] hover:text-[#00D2FF] hover:border-[#00D2FF] disabled:opacity-50"
          >
            {isLoggingOut ? (
              <span className="material-symbols-outlined text-[16px] animate-spin">sync</span>
            ) : (
              <span className="material-symbols-outlined text-[16px]">logout</span>
            )}
            Sign Out
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-6xl w-full mx-auto p-6 md:p-10 flex flex-col gap-8">
        
        {/* Welcome Banner Card */}
        <section className="relative overflow-hidden rounded-2xl bg-[#0D1520] border border-[#1e2d3d] p-8 md:p-10 shadow-lg cyan-glow">
          <div className="absolute top-0 right-0 w-80 h-80 bg-[radial-gradient(circle,rgba(0,210,255,0.08)_0%,rgba(0,210,255,0)_70%)] pointer-events-none -translate-y-1/3 translate-x-1/4"></div>
          
          <span className="text-[10px] font-bold tracking-[0.2em] text-[#00D2FF] uppercase block mb-2">Welcome Back</span>
          <h2 className="text-3xl font-bold tracking-tight text-white mb-2">
            Welcome to the Nexus, {user?.email.split('@')[0]}
          </h2>
          <p className="text-[#9CA3AF] max-w-2xl text-base leading-relaxed">
            Your secure academic intelligence environment is active. Traverse curriculum prerequisites, query knowledge bases, and index course material structures.
          </p>
        </section>

        {/* Feature Navigation Grid */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          
          {/* Card 1: Marketplace */}
          <div 
            onClick={() => navigate('/marketplace')}
            className="group rounded-2xl bg-[#0D1520] border border-[#1e2d3d] p-6 hover:border-[#00D2FF] transition-all duration-300 cursor-pointer shadow-sm hover:shadow-[0_0_20px_rgba(0,210,255,0.08)] flex flex-col justify-between h-56"
          >
            <div>
              <div className="w-11 h-11 rounded-xl bg-[#00D2FF]/10 border border-[#00D2FF]/20 flex items-center justify-center mb-4 group-hover:bg-[#00D2FF]/20 group-hover:border-[#00D2FF]/40 transition-all">
                <span className="material-symbols-outlined text-[#00D2FF] text-[22px]">account_tree</span>
              </div>
              <h3 className="text-lg font-bold text-white mb-1.5 group-hover:text-[#00D2FF] transition-colors">Course Marketplace</h3>
              <p className="text-[#9CA3AF] text-xs leading-relaxed">
                Explore interconnected courses and prerequisites through the interactive React Flow visual graph.
              </p>
            </div>
            <div className="flex items-center gap-1 text-[10px] font-bold tracking-widest text-[#00D2FF] uppercase mt-4">
              Explore Graph <span className="material-symbols-outlined text-sm transition-transform group-hover:translate-x-1">arrow_forward</span>
            </div>
          </div>

          {/* Card 2: Course Workspace */}
          <div 
            onClick={() => navigate('/workspace/CS30002')}
            className="group rounded-2xl bg-[#0D1520] border border-[#1e2d3d] p-6 hover:border-[#00D2FF] transition-all duration-300 cursor-pointer shadow-sm hover:shadow-[0_0_20px_rgba(0,210,255,0.08)] flex flex-col justify-between h-56"
          >
            <div>
              <div className="w-11 h-11 rounded-xl bg-[#00D2FF]/10 border border-[#00D2FF]/20 flex items-center justify-center mb-4 group-hover:bg-[#00D2FF]/20 group-hover:border-[#00D2FF]/40 transition-all">
                <span className="material-symbols-outlined text-[#00D2FF] text-[22px]">splitscreen</span>
              </div>
              <h3 className="text-lg font-bold text-white mb-1.5 group-hover:text-[#00D2FF] transition-colors">Research Workspace</h3>
              <p className="text-[#9CA3AF] text-xs leading-relaxed">
                Dive into your active courses with the Gemini-style split-pane reader and chat assistant.
              </p>
            </div>
            <div className="flex items-center gap-1 text-[10px] font-bold tracking-widest text-[#00D2FF] uppercase mt-4">
              Enter Workspace <span className="material-symbols-outlined text-sm transition-transform group-hover:translate-x-1">arrow_forward</span>
            </div>
          </div>

          {/* Card 3: Publisher Portal or Progress */}
          {user?.role === 'ADMIN' || user?.role === 'PUBLISHER' ? (
            <div 
              onClick={() => navigate('/publisher')}
              className="group rounded-2xl bg-[#0D1520] border border-[#1e2d3d] p-6 hover:border-[#00D2FF] transition-all duration-300 cursor-pointer shadow-sm hover:shadow-[0_0_20px_rgba(0,210,255,0.08)] flex flex-col justify-between h-56"
            >
              <div>
                <div className="w-11 h-11 rounded-xl bg-[#00D2FF]/10 border border-[#00D2FF]/20 flex items-center justify-center mb-4 group-hover:bg-[#00D2FF]/20 group-hover:border-[#00D2FF]/40 transition-all">
                  <span className="material-symbols-outlined text-[#00D2FF] text-[22px]">publish</span>
                </div>
                <h3 className="text-lg font-bold text-white mb-1.5 group-hover:text-[#00D2FF] transition-colors">Publisher Portal</h3>
                <p className="text-[#9CA3AF] text-xs leading-relaxed">
                  Upload study materials, manage syllabus references, and configure course dependencies.
                </p>
              </div>
              <div className="flex items-center gap-1 text-[10px] font-bold tracking-widest text-[#00D2FF] uppercase mt-4">
                Manage Content <span className="material-symbols-outlined text-sm transition-transform group-hover:translate-x-1">arrow_forward</span>
              </div>
            </div>
          ) : (
            <div 
              onClick={() => alert("Progress Analytics module is coming soon!")}
              className="group rounded-2xl bg-[#0D1520] border border-[#1e2d3d] p-6 hover:border-[#00D2FF] transition-all duration-300 cursor-pointer shadow-sm hover:shadow-[0_0_20px_rgba(0,210,255,0.08)] flex flex-col justify-between h-56"
            >
              <div>
                <div className="w-11 h-11 rounded-xl bg-[#00D2FF]/10 border border-[#00D2FF]/20 flex items-center justify-center mb-4 group-hover:bg-[#00D2FF]/20 group-hover:border-[#00D2FF]/40 transition-all">
                  <span className="material-symbols-outlined text-[#00D2FF] text-[22px]">analytics</span>
                </div>
                <h3 className="text-lg font-bold text-white mb-1.5 group-hover:text-[#00D2FF] transition-colors">Progress Analytics</h3>
                <p className="text-[#9CA3AF] text-xs leading-relaxed">
                  Track your learning milestones, completed modules, and mastery over complex topics.
                </p>
              </div>
              <div className="flex items-center gap-1 text-[10px] font-bold tracking-widest text-[#00D2FF] uppercase mt-4">
                View Progress <span className="material-symbols-outlined text-sm transition-transform group-hover:translate-x-1">arrow_forward</span>
              </div>
            </div>
          )}

        </section>

      </main>

      {/* Footer Status Bar */}
      <footer className="w-full py-4 border-t border-[#1e2d3d] px-8 bg-[#0D1520]/60 backdrop-blur-md flex items-center justify-between text-[10px] font-mono text-[#6B7280]">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[#00FF88] shadow-[0_0_8px_#00FF88]"></span>
          <span className="text-[#00FF88] tracking-widest font-bold uppercase">System Active</span>
        </div>
        <div>
          <span>© 2026 KgpOne. Proprietary Academic Nexus.</span>
        </div>
      </footer>

    </div>
  );
}
