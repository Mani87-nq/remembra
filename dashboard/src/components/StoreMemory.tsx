import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../lib/api';
import { Plus, Send, X, Clock, Loader2, Eye, Users, Lock, Check, Brain } from 'lucide-react';
import clsx from 'clsx';

interface StoreMemoryProps {
  onStored?: () => void;
  projectId?: string;
  startOpen?: boolean;
}

const TTL_OPTIONS = [
  { label: 'No expiry', value: '' },
  { label: '1 hour', value: '1h' },
  { label: '24 hours', value: '24h' },
  { label: '7 days', value: '7d' },
  { label: '30 days', value: '30d' },
  { label: '1 year', value: '1y' },
];

const VISIBILITY_OPTIONS = [
  { label: 'Personal', value: 'personal', icon: Lock, description: 'Only you can see this' },
  { label: 'Project', value: 'project', icon: Eye, description: 'Project members can see this' },
  { label: 'Team', value: 'team', icon: Users, description: 'All team members can see this' },
];

type Visibility = 'personal' | 'project' | 'team';

const overlayVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
};

const modalVariants = {
  hidden: {
    opacity: 0,
    scale: 0.96,
    y: 16,
    filter: 'blur(4px)',
  },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    filter: 'blur(0px)',
    transition: {
      duration: 0.25,
      ease: [0.22, 1, 0.36, 1] as [number, number, number, number],
    },
  },
  exit: {
    opacity: 0,
    scale: 0.98,
    y: -8,
    filter: 'blur(2px)',
    transition: { duration: 0.15, ease: [0.4, 0, 1, 1] as [number, number, number, number] },
  },
};

export function StoreMemory({ onStored, projectId, startOpen = false }: StoreMemoryProps) {
  const [isOpen, setIsOpen] = useState(startOpen);
  const [content, setContent] = useState('');
  const [ttl, setTtl] = useState('');
  const [visibility, setVisibility] = useState<Visibility>('personal');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-focus textarea when modal opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => textareaRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      await api.storeMemory(
        content.trim(),
        projectId,
        ttl || undefined,
        visibility,
      );
      setSuccess(true);
      setContent('');
      setTtl('');
      setVisibility('personal');
      setTimeout(() => {
        setSuccess(false);
        setIsOpen(false);
        onStored?.();
      }, 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to store memory');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (loading) return;
    setIsOpen(false);
    setContent('');
    setTtl('');
    setVisibility('personal');
    setError(null);
    setSuccess(false);
  };

  // Character count for feedback
  const charCount = content.length;
  const charColor = charCount === 0
    ? 'text-[hsl(var(--muted-foreground))]'
    : charCount < 20
      ? 'text-amber-400'
      : 'text-emerald-400';

  if (!isOpen) {
    return (
      <motion.button
        onClick={() => setIsOpen(true)}
        whileHover={{ scale: 1.04, y: -2 }}
        whileTap={{ scale: 0.96 }}
        className="fixed bottom-6 right-6 p-4 rounded-2xl btn-primary flex items-center gap-2 z-40"
      >
        <Plus className="w-5 h-5" />
        <span className="font-medium text-sm">Add Memory</span>
      </motion.button>
    );
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop"
          variants={overlayVariants}
          initial="hidden"
          animate="visible"
          exit="hidden"
          transition={{ duration: 0.2 }}
          onClick={handleClose}
        >
          <motion.div
            className="w-full max-w-lg modal-surface rounded-2xl overflow-hidden"
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-[hsl(var(--border)/0.5)]">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-[hsl(var(--primary)/0.12)] border border-[hsl(var(--primary)/0.2)]">
                  <Brain className="w-4 h-4 text-[hsl(var(--primary))]" />
                </div>
                <div>
                  <h2 className="text-base font-semibold text-[hsl(var(--foreground))]">
                    Store New Memory
                  </h2>
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">
                    Facts are extracted and indexed automatically
                  </p>
                </div>
              </div>
              <button
                onClick={handleClose}
                className="p-2 rounded-xl text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--muted)/0.6)] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="p-6 space-y-5">
              {/* Content */}
              <div>
                <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
                  Memory Content
                </label>
                <textarea
                  ref={textareaRef}
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Enter information to remember..."
                  rows={5}
                  className="w-full px-4 py-3 rounded-xl input-premium resize-none text-sm leading-relaxed"
                  disabled={loading}
                />
                <div className="flex items-center justify-between mt-1.5">
                  <p className="text-[11px] text-[hsl(var(--muted-foreground))]">
                    Tip: Be specific — facts are extracted per sentence
                  </p>
                  <span className={clsx('text-[11px] font-medium tabular-nums', charColor)}>
                    {charCount} chars
                  </span>
                </div>
              </div>

              {/* Visibility Selector */}
              <div>
                <label className="flex items-center gap-1.5 text-sm font-medium text-[hsl(var(--foreground))] mb-2">
                  <Eye className="w-3.5 h-3.5 text-[hsl(var(--muted-foreground))]" />
                  Visibility
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {VISIBILITY_OPTIONS.map((opt) => {
                    const Icon = opt.icon;
                    const isSelected = visibility === opt.value;
                    return (
                      <motion.button
                        key={opt.value}
                        type="button"
                        onClick={() => setVisibility(opt.value as Visibility)}
                        disabled={loading}
                        whileTap={{ scale: 0.96 }}
                        className={clsx(
                          'flex flex-col items-center p-3 rounded-xl border transition-all duration-150',
                          isSelected
                            ? 'border-[hsl(var(--primary)/0.5)] bg-[hsl(var(--primary)/0.08)] text-[hsl(var(--primary))] shadow-[0_0_12px_hsl(var(--primary)/0.08)]'
                            : 'border-[hsl(var(--border)/0.6)] bg-[hsl(var(--card)/0.5)] text-[hsl(var(--muted-foreground))] hover:border-[hsl(var(--primary)/0.3)] hover:text-[hsl(var(--foreground))]'
                        )}
                      >
                        <Icon className="w-4 h-4 mb-1" />
                        <span className="text-xs font-medium">{opt.label}</span>
                      </motion.button>
                    );
                  })}
                </div>
                <p className="mt-1.5 text-[11px] text-[hsl(var(--muted-foreground))]">
                  {VISIBILITY_OPTIONS.find(o => o.value === visibility)?.description}
                </p>
              </div>

              {/* TTL Selector */}
              <div>
                <label className="flex items-center gap-1.5 text-sm font-medium text-[hsl(var(--foreground))] mb-2">
                  <Clock className="w-3.5 h-3.5 text-[hsl(var(--muted-foreground))]" />
                  Time to Live
                </label>
                <select
                  value={ttl}
                  onChange={(e) => setTtl(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl input-premium text-sm"
                  disabled={loading}
                >
                  {TTL_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Error */}
              <AnimatePresence>
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -4, height: 0 }}
                    animate={{ opacity: 1, y: 0, height: 'auto' }}
                    exit={{ opacity: 0, y: -4, height: 0 }}
                    className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm"
                  >
                    {error}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Success */}
              <AnimatePresence>
                {success && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="flex items-center gap-2 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm"
                  >
                    <Check className="w-4 h-4" />
                    Memory stored and indexed
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-1">
                <button
                  type="button"
                  onClick={handleClose}
                  className="px-4 py-2.5 rounded-xl btn-ghost text-sm font-medium"
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || !content.trim()}
                  className={clsx(
                    'px-5 py-2.5 rounded-xl btn-primary text-sm',
                    'flex items-center gap-2',
                  )}
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Storing...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      Store Memory
                    </>
                  )}
                </button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
