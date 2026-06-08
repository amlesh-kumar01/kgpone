import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';

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
    <div className="bg-[#0e1511] text-[#dde4dd] min-h-screen flex flex-col antialiased selection:bg-[#4edea3]/20 selection:text-[#4edea3]">
      <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
      
      {/* Top Navigation Bar */}
      <header className="flex items-center justify-between px-8 py-6 border-b border-[#3c4a42]/30">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-[#4edea3]/10 border border-[#4edea3]/20 shadow-[0_0_15px_rgba(78,222,163,0.1)]">
            <span aria-hidden="true" className="material-symbols-outlined text-[#4edea3] text-[24px]">terminal</span>
          </div>
          <h1 className="font-sans text-[22px] font-semibold leading-[1.2] tracking-[-0.01em] text-[#4edea3]">Academic Nexus</h1>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex flex-col items-end">
            <span className="text-sm font-medium text-[#dde4dd]">{user?.email}</span>
            <span className="text-xs text-[#bbcabf] flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-[#4edea3] inline-block shadow-[0_0_8px_rgba(78,222,163,0.6)]"></span>
              {user?.role} Access
            </span>
          </div>
          
          <button 
            onClick={handleLogout}
            disabled={isLoggingOut}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all duration-300 bg-[#3c4a42]/20 text-[#bbcabf] hover:bg-[#3c4a42]/40 hover:text-[#dde4dd] border border-[#3c4a42]/50 hover:border-[#4edea3]/30 disabled:opacity-50"
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
        <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#16201a] to-[#0e1511] border border-[#3c4a42]/40 p-10 shadow-lg">
          <div className="absolute top-0 right-0 w-96 h-96 bg-[#4edea3]/5 rounded-full blur-[100px] pointer-events-none -translate-y-1/2 translate-x-1/3"></div>
          
          <h2 className="text-3xl font-semibold mb-2 text-white relative z-10">
            Welcome back, {user?.email.split('@')[0]}
          </h2>
          <p className="text-[#bbcabf] max-w-2xl text-lg relative z-10">
            Your personal research workspace is ready. Access your courses, browse the marketplace, and continue your academic journey.
          </p>
        </section>

        {/* Placeholder Grid for Future Features */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          
          {/* Card 1 */}
          <div className="group rounded-2xl bg-[#16201a]/50 border border-[#3c4a42]/30 p-6 hover:bg-[#16201a] hover:border-[#4edea3]/30 transition-all duration-300 cursor-pointer shadow-sm hover:shadow-[0_0_20px_rgba(78,222,163,0.05)]">
            <div className="w-12 h-12 rounded-xl bg-[#4edea3]/10 flex items-center justify-center mb-4 group-hover:bg-[#4edea3]/20 transition-colors">
              <span className="material-symbols-outlined text-[#4edea3]">account_tree</span>
            </div>
            <h3 className="text-xl font-medium text-[#dde4dd] mb-2">Marketplace</h3>
            <p className="text-[#bbcabf] text-sm leading-relaxed">
              Explore interconnected courses and prerequisites through the interactive React Flow visual graph.
            </p>
          </div>

          {/* Card 2 */}
          <div className="group rounded-2xl bg-[#16201a]/50 border border-[#3c4a42]/30 p-6 hover:bg-[#16201a] hover:border-[#4edea3]/30 transition-all duration-300 cursor-pointer shadow-sm hover:shadow-[0_0_20px_rgba(78,222,163,0.05)]">
            <div className="w-12 h-12 rounded-xl bg-[#4edea3]/10 flex items-center justify-center mb-4 group-hover:bg-[#4edea3]/20 transition-colors">
              <span className="material-symbols-outlined text-[#4edea3]">splitscreen</span>
            </div>
            <h3 className="text-xl font-medium text-[#dde4dd] mb-2">Course Workspace</h3>
            <p className="text-[#bbcabf] text-sm leading-relaxed">
              Dive into your active courses with the Gemini-style split-pane reader and chat assistant.
            </p>
          </div>

          {/* Card 3 */}
          <div className="group rounded-2xl bg-[#16201a]/50 border border-[#3c4a42]/30 p-6 hover:bg-[#16201a] hover:border-[#4edea3]/30 transition-all duration-300 cursor-pointer shadow-sm hover:shadow-[0_0_20px_rgba(78,222,163,0.05)]">
            <div className="w-12 h-12 rounded-xl bg-[#4edea3]/10 flex items-center justify-center mb-4 group-hover:bg-[#4edea3]/20 transition-colors">
              <span className="material-symbols-outlined text-[#4edea3]">analytics</span>
            </div>
            <h3 className="text-xl font-medium text-[#dde4dd] mb-2">Progress Analytics</h3>
            <p className="text-[#bbcabf] text-sm leading-relaxed">
              Track your learning milestones, completed modules, and mastery over complex topics.
            </p>
          </div>

        </div>
      </main>
    </div>
  );
}
