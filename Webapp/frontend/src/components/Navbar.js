import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { LogOut, Sun, Moon } from 'lucide-react';

function Navbar() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <nav aria-label="Main navigation" className="bg-mc-dirt h-16 border-b-[6px] border-mc-dirt-dark px-4 md:px-6 flex items-center justify-between shrink-0 z-50">
      {/* Logo */}
      <Link to="/dashboard" className="flex items-center gap-3 group shrink-0" aria-label="Back to dashboard">
        <div className="w-9 h-9 bg-mc-grass border-[3px] border-black shrink-0 transition-transform group-hover:scale-105" aria-hidden="true" />
        <h1 className="text-shadow font-pixel text-sm md:text-base text-white leading-tight">
          MINECRAFT<br className="hidden sm:block" /> BACKUP
        </h1>
      </Link>

      {/* Right section */}
      <div className="flex items-center gap-3 md:gap-5">
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="text-white/60 hover:text-white transition-colors p-2 rounded"
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? <Sun size={20} aria-hidden="true" /> : <Moon size={20} aria-hidden="true" />}
        </button>

        {/* User info */}
        <div className="flex items-center gap-3 pl-4 border-l-2 border-black/20">
          {user?.profile_picture && (
            <img
              src={user.profile_picture}
              alt={user?.display_name || 'User avatar'}
              className="w-9 h-9 border-[3px] border-black"
            />
          )}
          <span className="text-shadow text-sm font-semibold text-white hidden md:block">
            {user?.display_name || user?.email}
          </span>
          <button
            onClick={logout}
            className="pixel-btn pixel-btn-danger !py-2 !px-4 text-sm"
            aria-label="Logout"
          >
            <LogOut size={16} aria-hidden="true" />
            <span className="hidden sm:inline">Logout</span>
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
