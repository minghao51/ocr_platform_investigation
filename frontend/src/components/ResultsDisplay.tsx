import { Job } from '../lib/api';

interface ResultsDisplayProps {
  job: Job;
}

export default function ResultsDisplay({ job }: ResultsDisplayProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-100 text-green-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="space-y-6">
      {/* Status Overview */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Processing Status</h3>
          <span className={'px-3 py-1 rounded-full text-sm font-medium ' + getStatusColor(job.status)}>
            {job.status.toUpperCase()}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">File:</span>
            <span className="ml-2 font-medium">{job.file_name}</span>
          </div>
          <div>
            <span className="text-gray-500">Type:</span>
            <span className="ml-2 font-medium">{job.file_type}</span>
          </div>
          <div>
            <span className="text-gray-500">Provider:</span>
            <span className="ml-2 font-medium">{job.provider}</span>
          </div>
          <div>
            <span className="text-gray-500">Model:</span>
            <span className="ml-2 font-medium">{job.model}</span>
          </div>
          <div>
            <span className="text-gray-500">Schema:</span>
            <span className="ml-2 font-medium">{job.schema_name}</span>
          </div>
          {job.processing_time && (
            <div>
              <span className="text-gray-500">Processing Time:</span>
              <span className="ml-2 font-medium">{job.processing_time.toFixed(2)}s</span>
            </div>
          )}
          <div className="col-span-2">
            <span className="text-gray-500">Created:</span>
            <span className="ml-2 font-medium">{formatDate(job.created_at)}</span>
          </div>
        </div>
      </div>

      {/* Error */}
      {job.status === 'error' && job.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h4 className="text-sm font-semibold text-red-800 mb-2">Error Details</h4>
          <pre className="text-sm text-red-700 whitespace-pre-wrap">{job.error}</pre>
        </div>
      )}

      {/* Results */}
      {job.status === 'success' && job.result && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Extracted Data</h3>
            <button
              onClick={() => navigator.clipboard.writeText(JSON.stringify(job.result, null, 2))}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Copy JSON
            </button>
          </div>
          <pre className="bg-gray-50 p-4 rounded-md overflow-auto max-h-96">
            {JSON.stringify(job.result, null, 2)}
          </pre>
        </div>
      )}

      {/* Processing State */}
      {(job.status === 'pending' || job.status === 'processing') && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center">
            <svg className="animate-spin h-5 w-5 text-blue-600 mr-3" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <p className="text-blue-800">
              {job.status === 'pending' ? 'Job is queued...' : 'Processing document...'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
