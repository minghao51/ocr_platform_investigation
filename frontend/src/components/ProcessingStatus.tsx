import { Job } from '../lib/api';
import { useState, useEffect } from 'react';
import { QualityBadge, QualityScoreBadge } from './QualityBadge';

interface ProcessingStatusProps {
  job: Job;
}

export default function ProcessingStatus({ job }: ProcessingStatusProps) {
  const [elapsedTime, setElapsedTime] = useState(0);
  const [jobStartTime] = useState(() => {
    // Use the job's created_at if available, otherwise use current time
    // This handles the case where a temporary job object doesn't have created_at yet
    return Date.now();
  });

  useEffect(() => {
    // Only track elapsed time for pending/processing jobs
    if (job.status === 'pending' || job.status === 'processing') {
      const interval = setInterval(() => {
        const now = Date.now();
        setElapsedTime(Math.floor((now - jobStartTime) / 1000));
      }, 1000);

      return () => clearInterval(interval);
    } else {
      // Reset elapsed time when job completes
      setElapsedTime(0);
    }
  }, [job.status, jobStartTime]);
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

  const formatElapsedTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  const isCompleted = job.status === 'success' || job.status === 'error';

  return (
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
        {job.processing_time ? (
          <div>
            <span className="text-gray-500">Processing Time:</span>
            <span className="ml-2 font-medium">{job.processing_time.toFixed(2)}s</span>
          </div>
        ) : (job.status === 'pending' || job.status === 'processing') && elapsedTime > 0 ? (
          <div>
            <span className="text-gray-500">Elapsed Time:</span>
            <span className="ml-2 font-medium">{formatElapsedTime(elapsedTime)}</span>
          </div>
        ) : null}
        {job.created_at && (
          <div className="col-span-2">
            <span className="text-gray-500">Created:</span>
            <span className="ml-2 font-medium">{formatDate(job.created_at)}</span>
          </div>
        )}
        {isCompleted && job.updated_at && (
          <div className="col-span-2">
            <span className="text-gray-500">Completed:</span>
            <span className="ml-2 font-medium">{formatDate(job.updated_at)}</span>
          </div>
        )}
        {/* Quality Score */}
        {job.quality_score !== undefined && job.quality_score !== null && (
          <div className="col-span-2 flex items-center gap-2">
            <span className="text-gray-500">Quality:</span>
            <QualityScoreBadge score={job.quality_score} />
            {job.preprocessing_applied && job.preprocessing_applied.length > 0 && (
              <span className="text-xs text-blue-600">
                (preprocessed: {job.preprocessing_applied.join(', ')})
              </span>
            )}
          </div>
        )}
      </div>

      {/* Detailed Quality Report (for completed jobs) */}
      {isCompleted && job.quality_checks && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <QualityBadge report={job.quality_checks} compact={false} />
        </div>
      )}

      {/* Processing State */}
      {(job.status === 'pending' || job.status === 'processing') && (
        <div className="mt-6 flex items-center">
          <svg className="animate-spin h-5 w-5 text-blue-600 mr-3" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="text-blue-800">
            {job.status === 'pending' ? 'Job is queued...' : 'Processing document...'}
          </p>
        </div>
      )}
    </div>
  );
}
