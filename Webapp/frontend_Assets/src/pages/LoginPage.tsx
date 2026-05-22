/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useAuth } from '../App';
import { useNavigate } from 'react-router-dom';
import { motion } from 'motion/react';

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = () => {
    login();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-minecraft-dark minecraft-bg-grid flex items-center justify-center p-4">
      <motion.div 
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="pixel-card max-w-sm w-full text-center space-y-10"
      >
        <div className="space-y-4">
          <div className="flex justify-center">
            <div className="w-12 h-12 bg-minecraft-grass border-4 border-black shadow-[4px_4px_0_0_rgba(0,0,0,0.3)]"></div>
          </div>
          <h1 className="text-shadow font-bold text-2xl text-white tracking-widest drop-shadow-[0_4px_0_rgba(0,0,0,0.5)] m-0">
            MINECRAFT<br/>BACKUP PRO
          </h1>
          <p className="text-minecraft-dirt-dark font-bold text-[10px] uppercase tracking-tighter">
            Production Grade World Syncing
          </p>
        </div>

        <div className="space-y-6">
          <button 
            onClick={handleLogin}
            className="pixel-btn w-full py-4 text-xs font-bold"
          >
            Sign in with Google
          </button>
          
          <div className="flex justify-between text-[10px] font-bold text-minecraft-dirt-dark uppercase">
            <span>Ver 2.4.0</span>
            <span>By BlockDev</span>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
