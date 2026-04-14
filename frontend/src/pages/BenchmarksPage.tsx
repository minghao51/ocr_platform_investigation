import { useState, useEffect } from 'react';
import {
  listBenchmarkRuns,
  getBenchmarkRun,
  getBenchmarkResults,
  compareModels,
  getUsageAnalytics,
  BenchmarkRun,
  BenchmarkResult,
  ModelComparison,
  UsageAnalytics,
} from '../lib/api';

export default function BenchmarksPage() {
  const [comparison, setComparison] = useState<ModelComparison[]>([]);
  const [runs, setRuns] = useState<BenchmarkRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<BenchmarkRun | null>(null);
  const [selectedResults, setSelectedResults] = useState<BenchmarkResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [comparisonError, setComparisonError] = useState<string | null>(null);
  const [runsError, setRunsError] = useState<string | null>(null);
  const [datasetFilter, setDatasetFilter] = useState('cord');
  const [analytics, setAnalytics] = useState<UsageAnalytics | null>(null);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);

  useEffect(() => {
    loadComparison();
    loadRuns();
    loadAnalytics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetFilter]);

  const loadComparison = async () => {
    try {
      setLoading(true);
      setComparisonError(null);
      const data = await compareModels(datasetFilter, 50);
      setComparison(data.runs || []);
    } catch (err) {
      console.error('Failed to load comparison:', err);
      setComparisonError(err instanceof Error ? err.message : 'Failed to load benchmark comparison');
      setComparison([]);
    } finally {
      setLoading(false);
    }
  };

  const loadRuns = async () => {
    try {
      setRunsError(null);
      const data = await listBenchmarkRuns(100);
      setRuns(data);
    } catch (err) {
      console.error('Failed to load runs:', err);
      setRunsError(err instanceof Error ? err.message : 'Failed to load benchmark runs');
      setRuns([]);
    }
  };

  const loadAnalytics = async () => {
    try {
      setAnalyticsError(null);
      const data = await getUsageAnalytics();
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to load analytics:', err);
      setAnalyticsError(err instanceof Error ? err.message : 'Failed to load usage analytics');
      setAnalytics(null);
    }
  };

  const handleRunClick = async (runId: number) => {
    try {
      const run = await getBenchmarkRun(runId);
      const results = await getBenchmarkResults(runId);
      setSelectedRun(run);
      setSelectedResults(results);
    } catch (err) {
      console.error('Failed to load run details:', err);
    }
  };

  const getAccuracyColor = (accuracy: number | null) => {
    if (accuracy === null) return 'text-gray-400';
    if (accuracy >= 0.7) return 'text-green-600';
    if (accuracy >= 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Model Benchmarks</h1>

      <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold">Enterprise Usage Analytics</h2>
                <p className="text-sm text-gray-500 mt-1">
                  Production cost, throughput, correction rates, and benchmark accuracy in one view.
                </p>
              </div>
              <button
                onClick={loadAnalytics}
                className="px-4 py-2 bg-slate-900 text-white text-sm rounded-md hover:bg-slate-800"
              >
                Refresh Analytics
              </button>
            </div>

            {analyticsError && (
              <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
                {analyticsError}
              </div>
            )}

            {analytics && (
              <div className="mt-6 space-y-6">
                <div className="grid gap-4 md:grid-cols-4">
                  <div className="rounded-lg bg-slate-50 p-4">
                    <div className="text-sm text-slate-500">Jobs</div>
                    <div className="mt-2 text-2xl font-semibold text-slate-900">{analytics.overview.total_jobs}</div>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-4">
                    <div className="text-sm text-slate-500">Success Rate</div>
                    <div className="mt-2 text-2xl font-semibold text-slate-900">
                      {(analytics.overview.success_rate * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-4">
                    <div className="text-sm text-slate-500">Total Cost</div>
                    <div className="mt-2 text-2xl font-semibold text-slate-900">
                      ${analytics.overview.total_cost.toFixed(4)}
                    </div>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-4">
                    <div className="text-sm text-slate-500">Correction Rate</div>
                    <div className="mt-2 text-2xl font-semibold text-slate-900">
                      {(analytics.overview.production_correction_rate * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>

                <div className="grid gap-6 lg:grid-cols-2">
                  <div className="rounded-lg border border-gray-200">
                    <div className="border-b border-gray-200 px-4 py-3">
                      <h3 className="font-semibold text-gray-900">Provider / Model Breakdown</h3>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200 text-sm">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-2 text-left">Model</th>
                            <th className="px-4 py-2 text-right">Jobs</th>
                            <th className="px-4 py-2 text-right">Cost</th>
                            <th className="px-4 py-2 text-right">Correction</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 bg-white">
                          {analytics.provider_breakdown.slice(0, 8).map((row) => (
                            <tr key={`${row.provider}-${row.model}-${row.schema_name || 'none'}`}>
                              <td className="px-4 py-2">
                                <div className="font-medium text-gray-900">{row.model}</div>
                                <div className="text-xs text-gray-500">{row.provider}{row.schema_name ? ` • ${row.schema_name}` : ''}</div>
                              </td>
                              <td className="px-4 py-2 text-right">{row.total_jobs}</td>
                              <td className="px-4 py-2 text-right">${row.total_cost.toFixed(4)}</td>
                              <td className="px-4 py-2 text-right">{(row.correction_rate * 100).toFixed(1)}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className="rounded-lg border border-gray-200">
                    <div className="border-b border-gray-200 px-4 py-3">
                      <h3 className="font-semibold text-gray-900">Pipeline Distribution</h3>
                    </div>
                    <div className="divide-y divide-gray-200">
                      {analytics.pipeline_distribution.map((row) => (
                        <div key={row.processing_method} className="flex items-center justify-between px-4 py-3 text-sm">
                          <div>
                            <div className="font-medium text-gray-900">{row.processing_method}</div>
                            <div className="text-gray-500">Avg latency {row.avg_latency.toFixed(2)}s</div>
                          </div>
                          <div className="text-right">
                            <div className="font-medium text-gray-900">{row.job_count} jobs</div>
                            <div className="text-gray-500">${row.total_cost.toFixed(4)}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="border-t border-gray-200 px-4 py-3">
                      <h4 className="text-sm font-semibold text-gray-900">Top correction patterns</h4>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {analytics.correction_patterns.map((item) => (
                          <span key={item.feedback_tag} className="rounded-full bg-amber-100 px-3 py-1 text-xs text-amber-800">
                            {item.feedback_tag} ({item.frequency})
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Dataset Filter */}
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium text-gray-700">Dataset:</label>
              <select
                value={datasetFilter}
                onChange={(e) => setDatasetFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
                <option value="cord">CORD Receipts</option>
              </select>
              <button
                onClick={loadComparison}
                className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
              >
                Refresh
              </button>
            </div>
          </div>

          {comparisonError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800">{comparisonError}</p>
            </div>
          )}

          {/* Model Comparison Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold">Model Comparison</h2>
              <p className="text-sm text-gray-500 mt-1">
                Sorted by overall accuracy (highest first)
              </p>
            </div>

            {loading ? (
              <div className="p-8 text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
                <p className="mt-2 text-gray-500">Loading comparison...</p>
              </div>
            ) : comparison.length === 0 ? (
              <div className="p-8 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p className="mt-2 text-gray-500">No benchmark data available</p>
                <p className="text-sm text-gray-400 mt-1">
                  Run benchmarks using: <code className="bg-gray-100 px-2 py-1 rounded">uv run python cli.py run-benchmark</code>
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rank</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Model</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Provider</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Accuracy</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Latency</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Cost</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Samples</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Tokens</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {comparison.map((model, index) => (
                      <tr
                        key={model.run_id}
                        className="hover:bg-gray-50 cursor-pointer"
                        onClick={() => handleRunClick(model.run_id)}
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                            index === 0 ? 'bg-yellow-100 text-yellow-800' :
                            index === 1 ? 'bg-gray-200 text-gray-700' :
                            index === 2 ? 'bg-orange-100 text-orange-800' :
                            'bg-gray-100 text-gray-600'
                          }`}>
                            {index + 1}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="font-medium text-gray-900">{model.model}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {model.provider}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right">
                          <span className={`font-bold ${getAccuracyColor(model.overall_accuracy)}`}>
                            {model.overall_accuracy !== null ? `${(model.overall_accuracy * 100).toFixed(1)}%` : 'N/A'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-gray-600">
                          {model.avg_latency !== null ? `${model.avg_latency.toFixed(1)}s` : 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-gray-600">
                          {model.total_cost !== null ? `$${model.total_cost.toFixed(4)}` : 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-gray-600">
                          {model.sample_count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-gray-600">
                          {(model.total_prompt_tokens + model.total_completion_tokens).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {model.started_at ? new Date(model.started_at).toLocaleDateString() : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Run History */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold">Recent Benchmark Runs</h2>
            </div>
            <div className="divide-y divide-gray-200">
              {runsError && (
                <div className="p-6">
                  <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                    <p className="text-sm text-red-800">{runsError}</p>
                  </div>
                </div>
              )}
              {runs.length === 0 ? (
                <div className="p-8 text-center text-gray-500">No benchmark runs yet</div>
              ) : (
                runs.slice(0, 10).map((run) => (
                  <div
                    key={run.id}
                    className="px-6 py-4 hover:bg-gray-50 cursor-pointer"
                    onClick={() => handleRunClick(run.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-medium text-gray-900">#{run.id}</span>
                        <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {run.provider}
                        </span>
                        <span className="text-sm text-gray-700">{run.model}</span>
                        <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          {run.dataset}
                        </span>
                      </div>
                      <div className="flex items-center gap-6 text-sm">
                        <div className="text-right">
                          <div className="text-gray-500">Accuracy</div>
                          <div className={`font-medium ${getAccuracyColor(run.overall_accuracy)}`}>
                            {run.overall_accuracy !== null ? `${(run.overall_accuracy * 100).toFixed(1)}%` : 'Pending'}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-gray-500">Samples</div>
                          <div className="text-gray-900">{run.sample_count}</div>
                        </div>
                        <div className="text-right">
                          <div className="text-gray-500">Date</div>
                          <div className="text-gray-900">
                            {run.started_at ? new Date(run.started_at).toLocaleDateString() : 'N/A'}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Detailed Results Modal */}
          {selectedRun && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
              <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-semibold">Run #{selectedRun.id} Details</h3>
                    <p className="text-sm text-gray-500">
                      {selectedRun.provider} / {selectedRun.model} on {selectedRun.dataset}
                    </p>
                  </div>
                  <button
                    onClick={() => setSelectedRun(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <div className="p-6 overflow-y-auto max-h-[calc(80vh-80px)]">
                  {/* Summary Stats */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {selectedRun.overall_accuracy !== null ? `${(selectedRun.overall_accuracy * 100).toFixed(1)}%` : 'N/A'}
                      </div>
                      <div className="text-sm text-gray-500">Overall Accuracy</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {selectedRun.avg_latency !== null ? `${selectedRun.avg_latency.toFixed(1)}s` : 'N/A'}
                      </div>
                      <div className="text-sm text-gray-500">Avg Latency</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {selectedRun.total_cost !== null ? `$${selectedRun.total_cost.toFixed(4)}` : 'N/A'}
                      </div>
                      <div className="text-sm text-gray-500">Total Cost</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {(selectedRun.total_prompt_tokens + selectedRun.total_completion_tokens).toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-500">Total Tokens</div>
                    </div>
                  </div>

                  {/* Sample Results */}
                  <h4 className="text-lg font-semibold mb-3">Sample Results ({selectedResults.length})</h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left">#</th>
                          <th className="px-4 py-2 text-right">Accuracy</th>
                          <th className="px-4 py-2 text-right">Latency</th>
                          <th className="px-4 py-2 text-right">Cost</th>
                          <th className="px-4 py-2 text-left">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {selectedResults.map((result) => (
                          <tr key={result.id}>
                            <td className="px-4 py-2">{result.sample_index + 1}</td>
                            <td className="px-4 py-2 text-right">
                              <span className={`font-medium ${getAccuracyColor(result.accuracy_score)}`}>
                                {(result.accuracy_score * 100).toFixed(0)}%
                              </span>
                            </td>
                            <td className="px-4 py-2 text-right text-gray-600">
                              {result.latency.toFixed(1)}s
                            </td>
                            <td className="px-4 py-2 text-right text-gray-600">
                              ${result.cost.toFixed(4)}
                            </td>
                            <td className="px-4 py-2">
                              {result.error_message ? (
                                <span className="text-red-600 text-xs" title={result.error_message}>Error</span>
                              ) : (
                                <span className="text-green-600 text-xs">Success</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
    </div>
  );
}
