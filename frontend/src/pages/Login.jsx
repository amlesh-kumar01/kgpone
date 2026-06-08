import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
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
      // Login/Registration successful, AuthContext will update user state and auto-redirect
      navigate('/');
    } catch {
      setError('Invalid credentials or server error.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#0e1511] text-[#dde4dd] min-h-screen flex flex-col antialiased selection:bg-[#4edea3]/20 selection:text-[#4edea3]">
      <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
      <style dangerouslySetInnerHTML={{
        __html: `
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 24;
        }
      `}} />

      {/* Main Content Area: Login Canvas */}
      <main className="flex-grow flex items-center justify-center p-4 lg:p-12 relative overflow-hidden">
        {/* Subtle Background Glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-[#4edea3]/5 rounded-full blur-[120px] pointer-events-none z-0"></div>
        
        {/* Authentication Card */}
        <div className="relative z-10 w-full max-w-[440px] bg-[#0e1511] rounded-xl p-12 shadow-[0_20px_40px_rgba(0,0,0,0.4)] border border-[#3c4a42]/30 before:absolute before:inset-0 before:rounded-xl before:border before:border-white/5 before:pointer-events-none">
          
          {/* Branding Header */}
          <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-[#1a211d] border border-[#3c4a42]/50 mb-4 shadow-sm">
              <span aria-hidden="true" className="material-symbols-outlined text-[#4edea3] text-[28px]">terminal</span>
            </div>
            <h1 className="font-sans text-[32px] font-semibold leading-[1.2] tracking-[-0.01em] text-[#4edea3] mb-1">Academic Nexus</h1>
            <p className="font-sans text-base leading-relaxed text-[#bbcabf]">
              {isRegistering ? "Register your student credentials." : "Initialize your research session."}
            </p>
          </div>

          {/* Login Form */}
          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-500/10 border border-red-500/50 text-red-500 text-sm p-3 rounded-lg text-center">
                {error}
              </div>
            )}
            {/* Email Input */}
            <div className="space-y-2">
              <label className="block font-mono text-[12px] font-medium leading-none tracking-[0.05em] text-[#dde4dd]" htmlFor="student-email">Student Email</label>
              <div className="relative group">
                <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-[#bbcabf] group-focus-within:text-[#4edea3] transition-colors">mail</span>
                <input 
                  className="w-full bg-[#0e1511] text-[#dde4dd] font-sans text-base leading-relaxed rounded-lg border border-[#3c4a42] py-[14px] pl-12 pr-4 focus:outline-none focus:border-[#4edea3] focus:ring-2 focus:ring-[#4edea3]/20 transition-all placeholder:text-[#86948a]" 
                  id="student-email" 
                  placeholder="scholar@institution.edu" 
                  required 
                  type="email"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                />
              </div>
            </div>

            {/* Password Input */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="block font-mono text-[12px] font-medium leading-none tracking-[0.05em] text-[#dde4dd]" htmlFor="password">Password</label>
                <a className="font-mono text-[12px] font-medium leading-none tracking-[0.05em] text-[#4edea3] hover:text-[#4edea3]/80 transition-colors" href="#">Recover Access</a>
              </div>
              <div className="relative group">
                <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-[#bbcabf] group-focus-within:text-[#4edea3] transition-colors">lock</span>
                <input 
                  className="w-full bg-[#0e1511] text-[#dde4dd] font-sans text-base leading-relaxed rounded-lg border border-[#3c4a42] py-[14px] pl-12 pr-4 focus:outline-none focus:border-[#4edea3] focus:ring-2 focus:ring-[#4edea3]/20 transition-all placeholder:text-[#86948a]" 
                  id="password" 
                  placeholder="••••••••••••" 
                  required 
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            {/* Submit Action */}
            <button 
              className="w-full bg-[#4edea3] text-[#003824] font-sans text-[20px] font-medium leading-[1.4] py-[14px] rounded-lg hover:bg-[#4edea3]/90 transition-colors flex items-center justify-center gap-2 mt-4" 
              type="submit"
              disabled={loading}
            >
              {loading ? (
                <>
                  {isRegistering ? "Registering..." : "Authenticating..."}
                </>
              ) : (
                <>
                  {isRegistering ? "Sign Up" : "Sign In"}
                  <span aria-hidden="true" className="material-symbols-outlined text-[20px]">{isRegistering ? "person_add" : "login"}</span>
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="my-12 flex items-center gap-4 opacity-60">
            <div className="flex-grow h-[1px] bg-[#3c4a42]"></div>
            <span className="font-mono text-[12px] font-medium leading-none tracking-[0.05em] text-[#bbcabf] uppercase">Or continue with</span>
            <div className="flex-grow h-[1px] bg-[#3c4a42]"></div>
          </div>

          {/* Alternative Auth Methods */}
          <div className="grid grid-cols-2 gap-4">
            <button className="flex items-center justify-center gap-2 py-[10px] px-4 rounded-lg border border-[#3c4a42] bg-transparent text-[#dde4dd] font-sans text-[20px] font-medium leading-[1.4] hover:bg-[#dde4dd]/5 transition-colors group" type="button">
              <span aria-hidden="true" className="material-symbols-outlined text-[20px] text-[#bbcabf] group-hover:text-[#dde4dd] transition-colors">code</span>
              GitHub
            </button>
            <button className="flex items-center justify-center gap-2 py-[10px] px-4 rounded-lg border border-[#3c4a42] bg-transparent text-[#dde4dd] font-sans text-[20px] font-medium leading-[1.4] hover:bg-[#dde4dd]/5 transition-colors group" type="button">
              <span aria-hidden="true" className="material-symbols-outlined text-[20px] text-[#bbcabf] group-hover:text-[#dde4dd] transition-colors">account_circle</span>
              Google
            </button>
          </div>

          {/* Sign Up Prompt */}
          <div className="mt-12 text-center border-t border-[#3c4a42]/30 pt-6">
            <p className="font-sans text-base leading-relaxed text-[#bbcabf]">
              {isRegistering ? "Already have an account?" : "Unregistered researcher?"}
              <button 
                type="button"
                className="text-[#4edea3] hover:text-[#4edea3]/80 font-medium transition-colors ml-1" 
                onClick={() => {
                  setIsRegistering(!isRegistering);
                  setError('');
                }}
              >
                {isRegistering ? "Sign In Instead" : "Create Student Account"}
              </button>
            </p>
          </div>
        </div>
      </main>

      {/* Footer Component */}
      <footer className="bg-[#09100c] w-full py-12 mt-auto border-t border-[#3c4a42]/20">
        <div className="flex flex-col md:flex-row justify-between items-center max-w-[1280px] mx-auto px-6 gap-4">
          {/* Branding / Copyright */}
          <div className="flex flex-col items-center md:items-start gap-1">
            <span className="font-sans text-[32px] font-semibold leading-[1.2] tracking-[-0.01em] text-[#dde4dd]">Academic Nexus</span>
            <span className="font-mono text-[12px] font-medium leading-none tracking-[0.05em] text-[#bbcabf]">© 2024 Academic Nexus. Intellectual Pioneers Only.</span>
          </div>
          
          {/* Links */}
          <nav>
            <ul className="flex flex-wrap justify-center gap-6">
              <li><a className="font-mono text-[12px] font-medium leading-none tracking-[0.05em] text-[#bbcabf] hover:text-[#4edea3] transition-colors duration-300" href="#">Documentation</a></li>
              <li><a className="font-mono text-[12px] font-medium leading-none tracking-[0.05em] text-[#bbcabf] hover:text-[#4edea3] transition-colors duration-300" href="#">Server Status</a></li>
              <li><a className="font-mono text-[12px] font-medium leading-none tracking-[0.05em] text-[#bbcabf] hover:text-[#4edea3] transition-colors duration-300" href="#">Security</a></li>
              <li><a className="font-mono text-[12px] font-medium leading-none tracking-[0.05em] text-[#bbcabf] hover:text-[#4edea3] transition-colors duration-300" href="#">API</a></li>
              <li><a className="font-mono text-[12px] font-medium leading-none tracking-[0.05em] text-[#bbcabf] hover:text-[#4edea3] transition-colors duration-300" href="#">Terms</a></li>
            </ul>
          </nav>
        </div>
      </footer>
    </div>
  );
}
