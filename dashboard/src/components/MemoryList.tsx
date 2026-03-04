import type { Memory } from '../lib/api';
import { MemoryCard } from './MemoryCard';
import { Loader2, Brain } from 'lucide-react';

interface MemoryListProps {
  memories: Memory[];
  loading: boolean;
  error: string | null;
  hasMore?: boolean;
  onLoadMore?: () => void;
  onSelectMemory?: (memory: Memory) => void;
  showRelevance?: boolean;
  emptyMessage?: string;
}

export function MemoryList({
  memories,
  loading,
  error,
  hasMore = false,
  onLoadMore,
  onSelectMemory,
  showRelevance = false,
  emptyMessage = 'No memories found',
}: MemoryListProps) {
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-3">
          <span className="text-red-600 dark:text-red-400 text-xl">!</span>
        </div>
        <p className="text-red-600 dark:text-red-400 font-medium">{error}</p>
      </div>
    );
  }

  if (!loading && memories.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center">
        <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
          <Brain className="w-8 h-8 text-gray-400" />
        </div>
        <p className="text-gray-500 dark:text-gray-400">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {memories.map((memory) => (
        <MemoryCard
          key={memory.id}
          memory={memory}
          onClick={onSelectMemory ? () => onSelectMemory(memory) : undefined}
          showRelevance={showRelevance}
        />
      ))}

      {loading && (
        <div className="flex justify-center p-6">
          <Loader2 className="w-6 h-6 text-[#8B5CF6] animate-spin" />
        </div>
      )}

      {!loading && hasMore && onLoadMore && (
        <button
          onClick={onLoadMore}
          className="w-full py-3 text-sm font-medium text-[#8B5CF6] dark:text-[#A78BFA] hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
        >
          Load more
        </button>
      )}
    </div>
  );
}
