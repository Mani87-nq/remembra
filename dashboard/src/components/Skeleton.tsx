/**
 * Premium skeleton loading components for Remembra Dashboard
 * Inspired by Linear's loading states — content-shaped placeholders
 * that match the actual layout for zero-shift transitions.
 */

import clsx from 'clsx';

// ─── Base Skeleton Pulse ────────────────────────────────────────
interface SkeletonProps {
  className?: string;
  style?: React.CSSProperties;
}

export function Skeleton({ className, style }: SkeletonProps) {
  return (
    <div
      style={style}
      className={clsx(
        'rounded-lg bg-[hsl(var(--muted))]',
        'animate-pulse',
        className
      )}
    />
  );
}

// ─── Stat Card Skeleton ─────────────────────────────────────────
export function StatCardSkeleton() {
  return (
    <div className="p-5 rounded-xl bg-[hsl(var(--card))] border border-[hsl(var(--border))]">
      <div className="flex items-start justify-between">
        <div className="space-y-3 flex-1">
          <Skeleton className="h-3.5 w-20" />
          <Skeleton className="h-8 w-28" />
          <Skeleton className="h-3 w-16" />
        </div>
        <Skeleton className="w-10 h-10 rounded-lg flex-shrink-0" />
      </div>
    </div>
  );
}

// ─── Memory Card Skeleton ───────────────────────────────────────
export function MemoryCardSkeleton() {
  return (
    <div className="p-4 rounded-xl bg-[hsl(var(--card))] border border-[hsl(var(--border))]">
      <div className="flex items-start gap-3">
        {/* Left indicator bar */}
        <Skeleton className="w-0.5 h-16 rounded-full flex-shrink-0" />

        <div className="flex-1 space-y-3">
          {/* Content lines */}
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-4/5" />
          <Skeleton className="h-4 w-3/5" />

          {/* Entity tags */}
          <div className="flex gap-2 pt-1">
            <Skeleton className="h-5 w-16 rounded-full" />
            <Skeleton className="h-5 w-20 rounded-full" />
            <Skeleton className="h-5 w-14 rounded-full" />
          </div>

          {/* Footer: date + type */}
          <div className="flex items-center justify-between pt-1">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-3 w-12" />
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Memory List Skeleton ───────────────────────────────────────
export function MemoryListSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <MemoryCardSkeleton key={i} />
      ))}
    </div>
  );
}

// ─── Stats Grid Skeleton ────────────────────────────────────────
export function StatsGridSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {Array.from({ length: 4 }).map((_, i) => (
        <StatCardSkeleton key={i} />
      ))}
    </div>
  );
}

// ─── Entity List Skeleton ───────────────────────────────────────
export function EntityListSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-3 p-3 rounded-lg bg-[hsl(var(--card))] border border-[hsl(var(--border))]"
        >
          <Skeleton className="w-8 h-8 rounded-full flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3 w-20" />
          </div>
          <Skeleton className="h-5 w-12 rounded-full" />
        </div>
      ))}
    </div>
  );
}

// ─── Graph Skeleton ─────────────────────────────────────────────
export function GraphSkeleton() {
  return (
    <div className="relative w-full h-[500px] rounded-xl bg-[hsl(var(--card))] border border-[hsl(var(--border))] overflow-hidden">
      {/* Fake nodes */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="relative w-64 h-64">
          {[
            { x: '50%', y: '10%', size: 12 },
            { x: '80%', y: '35%', size: 10 },
            { x: '70%', y: '75%', size: 14 },
            { x: '30%', y: '80%', size: 8 },
            { x: '15%', y: '45%', size: 11 },
            { x: '50%', y: '50%', size: 16 },
          ].map((node, i) => (
            <div
              key={i}
              className="absolute rounded-full bg-[hsl(var(--muted))] animate-pulse"
              style={{
                left: node.x,
                top: node.y,
                width: node.size * 2,
                height: node.size * 2,
                transform: 'translate(-50%, -50%)',
                animationDelay: `${i * 200}ms`,
              }}
            />
          ))}
        </div>
      </div>

      {/* Loading text */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2">
        <Skeleton className="h-4 w-32" />
      </div>
    </div>
  );
}

// ─── Timeline Skeleton ──────────────────────────────────────────
export function TimelineSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="relative pl-8">
      {/* Vertical line */}
      <div className="absolute left-3 top-0 bottom-0 w-px bg-[hsl(var(--border))]" />

      <div className="space-y-6">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="relative flex gap-4">
            {/* Dot */}
            <div className="absolute -left-8 w-6 h-6 rounded-full bg-[hsl(var(--muted))] animate-pulse border-2 border-[hsl(var(--background))]"
              style={{ animationDelay: `${i * 150}ms` }}
            />

            {/* Content */}
            <div className="flex-1 p-4 rounded-xl bg-[hsl(var(--card))] border border-[hsl(var(--border))]">
              <Skeleton className="h-3 w-20 mb-2" />
              <Skeleton className="h-4 w-full mb-1" />
              <Skeleton className="h-4 w-3/4" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Analytics Chart Skeleton ───────────────────────────────────
export function ChartSkeleton() {
  return (
    <div className="p-6 rounded-xl bg-[hsl(var(--card))] border border-[hsl(var(--border))]">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-8 w-24 rounded-lg" />
      </div>

      {/* Chart bars */}
      <div className="flex items-end gap-2 h-40">
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i} className="flex-1 flex flex-col justify-end">
            <Skeleton
              className="w-full rounded-t"
              style={{
                height: `${20 + Math.random() * 80}%`,
                animationDelay: `${i * 80}ms`,
              }}
            />
          </div>
        ))}
      </div>

      {/* X-axis labels */}
      <div className="flex gap-2 mt-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="flex-1 h-3" />
        ))}
      </div>
    </div>
  );
}
