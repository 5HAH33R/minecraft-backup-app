/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Globe, Settings, Activity, Plus } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function Sidebar() {
  const location = useLocation();

  const menuItems = [
    { name: 'Worlds', path: '/', icon: LayoutDashboard },
    { name: 'Pair Device', path: '/settings#pairing', icon: Globe },
    { name: 'Settings', path: '/settings', icon: Settings },
    { name: 'Activity Logs', path: '/logs', icon: Activity },
  ];

  return (
    <aside className="w-64 bg-minecraft-sidebar border-r-6 border-black min-h-screen flex flex-col p-5 gap-6 hidden lg:flex">
      <button className="pixel-btn w-full mb-2">
        <div className="flex items-center justify-center gap-2">
          <Plus size={16} />
          <span>Add New World</span>
        </div>
      </button>

      <div>
        <div className="text-[10px] text-white opacity-60 uppercase mb-4 tracking-wider font-press-start">Menu</div>
        <div className="flex flex-col gap-2">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-3 p-3 transition-colors text-sm",
                location.pathname === item.path 
                  ? "bg-white/10 border-l-4 border-minecraft-grass" 
                  : "hover:bg-white/5 border-l-4 border-transparent"
              )}
            >
              <item.icon size={18} />
              <span>{item.name}</span>
            </Link>
          ))}
        </div>
      </div>
    </aside>
  );
}
