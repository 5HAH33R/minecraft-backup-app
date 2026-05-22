import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { LogIn, HardDrive, RefreshCw, Globe } from 'lucide-react';

function Login() {
  const { login } = useAuth();

  return (
    <div className="min-h-screen minecraft-bg-grid flex items-center justify-center p-4">
      <div className="pixel-card max-w-md w-full text-center py-10 px-8 md:px-12">
        {/* Logo */}
        <div className="flex justify-center mb-6" aria-hidden="true">
          <div className="w-16 h-16 bg-mc-grass border-4 border-black shadow-[6px_6px_0_0_rgba(0,0,0,0.3)]" />
        </div>

        {/* Title */}
        <h1 className="text-shadow text-2xl md:text-3xl font-pixel text-white leading-relaxed mb-3">
          MINECRAFT<br />BACKUP
        </h1>
        <p className="text-sm font-semibold text-mc-dirt-dark uppercase tracking-wider mb-10">
          Never lose your worlds again
        </p>

        {/* Google Sign-In */}
        <button
          onClick={login}
          className="pixel-btn w-full py-4 text-base font-bold gap-3"
        >
          <LogIn size={20} />
          Continue with Google
        </button>

        {/* Features */}
        <div className="mt-10 space-y-3">
          {[
            { icon: HardDrive, text: 'Free 15 GB storage' },
            { icon: RefreshCw, text: 'Automatic backups' },
            { icon: Globe, text: 'Access from anywhere' },
          ].map(({ icon: Icon, text }) => (
            <div key={text} className="flex items-center justify-center gap-2 text-sm font-semibold text-mc-dirt-dark/80">
              <Icon size={16} />
              <span>{text}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Login;
