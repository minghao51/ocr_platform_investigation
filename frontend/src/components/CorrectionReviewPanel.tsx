import { useEffect, useState } from 'react';
import {
  Job,
  JobCorrection,
  createJobCorrection,
  getCurrentUser,
  listJobCorrections,
} from '@/lib/api';

const feedbackOptions = [
  { id: 'wrong_field', label: 'Wrong field' },
  { id: 'missed_field', label: 'Missed field' },
  { id: 'bad_type', label: 'Bad type' },
  { id: 'layout_issue', label: 'Layout issue' },
] as const;

interface CorrectionReviewPanelProps {
  job: Job;
  onCorrectionSaved?: (correction: JobCorrection) => void;
}

export default function CorrectionReviewPanel({
  job,
  onCorrectionSaved,
}: CorrectionReviewPanelProps) {
  const currentUser = getCurrentUser();
  const [jsonDraft, setJsonDraft] = useState('');
  const [notes, setNotes] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [history, setHistory] = useState<JobCorrection[]>([]);
  const [hasSavedCorrection, setHasSavedCorrection] = useState(job.correction_status === 'corrected');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    setJsonDraft(JSON.stringify(job.result, null, 2));
  }, [job.result]);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        setLoadingHistory(true);
        const corrections = await listJobCorrections(job.job_id);
        setHistory(corrections);
      } catch {
        setHistory([]);
      } finally {
        setLoadingHistory(false);
      }
    };
    void loadHistory();
  }, [job.job_id]);

  if (!currentUser || job.status !== 'success' || !job.result || typeof job.result !== 'object') {
    return null;
  }

  const toggleTag = (tag: string) => {
    setSelectedTags((current) =>
      current.includes(tag) ? current.filter((item) => item !== tag) : [...current, tag]
    );
  };

  const handleSave = async () => {
    setError(null);
    setSuccess(null);
    let correctedResult: Record<string, unknown>;
    try {
      correctedResult = JSON.parse(jsonDraft) as Record<string, unknown>;
    } catch (parseError) {
      setError(parseError instanceof Error ? parseError.message : 'Invalid JSON');
      return;
    }

    setSaving(true);
    try {
      const correction = await createJobCorrection(
        job.job_id,
        correctedResult,
        selectedTags,
        notes || undefined,
      );
      setHistory((current) => [correction, ...current]);
      setHasSavedCorrection(true);
      setSuccess('Correction saved');
      setNotes('');
      setSelectedTags([]);
      onCorrectionSaved?.(correction);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'Failed to save correction');
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="space-y-4 rounded-lg border border-amber-200 bg-amber-50 p-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-amber-950">Human-in-the-Loop Review</h3>
          <p className="text-sm text-amber-800">
            Correct the extracted JSON, tag the issue, and save it to improve future prompt/routing behavior.
          </p>
        </div>
        {(job.correction_status === 'corrected' || hasSavedCorrection) && (
          <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
            Corrected
          </span>
        )}
      </div>

      <textarea
        value={jsonDraft}
        onChange={(e) => setJsonDraft(e.target.value)}
        className="min-h-[18rem] w-full rounded-md border border-amber-200 bg-white p-3 font-mono text-sm text-slate-800"
        spellCheck={false}
      />

      <div className="flex flex-wrap gap-2">
        {feedbackOptions.map((option) => (
          <button
            key={option.id}
            type="button"
            onClick={() => toggleTag(option.id)}
            className={`rounded-full border px-3 py-1 text-sm transition-colors ${
              selectedTags.includes(option.id)
                ? 'border-amber-500 bg-amber-200 text-amber-950'
                : 'border-amber-200 bg-white text-amber-900'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>

      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Optional reviewer notes"
        className="min-h-[5rem] w-full rounded-md border border-amber-200 bg-white p-3 text-sm text-slate-800"
      />

      <div className="flex items-center justify-between">
        <div className="text-sm">
          {error && <span className="text-red-700">{error}</span>}
          {!error && success && <span className="text-emerald-700">{success}</span>}
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 disabled:bg-amber-300"
        >
          {saving ? 'Saving...' : 'Save Correction'}
        </button>
      </div>

      <div className="rounded-md border border-amber-200 bg-white p-4">
        <h4 className="text-sm font-semibold text-slate-900">Correction History</h4>
        {loadingHistory ? (
          <p className="mt-2 text-sm text-slate-500">Loading corrections...</p>
        ) : history.length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">No corrections recorded yet.</p>
        ) : (
          <div className="mt-3 space-y-3">
            {history.map((entry) => (
              <div key={entry.id} className="rounded-md border border-slate-200 bg-slate-50 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-medium text-slate-900">
                    {entry.reviewer_username || 'Reviewer'} on {new Date(entry.created_at).toLocaleString()}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {entry.feedback_tags?.map((tag) => (
                      <span key={tag} className="rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-700">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                {entry.diff_summary?.length > 0 && (
                  <div className="mt-2 text-sm text-slate-700">
                    {entry.diff_summary.slice(0, 4).map((change) => (
                      <div key={`${entry.id}-${change.path}`}>
                        <span className="font-medium">{change.path}</span>: {change.change_type}
                      </div>
                    ))}
                  </div>
                )}
                {entry.notes && <p className="mt-2 text-sm text-slate-600">{entry.notes}</p>}
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
