import { useState } from 'react';
import ProcessingPage from './pages/ProcessingPage';
import TextExtractionPage from './pages/TextExtractionPage';
import MethodologyPage from './pages/MethodologyPage';
import HistoryPage from './pages/HistoryPage';

type Page = 'processing' | 'text-extraction' | 'history' | 'methodology';

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
                      ? 'border-purple-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    )}
                >
                  <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Smart Extract
                  <span className="ml-2 text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full font-medium">Auto</span>
                </button>
                <button
                  onClick={() => setCurrentPage('text-extraction')}
                  className={'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ' +
                    (currentPage === 'text-extraction'
                      ? 'border-green-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    )}
                >
                  <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
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
          </div>
        </div>
      </nav>

      {/* Page Content */}
      <main className="bg-gray-50">
        {currentPage === 'processing' && <ProcessingPage />}
        {currentPage === 'text-extraction' && <TextExtractionPage />}
        {currentPage === 'history' && <HistoryPage />}
        {currentPage === 'methodology' && <MethodologyPage />}
      </main>
    </div>
  );
}

export default App;
