/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Link } from 'react-router-dom';
import { useAuth } from '../App';
import { LogOut } from 'lucide-react';

export function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="bg-minecraft-dirt h-16 border-b-6 border-minecraft-dirt-dark px-6 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-4">
        <Link to="/" className="flex items-center gap-4 group">
          <div className="w-8 h-8 bg-minecraft-grass border-3 border-black"></div>
          <h1 className="text-shadow font-mono text-lg font-bold tracking-tight text-white m-0">
            MINECRAFT BACKUP PRO
          </h1>
        </Link>
      </div>

      <div className="flex items-center gap-6">
        <div className="hidden sm:block text-right">
          <div className="text-[10px] text-minecraft-gold uppercase mb-1 tracking-wider">Storage Used</div>
          <div className="w-32 h-4 bg-black border-2 border-minecraft-stone relative">
            <div className="h-full bg-minecraft-sky" style={{ width: '64%' }}></div>
          </div>
          <div className="text-[9px] mt-1 text-white/70">9.6 GB / 15 GB</div>
        </div>

        <div className="flex items-center gap-3 pl-6 border-l-2 border-black/20">
          <div className="flex flex-col items-end hidden md:flex">
            <span className="text-shadow text-[13px] font-bold text-white">{user?.name}</span>
            <span className="text-[9px] text-minecraft-grass uppercase tracking-tighter">Premium User</span>
          </div>
          <img src={user?.avatar} alt={user?.name} className="w-9 h-9 bg-minecraft-stone border-3 border-black" />
          <button 
            onClick={logout}
            className="p-1.5 hover:bg-black/20 text-white/50 hover:text-red-400 transition-colors"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </nav>
  );
}
