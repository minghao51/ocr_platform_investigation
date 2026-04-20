import { Job } from '../lib/api';
import ProcessingStatus from './ProcessingStatus';
import ExtractedDataDisplay from './ExtractedDataDisplay';
import type { ExtractionMethod } from './ExtractionModeSelector';
import CorrectionReviewPanel from './CorrectionReviewPanel';
import type { JobCorrection } from '@/lib/api';

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
      case 'docling-parse':
        return 'bg-indigo-100 text-indigo-800';
      case 'docling-extract':
        return 'bg-emerald-100 text-emerald-800';
      case 'transcription':
        return 'bg-teal-100 text-teal-800';
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
      case 'docling-parse':
        return 'Docling Parse';
      case 'docling-extract':
        return 'Docling Extract';
      case 'transcription':
        return 'Transcription';
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
      case 'docling-parse':
        return 'Docling Parse';
      case 'docling-extract':
        return 'Docling Extract';
      case 'transcription':
        return 'Transcription';
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
      case 'docling-parse':
        return 'bg-indigo-100 text-indigo-800';
      case 'docling-extract':
        return 'bg-emerald-100 text-emerald-800';
      case 'transcription':
        return 'bg-teal-100 text-teal-800';
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
      case 'docling-parse':
        return 'Multi-format support with cost-optimized extraction';
      case 'docling-extract':
        return 'Best accuracy with local VLM (86% on CORD)';
      case 'transcription':
        return 'Full document transcription to Markdown';
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
          <ExtractedDataDisplay result={job.result} fileName={job.file_name} processingMethod={job.processing_method} />
        </section>
      )}

      {job.hybrid_diagnostics && (
        <section className="rounded-lg border border-orange-200 bg-orange-50 p-5">
          <h3 className="text-lg font-semibold text-orange-950">Hybrid Diagnostics</h3>
          <div className="mt-3 grid gap-3 md:grid-cols-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-orange-700">Pages analyzed</p>
              <p className="text-2xl font-semibold text-orange-950">{job.hybrid_diagnostics.layout_pages}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-orange-700">Complex pages</p>
              <p className="text-2xl font-semibold text-orange-950">{job.hybrid_diagnostics.complex_pages.length}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-orange-700">Stage timings</p>
              <p className="text-sm text-orange-900">
                Layout {job.hybrid_diagnostics.timings.layout_seconds.toFixed(2)}s, vision {job.hybrid_diagnostics.timings.vision_seconds.toFixed(2)}s
              </p>
            </div>
          </div>
        </section>
      )}

      {job.status === 'success' && hasResult && (
        <CorrectionReviewPanel
          job={job}
          onCorrectionSaved={(correction: JobCorrection) => {
            console.log('Correction saved', correction.id);
          }}
        />
      )}
    </div>
  );
}
