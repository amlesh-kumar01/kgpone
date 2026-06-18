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
    } catch (err) {
      if (err.response) {
        if (err.response.status === 401) {
          setError('Invalid email or password. Please verify your credentials.');
        } else {
          setError(err.response.data?.detail || 'Server error. Please try again later.');
        }
      } else if (err.request) {
        setError('Cannot connect to the server. Please make sure the backend is running on port 8000.');
      } else {
        setError(err.message || 'An unexpected error occurred.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-theme-bg text-theme-text min-h-screen flex flex-col antialiased selection:bg-theme-accent-light selection:text-theme-accent transition-colors duration-300">
      <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
      <style dangerouslySetInnerHTML={{
        __html: `
          .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 24;
          }
        `
      }} />

      {/* Theme Toggle Button at top right */}
      <div className="absolute top-6 right-8 z-50">
        <ThemeToggle />
      </div>

      {/* Main Content Area: Login Canvas */}
      <main className="flex-grow flex items-center justify-center p-4 lg:p-12 relative overflow-hidden">
        {/* Subtle Background Glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-theme-accent-light rounded-full blur-[120px] pointer-events-none z-0 transition-colors duration-300"></div>
        
        {/* Authentication Card */}
        <div className="relative z-10 w-full max-w-[440px] bg-theme-surface rounded-3xl p-10 shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-theme-border before:absolute before:inset-0 before:rounded-3xl before:border before:border-theme-border-strong before:pointer-events-none transition-colors duration-300">
          
          {/* Branding Header */}
          <div className="text-center mb-10">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-theme-accent-light border border-theme-accent-light mb-6 shadow-[0_0_20px_rgba(78,222,163,0.15)] transition-colors duration-300">
              <span aria-hidden="true" className="material-symbols-outlined text-theme-accent text-[28px]">terminal</span>
            </div>
            <h1 className="font-sans text-[32px] font-semibold leading-[1.2] tracking-[-0.01em] text-theme-accent mb-1">Academic Nexus</h1>
            <p className="font-sans text-base leading-relaxed text-theme-text-muted">
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
              <label htmlFor="student-email" className="block font-mono text-[12px] tracking-wider text-theme-text-strong uppercase font-medium">Student Email</label>
              <div className="relative group">
                <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-theme-text-muted group-focus-within:text-theme-accent transition-colors">mail</span>
                <input 
                  className="w-full bg-theme-bg text-theme-text font-sans text-base rounded-xl border border-theme-border py-3.5 pl-12 pr-4 focus:outline-none focus:border-theme-accent focus:ring-1 focus:ring-theme-accent transition-all placeholder:text-theme-input-placeholder" 
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
                <label htmlFor="password" className="block font-mono text-[12px] tracking-wider text-theme-text-strong uppercase font-medium">Password</label>
                <a href="#" className="font-mono text-[12px] text-theme-accent hover:text-theme-accent-hover transition-colors">Recover Access</a>
              </div>
              <div className="relative group">
                <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-theme-text-muted group-focus-within:text-theme-accent transition-colors">lock</span>
                <input 
                  className="w-full bg-theme-bg text-theme-text font-sans text-base rounded-xl border border-theme-border py-3.5 pl-12 pr-4 focus:outline-none focus:border-theme-accent focus:ring-1 focus:ring-theme-accent transition-all placeholder:text-theme-input-placeholder" 
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
              className="w-full bg-theme-accent text-white font-sans text-lg font-medium py-3.5 rounded-xl hover:bg-theme-accent-hover transition-colors flex items-center justify-center gap-2 mt-4 disabled:opacity-70" 
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
          <div className="my-8 flex items-center gap-4 opacity-60">
            <div className="flex-grow h-[1px] bg-theme-border-strong"></div>
            <span className="font-mono text-[11px] text-theme-text-muted uppercase tracking-widest">Or continue with</span>
            <div className="flex-grow h-[1px] bg-theme-border-strong"></div>
          </div>

          {/* Alternative Auth Methods */}
          <div className="grid grid-cols-2 gap-4">
            <button className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl border border-theme-border bg-theme-surface text-theme-text font-medium hover:bg-theme-bg transition-colors group" type="button">
              <span aria-hidden="true" className="material-symbols-outlined text-[20px] text-theme-text-muted group-hover:text-theme-text-strong transition-colors">code</span>
              GitHub
            </button>
            <button className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl border border-theme-border bg-theme-surface text-theme-text font-medium hover:bg-theme-bg transition-colors group" type="button">
              <span aria-hidden="true" className="material-symbols-outlined text-[20px] text-theme-text-muted group-hover:text-theme-text-strong transition-colors">account_circle</span>
              Google
            </button>
          </div>

          {/* Sign Up Prompt */}
          <div className="mt-12 text-center border-t border-theme-border pt-6">
            <p className="font-sans text-base leading-relaxed text-theme-text-muted">
              {isRegistering ? "Already have an account?" : "Unregistered researcher?"}
              <button 
                type="button"
                className="text-theme-accent hover:text-theme-accent-hover font-medium transition-colors ml-1" 
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
      <footer className="bg-theme-bg/50 w-full py-8 mt-auto border-t border-theme-border backdrop-blur-md transition-colors duration-300">
        <div className="flex flex-col md:flex-row justify-between items-center max-w-7xl mx-auto px-6 gap-4">
          <div className="flex flex-col items-center md:items-start gap-1">
            <span className="font-sans text-[20px] font-semibold text-theme-text tracking-tight">Academic Nexus</span>
            <span className="font-mono text-[11px] text-theme-text-muted">© 2024 Academic Nexus. Intellectual Pioneers Only.</span>
          </div>
          
          <nav>
            <ul className="flex flex-wrap justify-center gap-6">
              <li><a className="font-mono text-[12px] text-theme-text-muted hover:text-theme-accent transition-colors" href="#">Documentation</a></li>
              <li><a className="font-mono text-[12px] text-theme-text-muted hover:text-theme-accent transition-colors" href="#">Server Status</a></li>
              <li><a className="font-mono text-[12px] text-theme-text-muted hover:text-theme-accent transition-colors" href="#">Security</a></li>
              <li><a className="font-mono text-[12px] text-theme-text-muted hover:text-theme-accent transition-colors" href="#">API</a></li>
              <li><a className="font-mono text-[12px] text-theme-text-muted hover:text-theme-accent transition-colors" href="#">Terms</a></li>
            </ul>
          </nav>
        </div>
      </footer>
    </div>
  );
}
