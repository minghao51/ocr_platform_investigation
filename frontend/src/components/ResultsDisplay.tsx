import { Job } from '../lib/api';
import ProcessingStatus from './ProcessingStatus';
import ExtractedDataDisplay from './ExtractedDataDisplay';

interface ResultsDisplayProps {
  job: Job;
  processingMethod?: 'vision' | 'text';
}

export default function ResultsDisplay({ job, processingMethod }: ResultsDisplayProps) {
  return (
    <div className="space-y-6">
      {/* Processing method badge */}
      {processingMethod && (
        <div className="flex items-center gap-2">
          <span className={`px-3 py-1 text-xs font-semibold rounded-full ${
            processingMethod === 'text'
              ? 'bg-green-100 text-green-800'
              : 'bg-blue-100 text-blue-800'
          }`}>
            {processingMethod === 'text' ? 'Text Extraction' : 'Vision Extraction'}
          </span>
          {processingMethod === 'text' && (
            <span className="text-xs text-gray-600">
              Fast, cost-effective extraction for digital PDFs
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
