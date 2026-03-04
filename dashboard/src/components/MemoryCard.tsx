import { Calendar, User, Tag, Brain, ChevronRight } from 'lucide-react';
import type { Memory } from '../lib/api';
import clsx from 'clsx';

interface MemoryCardProps {
  memory: Memory;
  onClick?: () => void;
  showRelevance?: boolean;
}

export function MemoryCard({ memory, onClick, showRelevance = false }: MemoryCardProps) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const truncateContent = (content: string, maxLength = 150) => {
    if (content.length <= maxLength) return content;
    return content.slice(0, maxLength).trim() + '...';
  };

  const relevanceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/30';
    if (score >= 0.6) return 'text-[#8B5CF6] dark:text-[#A78BFA] bg-blue-100 dark:bg-blue-900/30';
    if (score >= 0.4) return 'text-yellow-600 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-900/30';
    return 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800';
  };

  return (
    <div
      onClick={onClick}
      className={clsx(
        'bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700',
        'p-4 transition-all duration-200',
        onClick && 'cursor-pointer hover:border-blue-300 dark:hover:border-[#8B5CF6] hover:shadow-md'
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-gray-900 dark:text-gray-100 leading-relaxed">
            {truncateContent(memory.content)}
          </p>
        </div>
        
        <div className="flex items-center gap-2 flex-shrink-0">
          {showRelevance && memory.relevance !== undefined && (
            <span className={clsx(
              'px-2 py-0.5 rounded text-xs font-medium',
              relevanceColor(memory.relevance)
            )}>
              {(memory.relevance * 100).toFixed(0)}%
            </span>
          )}
          {onClick && (
            <ChevronRight className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </div>

      {/* Metadata */}
      <div className="flex flex-wrap items-center gap-4 mt-3 text-sm text-gray-500 dark:text-gray-400">
        <div className="flex items-center gap-1.5">
          <Calendar className="w-4 h-4" />
          <span>{formatDate(memory.created_at)}</span>
        </div>

        {memory.entities && memory.entities.length > 0 && (
          <div className="flex items-center gap-1.5">
            <User className="w-4 h-4" />
            <span className="truncate max-w-[200px]">
              {memory.entities.slice(0, 3).join(', ')}
              {memory.entities.length > 3 && ` +${memory.entities.length - 3}`}
            </span>
          </div>
        )}

        {memory.memory_type && (
          <div className="flex items-center gap-1.5">
            <Tag className="w-4 h-4" />
            <span>{memory.memory_type}</span>
          </div>
        )}

        {memory.access_count !== undefined && memory.access_count > 0 && (
          <div className="flex items-center gap-1.5">
            <Brain className="w-4 h-4" />
            <span>{memory.access_count} recalls</span>
          </div>
        )}
      </div>
    </div>
  );
}
