import { Database, Users, HardDrive, Activity, TrendingUp, TrendingDown } from 'lucide-react';
import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import { useEffect } from 'react';
import clsx from 'clsx';

function AnimatedNumber({ value }: { value: string | number }) {
  if (typeof value === 'string') {
    return <span>{value}</span>;
  }
  
  const count = useMotionValue(0);
  const rounded = useTransform(count, (latest) => Math.round(latest).toLocaleString());

  useEffect(() => {
    const animation = animate(count, value, { duration: 1.5, ease: "easeOut" });
    return animation.stop;
  }, [value, count]);

  return <motion.span>{rounded}</motion.span>;
}

interface StatCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon: React.ElementType;
  trend?: {
    value: number;
    label: string;
  };
  color?: 'purple' | 'blue' | 'green' | 'amber';
  delay?: number;
}

function StatCard({ label, value, subtext, icon: Icon, trend, color = 'purple', delay = 0 }: StatCardProps) {
  const colorStyles = {
    purple: {
      iconBg: 'bg-purple-500/10 border border-purple-500/20',
      iconColor: 'text-purple-400',
      trendPositive: 'text-green-400',
      trendNegative: 'text-red-400',
      glow: 'from-purple-500/10 via-purple-500/5 to-transparent'
    },
    blue: {
      iconBg: 'bg-blue-500/10 border border-blue-500/20',
      iconColor: 'text-blue-400',
      trendPositive: 'text-green-400',
      trendNegative: 'text-red-400',
      glow: 'from-blue-500/10 via-blue-500/5 to-transparent'
    },
    green: {
      iconBg: 'bg-emerald-500/10 border border-emerald-500/20',
      iconColor: 'text-emerald-400',
      trendPositive: 'text-green-400',
      trendNegative: 'text-red-400',
      glow: 'from-emerald-500/10 via-emerald-500/5 to-transparent'
    },
    amber: {
      iconBg: 'bg-amber-500/10 border border-amber-500/20',
      iconColor: 'text-amber-400',
      trendPositive: 'text-green-400',
      trendNegative: 'text-red-400',
      glow: 'from-amber-500/10 via-amber-500/5 to-transparent'
    },
  };

  const styles = colorStyles[color];

  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: "easeOut" }}
      className={clsx(
        'group relative p-6 rounded-2xl overflow-hidden',
        'bg-white/[0.02] backdrop-blur-md border border-white/5',
        'hover:bg-white/[0.04] hover:shadow-xl hover:shadow-black/50 hover:border-white/10',
        'transition-all duration-300'
      )}
    >
      {/* Subtle glowing animated background gradient */}
      <div className={clsx(
        'absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-100 transition-opacity duration-500',
        styles.glow
      )} />
      
      <div className="relative flex items-start justify-between z-10">
        <div>
          <p className="text-[13px] font-medium text-gray-400 tracking-wide mb-1.5 uppercase">{label}</p>
          <p className="text-3xl font-bold text-white tracking-tight">
            <AnimatedNumber value={value} />
          </p>
          {subtext && (
            <p className="text-[13px] text-gray-500 font-medium mt-1">{subtext}</p>
          )}
          {trend && (
            <div className={clsx(
              'flex items-center gap-1.5 mt-3 text-xs font-semibold px-2 py-1 rounded-md bg-black/40 w-fit',
              trend.value >= 0 ? styles.trendPositive : styles.trendNegative
            )}>
              {trend.value >= 0 ? (
                <TrendingUp className="w-3.5 h-3.5" />
              ) : (
                <TrendingDown className="w-3.5 h-3.5" />
              )}
              <span>{trend.value >= 0 ? '+' : ''}{trend.value}%</span>
              <span className="text-gray-500 font-medium ml-0.5">{trend.label}</span>
            </div>
          )}
        </div>
        
        <div className={clsx('p-3 rounded-xl shadow-inner', styles.iconBg)}>
          <Icon className={clsx('w-6 h-6', styles.iconColor)} />
        </div>
      </div>
    </motion.div>
  );
}

interface StatsOverviewProps {
  memoryCount: number;
  entityCount: number;
  storageUsed: string;
  apiCalls: number;
  loading?: boolean;
}

export function StatsOverview({ 
  memoryCount, 
  entityCount, 
  storageUsed, 
  apiCalls,
  loading 
}: StatsOverviewProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-8">
        {[...Array(4)].map((_, i) => (
          <div 
            key={i}
            className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 animate-pulse h-36"
          >
            <div className="h-4 bg-white/5 rounded w-24 mb-4" />
            <div className="h-8 bg-white/10 rounded w-28 mb-3" />
            <div className="h-3 bg-white/5 rounded w-16" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-8">
      <StatCard
        label="Total Memories"
        value={memoryCount}
        icon={Database}
        trend={{ value: 12, label: 'this week' }}
        color="purple"
        delay={0.1}
      />
      <StatCard
        label="Entities Count"
        value={entityCount}
        subtext={`${Math.round(memoryCount / Math.max(entityCount, 1))} memories/entity avg`}
        icon={Users}
        color="blue"
        delay={0.2}
      />
      <StatCard
        label="Storage Used"
        value={storageUsed}
        subtext="of 500 MB capacity"
        icon={HardDrive}
        color="green"
        delay={0.3}
      />
      <StatCard
        label="API Operations"
        value={apiCalls}
        subtext="past 30 days"
        icon={Activity}
        trend={{ value: 8, label: 'vs last month' }}
        color="amber"
        delay={0.4}
      />
    </div>
  );
}
