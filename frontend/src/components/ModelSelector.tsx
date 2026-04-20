import { useState, useEffect } from 'react';
import { listProviders, Provider } from '../lib/api';
import { Skeleton } from './LoadingSpinner';

interface ModelSelectorProps {
  provider: string;
  model: string;
  onProviderChange: (provider: string) => void;
  onModelChange: (model: string) => void;
}

export default function ModelSelector({
  provider,
  model,
  onProviderChange,
  onModelChange,
}: ModelSelectorProps) {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProviders();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadProviders = async () => {
    try {
      setLoading(true);
      const data = await listProviders();

      // Sort providers: Gemini first, then enabled providers, then disabled providers
      const sortedProviders = data.sort((a, b) => {
        const ORDER = ['gemini', 'openrouter', 'litellm'];
        const ai = ORDER.indexOf(a.name);
        const bi = ORDER.indexOf(b.name);
        if (ai !== -1 && bi !== -1) return ai - bi;
        if (ai !== -1) return -1;
        if (bi !== -1) return -1;

        if (a.has_api_key && !b.has_api_key) return -1;
        if (!a.has_api_key && b.has_api_key) return 1;

        return 0;
      });

      setProviders(sortedProviders);

      // Auto-select first available provider and model if not set
      const firstAvailableProvider = sortedProviders.find(p => p.has_api_key && p.models.length > 0);
      if (firstAvailableProvider && !provider) {
        onProviderChange(firstAvailableProvider.name);
        if (!model) {
          onModelChange(firstAvailableProvider.models[0].id);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load providers');
    } finally {
      setLoading(false);
    }
  };

  const selectedProvider = providers.find(p => p.name === provider);
  const availableModels = selectedProvider?.models || [];

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
        <button
          onClick={loadProviders}
          className="mt-2 text-sm text-red-700 underline"
        >
          Retry
        </button>
      </div>
    );
  }

  if (providers.length === 0) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
        <p className="text-sm text-yellow-800">
          No providers configured. Please add API keys to .env file.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Provider
        </label>
        <select
          value={provider}
          onChange={(e) => {
            onProviderChange(e.target.value);
            // Auto-select first model of new provider
            const newProvider = providers.find(p => p.name === e.target.value);
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
              {p.display_name} {!p.has_api_key && '(No key)'}
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
          {availableModels.map((m) => (
            <option key={m.id} value={m.id}>
              {m.name}
            </option>
          ))}
        </select>
        {availableModels.length === 0 && (
          <p className="text-xs text-gray-500 mt-1">No models available</p>
        )}
      </div>
    </div>
  );
}
