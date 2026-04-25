import { useEffect, useState, useRef, useCallback } from 'react';
import { api } from '../lib/api';
import type { TimelineMemory } from '../lib/api';
import { Clock, Eye, Tag, Loader2, Calendar } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';

const entityColors: Record<string, string> = {
  person: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  company: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  organization: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  location: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  concept: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
};

interface MemoryTimelineProps {
  projectId?: string;
}

export function MemoryTimeline({ projectId }: MemoryTimelineProps) {
  const [memories, setMemories] = useState<TimelineMemory[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const observer = useRef<IntersectionObserver | null>(null);
  
  const lastMemoryElementRef = useCallback((node: HTMLDivElement | null) => {
    if (loading || loadingMore) return;
    if (observer.current) observer.current.disconnect();
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && memories.length < total) {
        setPage(prev => prev + 1);
      }
    });
    if (node) observer.current.observe(node);
  }, [loading, loadingMore, memories.length, total]);

  useEffect(() => {
    loadTimeline(page === 1);
  }, [page, projectId]);

  useEffect(() => {
    setPage(1);
    setMemories([]);
    setTotal(0);
  }, [projectId]);

  const loadTimeline = async (isInitial = false) => {
    if (isInitial) setLoading(true);
    else setLoadingMore(true);
    setError(null);
    try {
      const result = await api.getMemoryTimeline(page, 20, projectId);
      if (isInitial) {
        setMemories(result.memories);
      } else {
        setMemories(prev => [...prev, ...result.memories]);
      }
      setTotal(result.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load timeline');
    } finally {
      if (isInitial) setLoading(false);
      else setLoadingMore(false);
    }
  };

  const formatDateLabel = (iso: string) => {
    const d = new Date(iso.endsWith('Z') ? iso : iso + 'Z');
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const days = Math.floor(diff / 86400000);

    if (days < 0) return 'Just now';
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const formatTime = (iso: string) => {
    return new Date(iso.endsWith('Z') ? iso : iso + 'Z').toLocaleTimeString('en-US', { 
      hour: '2-digit', minute: '2-digit'
    });
  };

  if (error && memories.length === 0) {
    return (
      <div className="p-4 flex items-center gap-3 rounded-xl bg-red-900/10 border border-red-500/20 text-red-400 text-sm font-medium">
        <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
        {error}
      </div>
    );
  }

  // Group by date
  const grouped: Record<string, TimelineMemory[]> = {};
  memories.forEach(mem => {
    const dateKey = formatDateLabel(mem.created_at);
    if (!grouped[dateKey]) grouped[dateKey] = [];
    grouped[dateKey].push(mem);
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-white/5">
        <h3 className="text-sm font-medium tracking-tight text-gray-400 flex items-center gap-2">
          <Calendar className="w-4 h-4 text-purple-400 opacity-80" />
          {total > 0 ? `${total.toLocaleString()} memories tracking timeline` : 'Loading index...'}
        </h3>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
        </div>
      ) : (
        <div className="relative pl-6 pb-12">
          {/* Subtle glowing timeline backbone */}
          <div className="absolute left-1.5 top-2 bottom-0 w-px bg-gradient-to-b from-purple-500/50 via-gray-700/30 to-transparent" />

          {Object.entries(grouped).map(([dateLabel, dateMemories], groupIndex) => (
            <div key={dateLabel} className="mb-10 relative">
              {/* Sticky Date Header */}
              <div className="sticky top-0 z-10 py-3 bg-black/80 backdrop-blur-xl mb-4 -ml-6 pl-6 flex items-center shadow-sm">
                <div className="absolute left-[-4.5px] w-2.5 h-2.5 rounded-full bg-black border-2 border-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.6)]" />
                <span className="text-sm font-semibold tracking-wide text-white">{dateLabel}</span>
              </div>

              <div className="space-y-4">
                <AnimatePresence>
                  {dateMemories.map((mem, index) => {
                    const isLast = groupIndex === Object.keys(grouped).length - 1 && index === dateMemories.length - 1;
                    return (
                      <motion.div
                        ref={isLast ? lastMemoryElementRef : null}
                        key={mem.id}
                        initial={{ opacity: 0, y: 15 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3, delay: index * 0.05, ease: 'easeOut' }}
                        className="group relative p-5 rounded-xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] hover:shadow-lg hover:shadow-purple-500/5 hover:border-purple-500/20 transition-all duration-300"
                      >
                        {/* Hover accent bar */}
                        <div className="absolute left-0 top-4 bottom-4 w-1 bg-purple-500 rounded-r opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                        
                        <p className="text-sm text-gray-300 leading-relaxed mb-4">{mem.content}</p>

                        <div className="flex items-center gap-2.5 flex-wrap">
                          <span className="flex items-center gap-1.5 text-[11px] font-medium text-gray-500 px-2 py-1 rounded-md bg-black/40 border border-white/5">
                            <Clock className="w-3 h-3 text-purple-400/80" />
                            {formatTime(mem.created_at)}
                          </span>

                          {mem.access_count > 0 && (
                            <span className="flex items-center gap-1.5 text-[11px] font-medium text-gray-500 px-2 py-1 rounded-md bg-black/40 border border-white/5">
                              <Eye className="w-3 h-3 text-blue-400/80" />
                              {mem.access_count}
                            </span>
                          )}

                          {mem.entities.map((entity, i) => (
                            <span
                              key={i}
                              className={clsx(
                                'inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-[10px] uppercase tracking-wider font-semibold shadow-sm border',
                                entityColors[entity.type] || 'bg-white/5 text-gray-400 border-white/10'
                              )}
                            >
                              <Tag className="w-2.5 h-2.5 opacity-70" />
                              {entity.name}
                            </span>
                          ))}
                        </div>
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
              </div>
            </div>
          ))}
          
          {loadingMore && (
            <div className="py-6 flex justify-center">
              <Loader2 className="w-5 h-5 animate-spin text-purple-500/50" />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
