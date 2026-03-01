import { useState } from 'react';
import { useMemories, useSearch } from '../hooks/useMemories';
import { SearchBar } from '../components/SearchBar';
import { MemoryList } from '../components/MemoryList';
import { MemoryDetail } from './MemoryDetail';
import type { Memory } from '../lib/api';
import { RefreshCw } from 'lucide-react';
import clsx from 'clsx';

export function Dashboard() {
  const { memories, loading, error, hasMore, refresh, loadMore } = useMemories();
  const { results, loading: searchLoading, error: searchError, search, clear } = useSearch();
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = (query: string) => {
    setIsSearching(true);
    search(query);
  };

  const handleClearSearch = () => {
    setIsSearching(false);
    clear();
  };

  const handleSelectMemory = (memory: Memory) => {
    setSelectedMemory(memory);
  };

  const handleCloseDetail = () => {
    setSelectedMemory(null);
  };

  // If a memory is selected, show the detail view
  if (selectedMemory) {
    return (
      <MemoryDetail
        memory={selectedMemory}
        onClose={handleCloseDetail}
        onDelete={() => {
          handleCloseDetail();
          refresh();
        }}
      />
    );
  }

  const displayMemories = isSearching && results ? results.memories : memories;
  const displayLoading = isSearching ? searchLoading : loading;
  const displayError = isSearching ? searchError : error;

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Search */}
      <div className="mb-6">
        <SearchBar
          onSearch={handleSearch}
          onClear={handleClearSearch}
          loading={searchLoading}
        />
      </div>

      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          {isSearching && results ? (
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {results.memories.length} result{results.memories.length !== 1 ? 's' : ''} for "{results.query}"
            </h2>
          ) : (
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              All Memories
              {memories.length > 0 && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  ({memories.length}{hasMore ? '+' : ''})
                </span>
              )}
            </h2>
          )}
        </div>

        {!isSearching && (
          <button
            onClick={refresh}
            disabled={loading}
            className={clsx(
              'p-2 rounded-lg text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200',
              'hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors',
              loading && 'opacity-50 cursor-not-allowed'
            )}
            title="Refresh"
          >
            <RefreshCw className={clsx('w-5 h-5', loading && 'animate-spin')} />
          </button>
        )}
      </div>

      {/* Context (for search results) */}
      {isSearching && results?.context && (
        <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-100 dark:border-blue-800">
          <h3 className="text-sm font-medium text-blue-800 dark:text-blue-300 mb-2">
            Context Summary
          </h3>
          <p className="text-sm text-blue-700 dark:text-blue-400 whitespace-pre-wrap">
            {results.context}
          </p>
        </div>
      )}

      {/* Memory List */}
      <MemoryList
        memories={displayMemories}
        loading={displayLoading}
        error={displayError}
        hasMore={!isSearching && hasMore}
        onLoadMore={!isSearching ? loadMore : undefined}
        onSelectMemory={handleSelectMemory}
        showRelevance={isSearching}
        emptyMessage={isSearching ? 'No memories match your search' : 'No memories yet. Start by storing some!'}
      />
    </div>
  );
}
