import { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';
import type { Memory, RecallResult } from '../lib/api';

export function useMemories(limit = 20, projectId?: string) {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const fetchMemories = useCallback(async (pageOffset: number, reset = false) => {
    try {
      setLoading(true);
      setError(null);
      const result = await api.listMemories({ limit, offset: pageOffset, project_id: projectId });
      
      if (reset) {
        setMemories(result);
        setOffset(result.length);
      } else {
        setMemories(prev => [...prev, ...result]);
        setOffset(prev => prev + result.length);
      }
      
      setHasMore(result.length === limit);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch memories');
    } finally {
      setLoading(false);
    }
  }, [limit, projectId]);

  const refresh = useCallback(() => {
    setMemories([]);
    setOffset(0);
    setHasMore(true);
    fetchMemories(0, true);
  }, [fetchMemories]);

  const loadMore = useCallback(() => {
    if (!loading && hasMore) {
      fetchMemories(offset, false);
    }
  }, [fetchMemories, hasMore, loading, offset]);

  useEffect(() => {
    if (api.isAuthenticated()) {
      setMemories([]);
      setOffset(0);
      setHasMore(true);
      void fetchMemories(0, true);
    }
  }, [fetchMemories]);

  return { memories, loading, error, hasMore, refresh, loadMore };
}

export function useSearch(projectId?: string) {
  const [results, setResults] = useState<RecallResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async (query: string) => {
    if (!query.trim()) {
      setResults(null);
      setError(null);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const result = await api.recallMemories({ query, limit: 10, project_id: projectId });
      setResults(result);
    } catch (err) {
      // Handle different error types
      if (err instanceof Error) {
        setError(err.message);
      } else if (typeof err === 'object' && err !== null) {
        setError(JSON.stringify(err));
      } else {
        setError('Search failed');
      }
      setResults(null);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  const clear = useCallback(() => {
    setResults(null);
    setError(null);
  }, []);

  return { results, loading, error, search, clear };
}

export function useMemory(id: string | null) {
  const [memory, setMemory] = useState<Memory | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      setMemory(null);
      return;
    }

    const fetchMemory = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await api.getMemory(id);
        setMemory(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch memory');
      } finally {
        setLoading(false);
      }
    };

    fetchMemory();
  }, [id]);

  return { memory, loading, error };
}
