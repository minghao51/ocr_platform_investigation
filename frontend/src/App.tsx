import { useEffect, useRef, useState } from 'react';
import { NavLink, Navigate, Route, Routes } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import ProcessingPage from './pages/ProcessingPage';
import MethodologyPage from './pages/MethodologyPage';
import HistoryPage from './pages/HistoryPage';
import BenchmarksPage from './pages/BenchmarksPage';
import { AUTH_CHANGE_EVENT, logout, getCurrentUser } from '@/lib/api';
import ErrorBoundary from '@/components/ErrorBoundary';
import LoginPanel from '@/components/LoginPanel';

const navItems: Array<{
  to: string;
  label: string;
  end?: boolean;
  icon?: React.ReactNode;
}> = [
  {
    to: '/',
    label: 'Home',
    end: true,
  },
  {
    to: '/extract',
    label: 'Extract',
    icon: (
      <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
  {
    to: '/history',
    label: 'History',
  },
  {
    to: '/methodology',
    label: 'Methodology',
  },
  {
    to: '/analytics',
    label: 'Analytics',
  },
];

function App() {
  const [authUser, setAuthUser] = useState(getCurrentUser());
  const [authMenuOpen, setAuthMenuOpen] = useState(false);
  const authMenuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const syncAuthUser = () => {
      setAuthUser(getCurrentUser());
    };

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        syncAuthUser();
      }
    };

    syncAuthUser();

    window.addEventListener('storage', syncAuthUser);
    window.addEventListener(AUTH_CHANGE_EVENT, syncAuthUser);
    window.addEventListener('focus', syncAuthUser);
    window.addEventListener('pageshow', syncAuthUser);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      window.removeEventListener('storage', syncAuthUser);
      window.removeEventListener(AUTH_CHANGE_EVENT, syncAuthUser);
      window.removeEventListener('focus', syncAuthUser);
      window.removeEventListener('pageshow', syncAuthUser);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  useEffect(() => {
    if (!authMenuOpen) {
      return;
    }

    const handlePointerDown = (event: MouseEvent) => {
      if (authMenuRef.current && !authMenuRef.current.contains(event.target as Node)) {
        setAuthMenuOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setAuthMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [authMenuOpen]);

  const handleAuthChanged = () => {
    setAuthUser(getCurrentUser());
    setAuthMenuOpen(false);
  };
  const authenticated = authUser !== null;

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center">
                  <h1 className="text-xl font-bold text-gray-900">OCR Platform</h1>
                </div>
                <div className="ml-6 hidden sm:flex space-x-8">
                  {navItems.map((item) => (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      end={item.end}
                      className={({ isActive }) =>
                        'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ' +
                        (isActive
                          ? 'border-blue-500 text-gray-900'
                          : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700')
                      }
                    >
                      {item.icon}
                      {item.label}
                    </NavLink>
                  ))}
                </div>
              </div>
              <div ref={authMenuRef} className="relative flex items-center">
                {authenticated ? (
                  <>
                    <span className="text-sm text-gray-600 mr-4">
                      {authUser?.username}
                    </span>
                    <button
                      onClick={() => {
                        logout();
                        setAuthUser(null);
                      }}
                      className="text-sm text-gray-500 hover:text-gray-700"
                    >
                      Logout
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      type="button"
                      onClick={() => setAuthMenuOpen((open) => !open)}
                      className="text-sm text-amber-700 bg-amber-50 border border-amber-200 px-3 py-1 rounded-full hover:bg-amber-100 transition-colors"
                      aria-expanded={authMenuOpen}
                      aria-haspopup="dialog"
                    >
                      Guest mode
                    </button>
                    {authMenuOpen && (
                      <div className="absolute right-0 top-12 z-20 w-[22rem] rounded-xl border border-gray-200 bg-white p-4 shadow-lg">
                        <LoginPanel
                          onLoginSuccess={handleAuthChanged}
                          title="Sign in"
                          subtitle="Use an admin or demo account to upload documents, run OCR, and review history."
                          compact={true}
                        />
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
            <div className="sm:hidden pb-3 flex gap-4 overflow-x-auto">
              {navItems.map((item) => (
                <NavLink
                  key={`mobile-${item.to}`}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) =>
                    'inline-flex items-center whitespace-nowrap px-2 py-1 rounded-md text-sm font-medium transition-colors ' +
                    (isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-800')
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </div>
          </div>
        </nav>

        {/* Page Content */}
        <main className="bg-gray-50">
          <Routes>
            <Route
              path="/"
              element={
                <LandingPage
                  isAuthenticated={authenticated}
                  username={authUser?.username}
                />
              }
            />
            <Route
              path="/extract"
              element={
                <ProcessingPage isAuthenticated={authenticated} />
              }
            />
            <Route
              path="/history"
              element={
                <HistoryPage isAuthenticated={authenticated} />
              }
            />
            <Route path="/methodology" element={<MethodologyPage />} />
            <Route path="/analytics" element={<BenchmarksPage />} />
            <Route path="/benchmarks" element={<BenchmarksPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </ErrorBoundary>
  );
}

export default App;
