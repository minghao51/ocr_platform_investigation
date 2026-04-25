import { useState, useEffect, useMemo } from 'react';
import { listProviders, analyzePdf, getBenchmarkedModels, Provider, BenchmarkedModel } from '../lib/api';
import { Skeleton } from './LoadingSpinner';
import { ExtractionMethod } from './ExtractionModeSelector';

const PROVIDER_REQUIRED_METHODS: ExtractionMethod[] = [
  'auto',
  'text',
  'vision',
  'hybrid',
  'docling-parse',
  'transcription',
];

const FILE_TYPE_METHODS: Record<string, ExtractionMethod[]> = {
  image: ['docling-extract', 'vision'],
  audio: ['transcription'],
  document: ['docling-parse', 'transcription'],
};

const PDF_ALL_METHODS: ExtractionMethod[] = [
  'docling-extract', 'docling-parse', 'auto', 'text', 'vision', 'hybrid', 'transcription',
];

const METHOD_LABELS: Record<string, string> = {
  auto: 'Auto',
  text: 'Text',
  vision: 'Vision',
  hybrid: 'Hybrid',
  'docling-parse': 'PyMuPDF + LLM',
  'docling-extract': 'Docling Local Extract',
  transcription: 'Transcription',
};

const METHOD_COLORS: Record<string, string> = {
  auto: 'bg-purple-100 border-purple-300 text-purple-800',
  text: 'bg-green-100 border-green-300 text-green-800',
  vision: 'bg-blue-100 border-blue-300 text-blue-800',
  hybrid: 'bg-orange-100 border-orange-300 text-orange-800',
  'docling-parse': 'bg-indigo-100 border-indigo-300 text-indigo-800',
  'docling-extract': 'bg-emerald-100 border-emerald-300 text-emerald-800',
  transcription: 'bg-teal-100 border-teal-300 text-teal-800',
};

const METHOD_COLORS_DISABLED = 'bg-gray-100 border-gray-200 text-gray-400 cursor-not-allowed';

interface MethodModelSelectorProps {
  provider: string;
  model: string;
  extractionMethod: ExtractionMethod;
  fileType: string | null;
  fileId: string | null;
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
  onProviderChange,
  onModelChange,
  onMethodChange,
}: MethodModelSelectorProps) {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [benchmarkedModels, setBenchmarkedModels] = useState<BenchmarkedModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pdfMethods, setPdfMethods] = useState<ExtractionMethod[] | null>(null);

  useEffect(() => {
    loadProviders();
    getBenchmarkedModels().then(setBenchmarkedModels).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!fileId || !fileType) {
      setPdfMethods(null);
      return;
    }
    if (fileType === 'application/pdf') {
      analyzePdf(fileId)
        .then((analysis) => setPdfMethods(analysis.suggested_methods as ExtractionMethod[]))
        .catch(() => setPdfMethods(PDF_ALL_METHODS));
    } else {
      setPdfMethods(null);
    }
  }, [fileId, fileType]);

  const loadProviders = async () => {
    try {
      setLoading(true);
      const data = await listProviders();

      const sortedProviders = data.sort((a, b) => {
        if (a.is_default && !b.is_default) return -1;
        if (!a.is_default && b.is_default) return 1;
        if (a.has_api_key && !b.has_api_key) return -1;
        if (!a.has_api_key && b.has_api_key) return 1;
        return 0;
      });

      setProviders(sortedProviders);

      const defaultProvider = sortedProviders.find((p) => p.is_default && p.has_api_key)
        || sortedProviders.find((p) => p.has_api_key && p.models.length > 0);
      if (defaultProvider && !provider) {
        onProviderChange(defaultProvider.name);
        if (!model) {
          onModelChange(defaultProvider.models[0]?.id || '');
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load providers');
    } finally {
      setLoading(false);
    }
  };

  const availableMethods = useMemo(() => {
    if (!fileType) return PDF_ALL_METHODS;

    if (fileType === 'application/pdf') {
      return pdfMethods || PDF_ALL_METHODS;
    }

    if (fileType.startsWith('image/')) return FILE_TYPE_METHODS.image;
    if (fileType.startsWith('audio/')) return FILE_TYPE_METHODS.audio;

    return FILE_TYPE_METHODS.document;
  }, [fileType, pdfMethods]);

  useEffect(() => {
    if (availableMethods.length > 0 && !availableMethods.includes(extractionMethod)) {
      onMethodChange(availableMethods[0]);
    }
  }, [availableMethods, extractionMethod, onMethodChange]);

  const selectedProvider = providers.find((p) => p.name === provider);
  const availableModels = selectedProvider?.models || [];
  const requiresProvider = PROVIDER_REQUIRED_METHODS.includes(extractionMethod);

  const getBenchmarkBadge = (modelId: string) => {
    const bm = benchmarkedModels.find(
      (b) => b.model === modelId && b.provider === provider
    );
    if (!bm || bm.accuracy == null) return null;
    return `${(bm.accuracy * 100).toFixed(1)}% acc`;
  };

  if (loading) {
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

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-md">
        <p className="text-sm text-red-600">{error}</p>
        <button onClick={loadProviders} className="mt-2 text-sm text-red-700 underline">
          Retry
        </button>
      </div>
    );
  }

  if (providers.length === 0 && requiresProvider) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
        <p className="text-sm text-yellow-800">
          No providers configured. Please add API keys to .env file.
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
          {PDF_ALL_METHODS.map((method) => {
            const isAvailable = availableMethods.includes(method);
            const isSelected = extractionMethod === method;
            const colorClass = isAvailable ? METHOD_COLORS[method] : METHOD_COLORS_DISABLED;

            return (
              <button
                key={method}
                onClick={() => isAvailable && onMethodChange(method)}
                disabled={!isAvailable}
                className={`
                  px-3 py-1.5 text-xs font-medium rounded-full border transition-all
                  ${colorClass}
                  ${isSelected && isAvailable ? 'ring-2 ring-offset-1 ring-blue-500' : ''}
                `}
                title={!isAvailable ? 'Not available for this file type' : undefined}
              >
                {METHOD_LABELS[method]}
              </button>
            );
          })}
        </div>
        {fileType && availableMethods.length === 1 && (
          <p className="mt-2 text-xs text-gray-500">
            Auto-selected: only <span className="font-medium">{METHOD_LABELS[availableMethods[0]]}</span> is available for this file type.
          </p>
        )}
        {fileType === 'application/pdf' && pdfMethods && (
          <p className="mt-2 text-xs text-gray-500">
            {pdfMethods.length < PDF_ALL_METHODS.length
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
              onChange={(e) => {
                onProviderChange(e.target.value);
                const newProvider = providers.find((p) => p.name === e.target.value);
                if (newProvider && newProvider.models.length > 0) {
                  onModelChange(newProvider.models[0].id);
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {providers.map((p) => (
                <option
                  key={p.name}
                  value={p.name}
                  disabled={!p.has_api_key}
                  className={!p.has_api_key ? 'text-gray-400 bg-gray-50' : ''}
                  title={!p.has_api_key ? 'No API key configured' : undefined}
                >
                  {p.display_name} {!p.has_api_key && '(No key)'} {p.is_default ? '★' : ''}
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
              onChange={(e) => onModelChange(e.target.value)}
              disabled={availableModels.length === 0}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              {availableModels.map((m) => {
                const badge = getBenchmarkBadge(m.id);
                return (
                  <option key={m.id} value={m.id}>
                    {m.name}{badge ? ` — ${badge}` : ''}
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
          This method runs locally with Docling and does not require a provider or model selection.
        </div>
      )}
    </div>
  );
}
