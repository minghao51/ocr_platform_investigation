import { useState, useEffect } from 'react';
import { listJobs, getJob, deleteJob, Job } from '../lib/api';
import ResultsDisplay from '../components/ResultsDisplay';
import { SkeletonList } from '@/components/LoadingSpinner';

interface HistoryPageProps {
  isAuthenticated: boolean;
}

export default function HistoryPage({ isAuthenticated }: HistoryPageProps) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState({ status: '', provider: '' });

  useEffect(() => {
    if (!isAuthenticated) {
      setJobs([]);
      setSelectedJob(null);
      setError(null);
      setLoading(false);
      return;
    }
    loadJobs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter, isAuthenticated]);

  const loadJobs = async () => {
    if (!isAuthenticated) {
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const data = await listJobs(
        filter.status || undefined,
        filter.provider || undefined,
        50
      );
      setJobs(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load jobs';
      console.error('Failed to load jobs:', err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleJobClick = async (jobId: number) => {
    try {
      const job = await getJob(jobId);
      setSelectedJob(job);
    } catch (err) {
      console.error('Failed to load job:', err);
    }
  };

  const handleDelete = async (jobId: number) => {
    if (!confirm('Are you sure you want to delete this job?')) {
      return;
    }

    try {
      await deleteJob(jobId);
      if (selectedJob?.job_id === jobId) {
        setSelectedJob(null);
      }
      loadJobs();
    } catch (err) {
      console.error('Failed to delete job:', err);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-100 text-green-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Processing History</h1>

      {!isAuthenticated && (
        <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 p-4">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 rounded-full bg-amber-100 p-2 text-amber-700">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12A9 9 0 113 12a9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-amber-900">History is available after sign-in.</p>
              <p className="mt-1 text-sm text-amber-800">
                Use the top-right guest menu to log in with an admin or demo account, then your OCR jobs will appear here.
              </p>
            </div>
          </div>
        </div>
      )}

      {isAuthenticated && (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Job List */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow p-4">
            <h2 className="text-lg font-semibold mb-4">Filters</h2>
            <div className="space-y-3 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  value={filter.status}
                  onChange={(e) => setFilter({ ...filter, status: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="">All</option>
                  <option value="success">Success</option>
                  <option value="error">Error</option>
                  <option value="processing">Processing</option>
                  <option value="pending">Pending</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Provider
                </label>
                <select
                  value={filter.provider}
                  onChange={(e) => setFilter({ ...filter, provider: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="">All</option>
                  <option value="openrouter">OpenRouter</option>
                  <option value="gemini">Gemini</option>
                  <option value="litellm">LiteLLM (Unified)</option>
                </select>
              </div>
            </div>

            <h2 className="text-lg font-semibold mb-4">Jobs ({jobs.length})</h2>
            {loading ? (
              <SkeletonList count={5} />
            ) : error ? (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <p className="text-sm text-red-800 mb-3">{error}</p>
                <button
                  onClick={loadJobs}
                  className="w-full px-4 py-2 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 transition-colors"
                >
                  Retry
                </button>
              </div>
            ) : jobs.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">No jobs found</p>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {jobs.map((job) => (
                  <div
                    key={job.job_id}
                    className="p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => handleJobClick(job.job_id)}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium truncate">{job.file_name}</span>
                      <div className="flex items-center gap-2">
                        {job.processing_method && (
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            job.processing_method === 'text'
                              ? 'bg-green-100 text-green-800'
                              : job.processing_method === 'hybrid'
                                ? 'bg-orange-100 text-orange-800'
                                : 'bg-blue-100 text-blue-800'
                          }`}>
                            {job.processing_method}
                          </span>
                        )}
                        {job.correction_status === 'corrected' && (
                          <span className="px-2 py-1 rounded-full text-xs bg-amber-100 text-amber-800">
                            corrected
                          </span>
                        )}
                        <span className={'px-2 py-1 rounded-full text-xs ' + getStatusColor(job.status)}>
                          {job.status}
                        </span>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">
                      {job.created_at ? new Date(job.created_at).toLocaleString() : 'N/A'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Job Details */}
        <div className="lg:col-span-2">
          {selectedJob ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Job Details</h2>
                <button
                  onClick={() => handleDelete(selectedJob.job_id)}
                  className="px-4 py-2 text-sm text-red-600 border border-red-300 rounded-md hover:bg-red-50"
                >
                  Delete Job
                </button>
              </div>
              <ResultsDisplay job={selectedJob} />
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="mt-2 text-sm text-gray-500">Select a job to view details</p>
            </div>
          )}
        </div>
      </div>
      )}
    </div>
  );
}
