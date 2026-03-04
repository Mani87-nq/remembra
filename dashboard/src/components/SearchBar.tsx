import { useState, useEffect, useRef } from 'react';
import { Search, X, Loader2 } from 'lucide-react';
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
    <div className="relative">
      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
        {loading ? (
          <Loader2 className="w-5 h-5 text-[#8B5CF6] animate-spin" />
        ) : (
          <Search className="w-5 h-5 text-gray-400" />
        )}
      </div>
      
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className={clsx(
          'w-full pl-12 pr-10 py-3 rounded-lg',
          'bg-white dark:bg-gray-800',
          'border border-gray-200 dark:border-gray-700',
          'text-gray-900 dark:text-gray-100 placeholder-gray-400',
          'focus:outline-none focus:ring-2 focus:ring-[#8B5CF6] focus:border-transparent',
          'transition-all duration-200'
        )}
      />

      {value && (
        <button
          onClick={handleClear}
          className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        >
          <X className="w-5 h-5" />
        </button>
      )}
    </div>
  );
}
