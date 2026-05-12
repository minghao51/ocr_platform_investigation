import { useEffect, useRef } from 'react';
import { useProviders, getDefaultProvider } from '../hooks/useProviders';
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
  const { providers, loading, error, retry } = useProviders();
  const didAutoSelect = useRef(false);

  useEffect(() => {
    if (didAutoSelect.current || providers.length === 0) return;
    const defaults = getDefaultProvider(providers);
    if (defaults && !provider) {
      didAutoSelect.current = true;
      onProviderChange(defaults.provider);
      if (!model) onModelChange(defaults.model);
    }
  }, [providers, provider, model, onProviderChange, onModelChange]);

  const selectedProvider = providers.find((p) => p.name === provider);
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
        <button onClick={retry} className="mt-2 text-sm text-red-700 underline">
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
