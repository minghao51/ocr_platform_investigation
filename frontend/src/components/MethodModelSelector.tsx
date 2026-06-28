import { useEffect, useMemo, useState } from 'react';
import { analyzePdf, getBenchmarkedModels } from '../lib/api';
import type { BenchmarkedModel, ExtractSettings, Provider } from '../lib/api';
import { Skeleton } from './LoadingSpinner';
import {
  type ExtractionMethod,
  getMethodMeta,
  getMethodPillClass,
  PILL_CLASS_DISABLED,
} from '../lib/methods';

interface MethodModelSelectorProps {
  provider: string;
  model: string;
  extractionMethod: ExtractionMethod;
  fileType: string | null;
  fileId: string | null;
  settings: ExtractSettings | null;
  onProviderChange: (provider: string) => void;
  onModelChange: (model: string) => void;
  onMethodChange: (method: ExtractionMethod) => void;
}

export default function MethodModelSelector({
  provider,
  model,
  extractionMethod,
  fileType,
  fileId,
  settings,
  onProviderChange,
  onModelChange,
  onMethodChange,
}: MethodModelSelectorProps) {
  const [benchmarkedModels, setBenchmarkedModels] = useState<BenchmarkedModel[]>([]);
  const [pdfMethods, setPdfMethods] = useState<ExtractionMethod[] | null>(null);

  useEffect(() => {
    getBenchmarkedModels().then(setBenchmarkedModels).catch(() => {});
  }, []);

  const allMethods = useMemo(
    () =>
      (settings?.extraction_methods.map(
        (method) => method.id as ExtractionMethod
      ) ?? []),
    [settings]
  );

  const providers = useMemo<Provider[]>(() => {
    const rawProviders = settings?.providers ?? [];
    return [...rawProviders].sort((a, b) => {
      if (a.is_default && !b.is_default) return -1;
      if (!a.is_default && b.is_default) return 1;
      if (a.has_api_key && !b.has_api_key) return -1;
      if (!a.has_api_key && b.has_api_key) return 1;
      return 0;
    });
  }, [settings]);

  const providerRequiredMethods = useMemo(
    () => (settings?.provider_required_methods ?? []) as ExtractionMethod[],
    [settings]
  );

  useEffect(() => {
    const defaultProvider =
      providers.find((item) => item.is_default && item.has_api_key) ||
      providers.find((item) => item.has_api_key && item.models.length > 0);
    if (defaultProvider && !provider) {
      onProviderChange(defaultProvider.name);
      if (!model) {
        onModelChange(defaultProvider.models[0]?.id || '');
      }
    }
  }, [providers, provider, model, onProviderChange, onModelChange]);

  useEffect(() => {
    if (!fileId || !fileType) {
      setPdfMethods(null);
      return;
    }
    if (fileType === 'application/pdf') {
      analyzePdf(fileId)
        .then((analysis) =>
          setPdfMethods(analysis.suggested_methods as ExtractionMethod[])
        )
        .catch(() =>
          setPdfMethods(
            (settings?.available_methods_by_file_type['application/pdf'] ??
              []) as ExtractionMethod[]
          )
        );
    } else {
      setPdfMethods(null);
    }
  }, [fileId, fileType, settings]);

  const availableMethods = useMemo(() => {
    if (!fileType) return allMethods;

    if (fileType === 'application/pdf') {
      return (
        pdfMethods ||
        ((settings?.available_methods_by_file_type['application/pdf'] ??
          []) as ExtractionMethod[])
      );
    }

    if (fileType.startsWith('image/')) {
      return (settings?.available_methods_by_file_type['image/*'] ??
        []) as ExtractionMethod[];
    }

    return (settings?.available_methods_by_file_type['document/*'] ??
      []) as ExtractionMethod[];
  }, [allMethods, fileType, pdfMethods, settings]);

  useEffect(() => {
    if (
      availableMethods.length > 0 &&
      !availableMethods.includes(extractionMethod)
    ) {
      onMethodChange(availableMethods[0]);
    }
  }, [availableMethods, extractionMethod, onMethodChange]);

  const selectedProvider = providers.find((item) => item.name === provider);
  const availableModels = selectedProvider?.models || [];
  const requiresProvider = providerRequiredMethods.includes(extractionMethod);

  const getBenchmarkBadge = (modelId: string) => {
    const benchmark = benchmarkedModels.find(
      (item) => item.model === modelId && item.provider === provider
    );
    if (!benchmark || benchmark.accuracy == null) return null;
    return `${(benchmark.accuracy * 100).toFixed(1)}% acc`;
  };

  if (!settings) {
    return (
      <div className="space-y-4">
        <div>
          <Skeleton className="h-4 w-20 mb-2" />
          <Skeleton className="h-10 w-full" />
        </div>
        <div>
          <Skeleton className="h-4 w-16 mb-2" />
          <Skeleton className="h-10 w-full" />
        </div>
      </div>
    );
  }

  if (providers.length === 0 && requiresProvider) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
        <p className="text-sm text-yellow-800">
          No providers configured. Please add API keys to `.env` file.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Extraction Method
        </label>
        <div className="flex flex-wrap gap-2">
          {allMethods.map((method) => {
            const isAvailable = availableMethods.includes(method);
            const isSelected = extractionMethod === method;
            const colorClass = isAvailable
              ? getMethodPillClass(method)
              : PILL_CLASS_DISABLED;

            return (
              <button
                key={method}
                onClick={() => isAvailable && onMethodChange(method)}
                disabled={!isAvailable}
                className={`
                  px-3 py-1.5 text-xs font-medium rounded-full border transition-all
                  ${colorClass}
                  ${
                    isSelected && isAvailable
                      ? 'ring-2 ring-offset-1 ring-blue-500'
                      : ''
                  }
                `}
                title={!isAvailable ? 'Not available for this file type' : undefined}
              >
                {getMethodMeta(method).label}
              </button>
            );
          })}
        </div>
        {fileType && availableMethods.length === 1 && (
          <p className="mt-2 text-xs text-gray-500">
            Auto-selected: only{' '}
            <span className="font-medium">
              {getMethodMeta(availableMethods[0]).label}
            </span>{' '}
            is available for this file type.
          </p>
        )}
        {fileType === 'application/pdf' && pdfMethods && (
          <p className="mt-2 text-xs text-gray-500">
            {pdfMethods.length < allMethods.length
              ? 'PDF appears to be image-based. Text extraction methods are available but may not work well.'
              : 'PDF has a text layer. All extraction methods are available.'}
          </p>
        )}
      </div>

      {requiresProvider ? (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Provider
            </label>
            <select
              value={provider}
              onChange={(event) => {
                onProviderChange(event.target.value);
                const newProvider = providers.find(
                  (item) => item.name === event.target.value
                );
                if (newProvider && newProvider.models.length > 0) {
                  onModelChange(newProvider.models[0].id);
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {providers.map((item) => (
                <option
                  key={item.name}
                  value={item.name}
                  disabled={!item.has_api_key}
                  className={!item.has_api_key ? 'text-gray-400 bg-gray-50' : ''}
                  title={!item.has_api_key ? 'No API key configured' : undefined}
                >
                  {item.display_name} {!item.has_api_key && '(No key)'}{' '}
                  {item.is_default ? '★' : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Model
            </label>
            <select
              value={model}
              onChange={(event) => onModelChange(event.target.value)}
              disabled={availableModels.length === 0}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              {availableModels.map((item) => {
                const badge = getBenchmarkBadge(item.id);
                return (
                  <option key={item.id} value={item.id}>
                    {item.name}
                    {badge ? ` — ${badge}` : ''}
                  </option>
                );
              })}
            </select>
            {availableModels.length === 0 && (
              <p className="text-xs text-gray-500 mt-1">No models available</p>
            )}
          </div>
        </>
      ) : (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          This method runs locally with Docling and does not require a provider
          or model selection.
        </div>
      )}
    </div>
  );
}
