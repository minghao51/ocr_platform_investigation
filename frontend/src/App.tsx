import { useState, useEffect } from 'react';
import ProcessingPage from './pages/ProcessingPage';
import MethodologyPage from './pages/MethodologyPage';
import HistoryPage from './pages/HistoryPage';
import LoginPage from './pages/LoginPage';
import { isAuthenticated, logout, getCurrentUser } from '@/lib/api';

type Page = 'processing' | 'history' | 'methodology';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('processing');
  const [isAuthChecked, setIsAuthChecked] = useState(false);
  const [showLogin, setShowLogin] = useState(false);

  // Check authentication on mount
  useEffect(() => {
    setIsAuthChecked(true);
    setShowLogin(!isAuthenticated());
  }, []);

  const handleLoginSuccess = () => {
    setShowLogin(false);
    window.location.reload(); // Reload to refresh app state
  };

  // Show loading while checking auth
  if (!isAuthChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  // Show login page if not authenticated
  if (showLogin) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  const currentUser = getCurrentUser();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold text-gray-900">OCR Platform</h1>
              </div>
              <div className="ml-6 flex space-x-8">
                <button
                  onClick={() => setCurrentPage('processing')}
                  className={'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ' +
                    (currentPage === 'processing'
                      ? 'border-blue-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    )}
                >
                  <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Extract
                </button>
                <button
                  onClick={() => setCurrentPage('history')}
                  className={'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ' +
                    (currentPage === 'history'
                      ? 'border-blue-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    )}
                >
                  History
                </button>
                <button
                  onClick={() => setCurrentPage('methodology')}
                  className={'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ' +
                    (currentPage === 'methodology'
                      ? 'border-blue-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    )}
                >
                  Methodology
                </button>
              </div>
            </div>
            <div className="flex items-center">
              <span className="text-sm text-gray-600 mr-4">
                {currentUser?.username}
              </span>
              <button
                onClick={() => {
                  logout();
                  setShowLogin(true);
                }}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Page Content */}
      <main className="bg-gray-50">
        {currentPage === 'processing' && <ProcessingPage />}
        {currentPage === 'history' && <HistoryPage />}
        {currentPage === 'methodology' && <MethodologyPage />}
      </main>
    </div>
  );
}

export default App;
