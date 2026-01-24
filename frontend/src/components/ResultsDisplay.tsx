import { Job } from '../lib/api';
import ProcessingStatus from './ProcessingStatus';
import ExtractedDataDisplay from './ExtractedDataDisplay';

interface ResultsDisplayProps {
  job: Job;
  processingMethod?: 'vision' | 'text' | 'auto';  // NEW: Added 'auto'
}

export default function ResultsDisplay({ job, processingMethod }: ResultsDisplayProps) {
  return (
    <div className="space-y-6">
      {/* Processing method badge */}
      {processingMethod && (
        <div className="flex items-center gap-2 flex-wrap">
          {/* Requested method */}
          <span className="text-xs text-gray-600">Requested:</span>
          <span className={`px-3 py-1 text-xs font-semibold rounded-full ${
            processingMethod === 'text'
              ? 'bg-green-100 text-green-800'
              : processingMethod === 'auto'
              ? 'bg-purple-100 text-purple-800'
              : 'bg-blue-100 text-blue-800'
          }`}>
            {processingMethod === 'text' ? 'Text Extraction' :
             processingMethod === 'auto' ? 'Auto-Detection' :
             'Vision Extraction'}
          </span>

          {/* Actual method used (shown after job starts) */}
          {job.processing_method && processingMethod === 'auto' && (
            <>
              <span className="text-xs text-gray-600">→</span>
              <span className="text-xs text-gray-600">Detected:</span>
              <span className={`px-3 py-1 text-xs font-semibold rounded-full ${
                job.processing_method === 'text'
                  ? 'bg-green-100 text-green-800'
                  : job.processing_method === 'hybrid'
                  ? 'bg-orange-100 text-orange-800'
                  : 'bg-blue-100 text-blue-800'
              }`}>
                {job.processing_method === 'text' ? 'Text Pipeline (Fast)' :
                 job.processing_method === 'hybrid' ? 'Hybrid Pipeline (Balanced)' :
                 'Vision Pipeline (Accurate)'}
              </span>
            </>
          )}

          {/* Description */}
          {processingMethod === 'auto' && !job.processing_method && (
            <span className="text-xs text-gray-600">
              Automatically selecting optimal pipeline...
            </span>
          )}
          {processingMethod === 'text' && (
            <span className="text-xs text-gray-600">
              Fast, cost-effective extraction for digital PDFs
            </span>
          )}
          {processingMethod === 'vision' && (
            <span className="text-xs text-gray-600">
              High accuracy for images and scanned documents
            </span>
          )}
        </div>
      )}

      {/* Always show processing status */}
      <ProcessingStatus job={job} />

      {/* Error display */}
      {job.status === 'error' && job.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h4 className="text-sm font-semibold text-red-800 mb-2">Error Details</h4>
          <pre className="text-sm text-red-700 whitespace-pre-wrap">{job.error}</pre>
        </div>
      )}

      {/* Extracted data display */}
      {job.status === 'success' && job.result && (
        <section>
          <h2 className="text-xl font-semibold mb-4">Extracted Data</h2>
          <ExtractedDataDisplay result={job.result} fileName={job.file_name} />
        </section>
      )}
    </div>
  );
}
