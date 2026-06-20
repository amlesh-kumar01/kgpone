import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ThemeToggle from '../components/ThemeToggle';

export default function Login() {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  const navigate = useNavigate();
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      if (isRegistering) {
        await register(identifier, password);
      } else {
        await login(identifier, password);
      }
      navigate('/');
    } catch (err) {
      if (err.response) {
        if (err.response.status === 401) {
          setError('Invalid credentials. Please verify your access parameters.');
        } else {
          setError(err.response.data?.detail || 'System error. Please try again later.');
        }
      } else if (err.request) {
        setError('Connection timeout. Ensure the backend gateway is active on port 8000.');
      } else {
        setError(err.message || 'An unexpected authentication exception occurred.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#060d13] text-white min-h-screen flex flex-col antialiased selection:bg-[#00D2FF]/20 selection:text-[#00D2FF] font-sans relative overflow-hidden">
      {/* Import Material Symbols and Google Fonts */}
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
            box-shadow: 0 0 40px rgba(0, 210, 255, 0.1);
          }
          .cyan-glow-intense:focus-within {
            box-shadow: 0 0 15px rgba(0, 210, 255, 0.25);
          }
        `
      }} />

      {/* Floating Theme Toggle (Optional but fits visual layout) */}
      <div className="absolute top-6 right-8 z-50">
        <ThemeToggle />
      </div>

      {/* Radial Background Gradients */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] bg-[radial-gradient(circle,rgba(0,210,255,0.08)_0%,rgba(6,13,19,0)_70%)] pointer-events-none z-0"></div>

      {/* Main Container */}
      <main className="flex-grow flex flex-col items-center justify-center px-4 relative z-10 py-12">
        
        {/* Core Auth Card */}
        <div className="w-full max-w-[420px] bg-[#0D1520] rounded-2xl border border-[#1e2d3d] p-8 md:p-10 shadow-2xl cyan-glow">
          
          {/* Header Section */}
          <div className="flex flex-col items-center mb-8">
            <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-[#00D2FF]/10 border border-[#00D2FF]/30 mb-4 shadow-[0_0_15px_rgba(0,210,255,0.15)]">
              <span className="material-symbols-outlined text-[#00D2FF] text-[26px]">terminal</span>
            </div>
            
            <div className="flex items-center gap-1.5 text-2xl font-bold tracking-tight">
              <span className="text-white">Kgp</span>
              <span className="text-[#00D2FF]">One</span>
            </div>
            <span className="text-[10px] font-semibold text-[#00D2FF] tracking-[0.25em] uppercase mt-1">
              {isRegistering ? "Register Credentials" : "Admin Portal Access"}
            </span>
            
            <p className="text-[#6B7280] text-sm text-center mt-3">
              {isRegistering 
                ? "Provision a new secure researcher account" 
                : "Initialize session parameters to authenticate"}
            </p>
          </div>

          {/* Form */}
          <form className="space-y-5" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-xs p-3 rounded-lg text-center flex items-center justify-center gap-2">
                <span className="material-symbols-outlined text-sm">warning</span>
                {error}
              </div>
            )}

            {/* Email Field */}
            <div className="space-y-1.5">
              <label htmlFor="user-email" className="block text-[10px] font-bold tracking-wider text-[#9CA3AF] uppercase">
                Work Email
              </label>
              <div className="relative group cyan-glow-intense">
                <span className="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-[#6B7280] group-focus-within:text-[#00D2FF] transition-colors text-[20px]">
                  alternate_email
                </span>
                <input 
                  id="user-email"
                  type="email"
                  required
                  placeholder="scholar@institution.edu"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  className="w-full bg-[#060d13] text-white text-sm rounded-lg border border-[#1e2d3d] py-3 pl-11 pr-4 focus:outline-none focus:border-[#00D2FF] focus:ring-1 focus:ring-[#00D2FF] transition-all placeholder:text-[#4B5563]"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <label htmlFor="user-password" className="block text-[10px] font-bold tracking-wider text-[#9CA3AF] uppercase">
                  Access Key
                </label>
                <a href="#" className="text-[10px] font-medium text-[#00D2FF] hover:underline">
                  Request Reset
                </a>
              </div>
              <div className="relative group cyan-glow-intense">
                <span className="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-[#6B7280] group-focus-within:text-[#00D2FF] transition-colors text-[20px]">
                  lock
                </span>
                <input 
                  id="user-password"
                  type={showPassword ? "text" : "password"}
                  required
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-[#060d13] text-white text-sm rounded-lg border border-[#1e2d3d] py-3 pl-11 pr-11 focus:outline-none focus:border-[#00D2FF] focus:ring-1 focus:ring-[#00D2FF] transition-all placeholder:text-[#4B5563]"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#6B7280] hover:text-[#9CA3AF] transition-colors flex items-center justify-center w-8 h-8 rounded-lg"
                >
                  <span className="material-symbols-outlined text-[20px]">
                    {showPassword ? "visibility_off" : "visibility"}
                  </span>
                </button>
              </div>
            </div>

            {/* Keep session authorized checkbox */}
            {!isRegistering && (
              <div className="flex items-center gap-2.5 py-1">
                <input 
                  id="persist-session" 
                  type="checkbox"
                  defaultChecked
                  className="w-4 h-4 rounded border-[#1e2d3d] bg-[#060d13] text-[#00D2FF] focus:ring-[#00D2FF] focus:ring-offset-[#0d1520]"
                />
                <label htmlFor="persist-session" className="text-xs text-[#9CA3AF] select-none cursor-pointer">
                  Keep session authorized for 24 hours
                </label>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#00D2FF] hover:bg-[#1AD1FF] active:scale-[0.99] text-black font-semibold text-sm py-3.5 rounded-lg transition-all flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(0,210,255,0.2)] mt-6 disabled:opacity-75"
            >
              {loading ? (
                <>
                  <span className="material-symbols-outlined animate-spin text-[18px]">sync</span>
                  {isRegistering ? "Initializing..." : "Authorizing..."}
                </>
              ) : (
                <>
                  {isRegistering ? "Provision Account" : "Initialize Portal"}
                  <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                </>
              )}
            </button>
          </form>

          {/* Social Sign In Divider */}
          <div className="my-6 flex items-center gap-3 opacity-30">
            <div className="flex-grow h-[1px] bg-[#1e2d3d]"></div>
            <span className="text-[9px] uppercase tracking-widest text-[#9CA3AF]">federated access</span>
            <div className="flex-grow h-[1px] bg-[#1e2d3d]"></div>
          </div>

          {/* Alternative Auth Methods */}
          <div className="grid grid-cols-2 gap-3">
            <button className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg border border-[#1e2d3d] bg-[#060d13] text-sm text-[#9CA3AF] hover:text-white hover:bg-[#0D1520] transition-colors" type="button">
              GitHub
            </button>
            <button className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg border border-[#1e2d3d] bg-[#060d13] text-sm text-[#9CA3AF] hover:text-white hover:bg-[#0D1520] transition-colors" type="button">
              Google
            </button>
          </div>

          {/* Toggle Register Action */}
          <div className="mt-8 pt-5 border-t border-[#1e2d3d] text-center">
            <p className="text-xs text-[#6B7280]">
              {isRegistering ? "Already authorized?" : "Unregistered credentials?"}
              <button
                type="button"
                onClick={() => {
                  setIsRegistering(!isRegistering);
                  setError('');
                }}
                className="text-[#00D2FF] hover:underline font-semibold ml-1.5"
              >
                {isRegistering ? "Sign In Instead" : "Create Student Account"}
              </button>
            </p>
          </div>

        </div>

        {/* Footer Proprietary Disclaimer */}
        <p className="text-[10px] text-[#4B5563] text-center mt-8 tracking-wide uppercase">
          Proprietary System — Unauthorized Access Prohibited
        </p>

      </main>

      {/* Bottom Status Row */}
      <footer className="w-full py-4 border-t border-[#1e2d3d] px-8 bg-[#020508]/60 backdrop-blur-md relative z-10 flex items-center justify-between text-[10px] font-mono text-[#6B7280]">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[#00FF88] animate-pulse shadow-[0_0_8px_#00FF88]"></span>
          <span className="text-[#00FF88] tracking-widest font-bold uppercase">System Core Active</span>
        </div>
        <div>
          <span>Build v2.4.0-admin</span>
        </div>
      </footer>

    </div>
  );
}
