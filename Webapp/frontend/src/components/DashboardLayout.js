import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

export default function DashboardLayout() {
  return (
    <div className="min-h-screen flex flex-col bg-mc-dark">
      <Navbar />
      <div className="flex flex-1 overflow-hidden" style={{ height: 'calc(100vh - 64px)' }}>
        <Sidebar />
        <main id="main-content" className="flex-1 overflow-y-auto minecraft-bg-grid" tabIndex={-1}>
          <div className="max-w-7xl mx-auto p-4 md:p-6 lg:p-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
