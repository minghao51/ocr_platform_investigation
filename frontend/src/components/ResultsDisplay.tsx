import { Job } from '../lib/api';
import ProcessingStatus from './ProcessingStatus';
import ExtractedDataDisplay from './ExtractedDataDisplay';

interface ResultsDisplayProps {
  job: Job;
}

export default function ResultsDisplay({ job }: ResultsDisplayProps) {
  return (
    <div className="space-y-6">
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
        <ExtractedDataDisplay result={job.result} fileName={job.file_name} />
      )}
    </div>
  );
}
