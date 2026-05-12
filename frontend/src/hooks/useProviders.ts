import { useState, useEffect } from 'react';
import { listProviders, getBenchmarkedModels } from '@/lib/api';
import type { Provider, BenchmarkedModel } from '@/lib/api';

interface UseProvidersResult {
  providers: Provider[];
  benchmarkedModels: BenchmarkedModel[];
  loading: boolean;
  error: string | null;
  retry: () => void;
}

export function useProviders(): UseProvidersResult {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [benchmarkedModels, setBenchmarkedModels] = useState<BenchmarkedModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listProviders();

      const sorted = data.sort((a, b) => {
        if (a.is_default && !b.is_default) return -1;
        if (!a.is_default && b.is_default) return 1;
        if (a.has_api_key && !b.has_api_key) return -1;
        if (!a.has_api_key && b.has_api_key) return 1;
        return 0;
      });

      setProviders(sorted);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load providers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    getBenchmarkedModels().then(setBenchmarkedModels).catch(() => {});
  }, []);

  return { providers, benchmarkedModels, loading, error, retry: load };
}

export function getDefaultProvider(providers: Provider[]): { provider: string; model: string } | null {
  const best = providers.find((p) => p.is_default && p.has_api_key)
    || providers.find((p) => p.has_api_key && p.models.length > 0);
  if (!best) return null;
  return {
    provider: best.name,
    model: best.models[0]?.id || '',
  };
}
