import React from 'react';
import { QualityReport, QualityCheck } from '../lib/api';

interface QualityBadgeProps {
  report: QualityReport;
  compact?: boolean;
}

const levelColors: Record<string, { bg: string; text: string; border: string; icon: string }> = {
  excellent: { bg: 'bg-emerald-50', text: 'text-emerald-800', border: 'border-emerald-200', icon: '✓' },
  good: { bg: 'bg-green-50', text: 'text-green-800', border: 'border-green-200', icon: '✓' },
  acceptable: { bg: 'bg-yellow-50', text: 'text-yellow-800', border: 'border-yellow-200', icon: '⚠' },
  poor: { bg: 'bg-orange-50', text: 'text-orange-800', border: 'border-orange-200', icon: '✗' },
  critical: { bg: 'bg-red-50', text: 'text-red-800', border: 'border-red-200', icon: '✗' },
};

const severityColors: Record<string, { bg: string; text: string; dot: string }> = {
  pass: { bg: 'bg-green-100', text: 'text-green-700', dot: 'bg-green-500' },
  warn: { bg: 'bg-yellow-100', text: 'text-yellow-700', dot: 'bg-yellow-500' },
  fail: { bg: 'bg-red-100', text: 'text-red-700', dot: 'bg-red-500' },
};

const checkLabels: Record<string, string> = {
  blur: 'Sharpness',
  skew: 'Alignment',
  noise: 'Noise Level',
  contrast: 'Contrast',
  brightness: 'Brightness',
  content_density: 'Content Density',
  resolution: 'Resolution',
};

export const QualityBadge: React.FC<QualityBadgeProps> = ({ report, compact = false }) => {
  const colors = levelColors[report.level] || levelColors.acceptable;

  if (compact) {
    return (
      <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${colors.bg} ${colors.text} ${colors.border}`}>
        <span>{colors.icon}</span>
        <span>Quality: {report.overall_score}/100</span>
      </div>
    );
  }

  return (
    <div className={`rounded-lg border p-4 ${colors.bg} ${colors.border}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`text-lg font-bold ${colors.text}`}>{colors.icon}</span>
          <div>
            <h4 className={`font-semibold text-sm ${colors.text}`}>
              Image Quality: {report.level.charAt(0).toUpperCase() + report.level.slice(1)}
            </h4>
            <p className={`text-xs ${colors.text} opacity-75`}>
              Overall Score: {report.overall_score}/100
            </p>
          </div>
        </div>
        {!report.passed && (
          <span className="px-2 py-0.5 text-xs font-medium bg-red-100 text-red-700 rounded-full">
            Below Threshold
          </span>
        )}
      </div>

      {/* Score bar */}
      <div className="mb-3">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${
              report.overall_score >= 80 ? 'bg-emerald-500' :
              report.overall_score >= 60 ? 'bg-green-500' :
              report.overall_score >= 40 ? 'bg-yellow-500' :
              report.overall_score >= 20 ? 'bg-orange-500' : 'bg-red-500'
            }`}
            style={{ width: `${Math.min(100, report.overall_score)}%` }}
          />
        </div>
      </div>

      {/* Individual checks */}
      <div className="space-y-1.5">
        {Object.entries(report.checks).map(([key, check]) => (
          <CheckRow key={key} name={key} check={check} />
        ))}
      </div>

      {/* Recommendations */}
      {report.recommendations.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200/50">
          <p className={`text-xs font-medium mb-1 ${colors.text}`}>Issues:</p>
          <ul className="text-xs space-y-0.5 opacity-80">
            {report.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-1">
                <span className="mt-0.5">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Auto-fix info */}
      {report.auto_fixable_issues.length > 0 && (
        <div className="mt-2 pt-2 border-t border-gray-200/50">
          <p className="text-xs text-blue-600 font-medium">
            🔧 Auto-fixable: {report.auto_fixable_issues.join(', ')}
          </p>
        </div>
      )}

      {/* Rejection reason */}
      {report.should_reject && report.rejection_reason && (
        <div className="mt-2 p-2 bg-red-100 rounded text-xs text-red-700 font-medium">
          {report.rejection_reason}
        </div>
      )}
    </div>
  );
};

const CheckRow: React.FC<{ name: string; check: QualityCheck }> = ({ name, check }) => {
  const colors = severityColors[check.severity];
  const label = checkLabels[name] || name;

  return (
    <div className="flex items-center justify-between text-xs">
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${colors.dot}`} />
        <span className="text-gray-700">{label}</span>
      </div>
      <div className={`flex items-center gap-2 px-2 py-0.5 rounded ${colors.bg} ${colors.text}`}>
        <span className="font-medium">{check.score.toFixed(0)}</span>
        {check.auto_fixable && <span title="Auto-fixable" className="text-[10px]">🔧</span>}
      </div>
    </div>
  );
};

// Simple score-only badge for list views
export const QualityScoreBadge: React.FC<{ score?: number }> = ({ score }) => {
  if (score === undefined || score === null) return null;

  const colors =
    score >= 80 ? 'bg-emerald-100 text-emerald-700' :
    score >= 60 ? 'bg-green-100 text-green-700' :
    score >= 40 ? 'bg-yellow-100 text-yellow-700' :
    score >= 20 ? 'bg-orange-100 text-orange-700' : 'bg-red-100 text-red-700';

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colors}`}>
      Q: {score.toFixed(0)}
    </span>
  );
};
