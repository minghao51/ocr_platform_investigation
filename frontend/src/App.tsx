import { useState } from 'react';
import ProcessingPage from './pages/ProcessingPage';
import TextExtractionPage from './pages/TextExtractionPage';
import HistoryPage from './pages/HistoryPage';

type Page = 'processing' | 'text-extraction' | 'history';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('processing');

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
                  Vision Extract
                </button>
                <button
                  onClick={() => setCurrentPage('text-extraction')}
                  className={'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ' +
                    (currentPage === 'text-extraction'
                      ? 'border-blue-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    )}
                >
                  Text Extract
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
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Page Content */}
      <main className="bg-gray-50">
        {currentPage === 'processing' && <ProcessingPage />}
        {currentPage === 'text-extraction' && <TextExtractionPage />}
        {currentPage === 'history' && <HistoryPage />}
      </main>
    </div>
  );
}

export default App;
