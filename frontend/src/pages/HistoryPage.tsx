import { useState, useEffect } from 'react';
import { listJobs, getJob, deleteJob, Job } from '../lib/api';
import ResultsDisplay from '../components/ResultsDisplay';

export default function HistoryPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState({ status: '', provider: '' });

  useEffect(() => {
    loadJobs();
  }, [filter]);

  const loadJobs = async () => {
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
                  <option value="nebius">Nebius</option>
                  <option value="openrouter">OpenRouter</option>
                  <option value="gemini">Gemini</option>
                </select>
              </div>
            </div>

            <h2 className="text-lg font-semibold mb-4">Jobs ({jobs.length})</h2>
            {loading ? (
              <div className="animate-pulse space-y-2">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-16 bg-gray-200 rounded"></div>
                ))}
              </div>
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
                      <span className={'px-2 py-1 rounded-full text-xs ' + getStatusColor(job.status)}>
                        {job.status}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(job.created_at).toLocaleString()}
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
    </div>
  );
}
