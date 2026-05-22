import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useSearchParams } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import Login from './pages/login';
import Dashboard from './pages/dashboard';
import AddWorld from './pages/AddWorld';
import WorldDetails from './pages/WorldDetails';
import Settings from './pages/Settings';
import DashboardLayout from './components/DashboardLayout';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

function AuthCallback() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = React.useState('processing');

  useEffect(() => {
    const token = searchParams.get('token');
    const refreshToken = searchParams.get('refresh_token');

    if (token) {
      localStorage.setItem('authToken', token);
      if (refreshToken) {
        localStorage.setItem('refreshToken', refreshToken);
      }
      setStatus('success');
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 1000);
    } else {
      setStatus('error');
    }
  }, [searchParams]);

  const statusMsg = status === 'processing' ? 'Logging in...' :
    status === 'success' ? 'Success! Redirecting...' : 'Login failed';

  return (
    <div className="flex items-center justify-center h-screen minecraft-bg-grid" role="status" aria-live="polite">
      <h1 className="sr-only">{statusMsg}</h1>
      <div className="pixel-card text-center max-w-sm w-full mx-4">
        {status === 'processing' && (
          <>
            <Loader2 size={40} className="mx-auto mb-4 text-mc-sky animate-spin" aria-hidden="true" />
            <p className="text-lg font-bold uppercase tracking-wider text-white">Logging in...</p>
          </>
        )}
        {status === 'success' && (
          <>
            <div className="w-14 h-14 bg-mc-grass border-4 border-black mx-auto mb-4 flex items-center justify-center" aria-hidden="true">
              <CheckCircle size={28} className="text-white" />
            </div>
            <p className="text-lg font-bold uppercase tracking-wider text-mc-grass">Success! Redirecting...</p>
          </>
        )}
        {status === 'error' && (
          <>
            <div className="w-14 h-14 bg-red-500 border-4 border-black mx-auto mb-4 flex items-center justify-center" aria-hidden="true">
              <XCircle size={28} className="text-white" />
            </div>
            <p className="text-lg font-bold uppercase tracking-wider text-red-400 mb-4">Login failed</p>
            <a href="/" className="text-mc-sky hover:underline text-sm font-semibold uppercase tracking-wider focus-visible:outline-2 focus-visible:outline-mc-sky">
              Try again
            </a>
          </>
        )}
      </div>
    </div>
  );
}

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen minecraft-bg-grid" role="status" aria-live="polite">
        <div className="w-12 h-12 bg-mc-grass border-4 border-black animate-pulse" aria-hidden="true" />
        <span className="sr-only">Checking authentication...</span>
      </div>
    );
  }

  return user ? children : <Navigate to="/" />;
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          {/* Skip link for keyboard users */}
          <a href="#main-content" className="skip-link">
            Skip to main content
          </a>

          <Routes>
            <Route path="/" element={<Login />} />
            <Route path="/auth/callback" element={<AuthCallback />} />
            <Route
              path="/*"
              element={
                <PrivateRoute>
                  <DashboardLayout />
                </PrivateRoute>
              }
            >
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="add-world" element={<AddWorld />} />
              <Route path="worlds/:worldId" element={<WorldDetails />} />
              <Route path="settings" element={<Settings />} />
              <Route path="*" element={<Navigate to="/dashboard" />} />
            </Route>
          </Routes>

          <ToastContainer
            position="bottom-right"
            autoClose={3000}
            hideProgressBar
            newestOnTop
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
            theme="dark"
            toastClassName="!bg-mc-obsidian !border-4 !border-black !rounded-none !text-white !text-sm !font-semibold"
            aria-label="Notifications"
          />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
