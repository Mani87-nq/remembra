import { useState, useEffect, useRef } from 'react';
import { Search, X, Loader2, Sparkles } from 'lucide-react';
import clsx from 'clsx';

interface SearchBarProps {
  onSearch: (query: string) => void;
  onClear: () => void;
  loading?: boolean;
  placeholder?: string;
  debounceMs?: number;
}

export function SearchBar({
  onSearch,
  onClear,
  loading = false,
  placeholder = 'Search memories semantically...',
  debounceMs = 500,
}: SearchBarProps) {
  const [value, setValue] = useState('');
  const [focused, setFocused] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    if (value.trim()) {
      debounceRef.current = setTimeout(() => {
        onSearch(value.trim());
      }, debounceMs);
    }

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [value, debounceMs, onSearch]);

  const handleClear = () => {
    setValue('');
    onClear();
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && value.trim()) {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
      onSearch(value.trim());
    }
    if (e.key === 'Escape') {
      handleClear();
    }
  };

  return (
    <div className="relative group">
      {/* Focus glow ring */}
      <div
        className={clsx(
          'absolute -inset-[1px] rounded-xl transition-opacity duration-200 pointer-events-none',
          'bg-gradient-to-r from-[hsl(var(--primary)/0.2)] via-[hsl(var(--shell-glow)/0.15)] to-[hsl(var(--primary)/0.2)]',
          'blur-sm',
          focused ? 'opacity-100' : 'opacity-0'
        )}
      />

      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none z-10">
          {loading ? (
            <Loader2 className="w-4 h-4 text-[hsl(var(--primary))] animate-spin" />
          ) : focused || value ? (
            <Sparkles className="w-4 h-4 text-[hsl(var(--primary))]" />
          ) : (
            <Search className="w-4 h-4 text-[hsl(var(--muted-foreground))]" />
          )}
        </div>

        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder={placeholder}
          className={clsx(
            'w-full pl-11 pr-10 py-3 rounded-xl text-sm',
            'input-premium'
          )}
        />

        {value && (
          <button
            onClick={handleClear}
            className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] transition-colors z-10"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}
