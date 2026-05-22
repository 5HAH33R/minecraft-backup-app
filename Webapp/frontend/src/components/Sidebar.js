import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Plus, Settings } from 'lucide-react';
import { cn } from '../lib/utils';

const menuItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/add-world', icon: Plus, label: 'Add World' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside aria-label="Sidebar navigation" className="w-56 bg-mc-sidebar border-r-[6px] border-black shrink-0 hidden lg:flex flex-col py-5">
      <div className="px-5 mb-3">
        <span className="text-[11px] font-semibold text-white/40 uppercase tracking-widest">
          Menu
        </span>
      </div>

      <nav aria-label="Main menu" className="flex flex-col gap-0.5 px-3">
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path ||
            (item.path !== '/dashboard' && location.pathname.startsWith(item.path));

          return (
            <Link
              key={item.path}
              to={item.path}
              aria-current={isActive ? 'page' : undefined}
              className={cn(
                'flex items-center gap-3 px-4 py-3 text-sm font-medium transition-all duration-100 border-l-4',
                isActive
                  ? 'bg-white/10 border-l-mc-grass text-white'
                  : 'border-l-transparent text-white/60 hover:text-white hover:bg-white/5'
              )}
            >
              <item.icon size={18} aria-hidden="true" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
