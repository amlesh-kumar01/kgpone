import { useTheme } from '../context/ThemeContext';

export default function ThemeToggle({ className = '' }) {
  const { isDarkMode, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={`relative inline-flex items-center justify-center w-10 h-10 rounded-full transition-colors duration-300 border focus:outline-none focus:ring-2 focus:ring-theme-accent focus:ring-offset-2 focus:ring-offset-theme-bg ${
        isDarkMode 
          ? 'bg-theme-surface border-theme-border text-theme-accent hover:bg-theme-bg' 
          : 'bg-white border-theme-border-strong text-slate-500 hover:text-theme-accent-dark hover:bg-theme-bg'
      } ${className}`}
      aria-label="Toggle Dark Mode"
    >
      <span 
        className={`material-symbols-outlined text-[20px] transition-all duration-500 absolute ${
          isDarkMode ? 'opacity-100 rotate-0 scale-100' : 'opacity-0 -rotate-90 scale-50'
        }`}
      >
        dark_mode
      </span>
      <span 
        className={`material-symbols-outlined text-[20px] transition-all duration-500 absolute ${
          isDarkMode ? 'opacity-0 rotate-90 scale-50' : 'opacity-100 rotate-0 scale-100'
        }`}
      >
        light_mode
      </span>
    </button>
  );
}
