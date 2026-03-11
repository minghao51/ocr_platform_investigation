import { Job } from '../lib/api';
import ProcessingStatus from './ProcessingStatus';
import ExtractedDataDisplay from './ExtractedDataDisplay';
import type { ExtractionMethod } from './ExtractionModeSelector';

interface ResultsDisplayProps {
  job: Job;
  processingMethod?: ExtractionMethod;
}

export default function ResultsDisplay({ job, processingMethod }: ResultsDisplayProps) {
  const errorMessage = typeof job.error === 'string' ? job.error : null;
  const hasResult = job.result !== null && job.result !== undefined;

  const getMethodBadgeColor = (method: ExtractionMethod): string => {
    switch (method) {
      case 'text':
        return 'bg-green-100 text-green-800';
      case 'auto':
        return 'bg-purple-100 text-purple-800';
      case 'vision':
        return 'bg-blue-100 text-blue-800';
      case 'hybrid':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getMethodLabel = (method: ExtractionMethod): string => {
    switch (method) {
      case 'text':
        return 'Text Extraction';
      case 'auto':
        return 'Auto-Detection';
      case 'vision':
        return 'Vision Extraction';
      case 'hybrid':
        return 'Hybrid Extraction';
      default:
        return 'Unknown';
    }
  };

  const getProcessingMethodLabel = (method?: string): string => {
    switch (method) {
      case 'text':
        return 'Text Pipeline (Fast)';
      case 'hybrid':
        return 'Hybrid Pipeline (Balanced)';
      case 'vision':
        return 'Vision Pipeline (Accurate)';
      default:
        return 'Unknown Pipeline';
    }
  };

  const getProcessingMethodColor = (method?: string): string => {
    switch (method) {
      case 'text':
        return 'bg-green-100 text-green-800';
      case 'hybrid':
        return 'bg-orange-100 text-orange-800';
      case 'vision':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getMethodDescription = (method: ExtractionMethod): string => {
    switch (method) {
      case 'auto':
        return 'Automatically selecting optimal pipeline...';
      case 'text':
        return 'Fast, cost-effective extraction for digital PDFs';
      case 'vision':
        return 'High accuracy for images and scanned documents';
      case 'hybrid':
        return 'Combines text extraction and vision processing';
      default:
        return '';
    }
  };

  return (
    <div className="space-y-6">
      {/* Processing method badge */}
      {processingMethod && (
        <div className="flex items-center gap-2 flex-wrap">
          {/* Requested method */}
          <span className="text-xs text-gray-600">Requested:</span>
          <span className={`px-3 py-1 text-xs font-semibold rounded-full ${getMethodBadgeColor(processingMethod)}`}>
            {getMethodLabel(processingMethod)}
          </span>

          {/* Actual method used (shown after job starts) */}
          {job.processing_method && processingMethod === 'auto' && (
            <>
              <span className="text-xs text-gray-600">→</span>
              <span className="text-xs text-gray-600">Detected:</span>
              <span className={`px-3 py-1 text-xs font-semibold rounded-full ${getProcessingMethodColor(job.processing_method)}`}>
                {getProcessingMethodLabel(job.processing_method)}
              </span>
            </>
          )}

          {/* Description */}
          {!job.processing_method && (
            <span className="text-xs text-gray-600">
              {getMethodDescription(processingMethod)}
            </span>
          )}
        </div>
      )}

      {/* Always show processing status */}
      <ProcessingStatus job={job} />

      {/* Error display */}
      {job.status === 'error' && errorMessage && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h4 className="text-sm font-semibold text-red-800 mb-2">Error Details</h4>
          <pre className="text-sm text-red-700 whitespace-pre-wrap">{errorMessage}</pre>
        </div>
      )}

      {/* Extracted data display */}
      {job.status === 'success' && hasResult && (
        <section>
          <h2 className="text-xl font-semibold mb-4">Extracted Data</h2>
          <ExtractedDataDisplay result={job.result} fileName={job.file_name} />
        </section>
      )}
    </div>
  );
}
