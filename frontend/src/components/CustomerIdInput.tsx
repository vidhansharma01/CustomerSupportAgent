import { useState, type FormEvent, type KeyboardEvent } from 'react';

interface CustomerIdInputProps {
  onCustomerIdChange: (id: string | undefined) => void;
  currentCustomerId?: string;
}

export function CustomerIdInput({ onCustomerIdChange, currentCustomerId }: CustomerIdInputProps) {
  const [inputValue, setInputValue] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  const handleSet = (e?: FormEvent) => {
    e?.preventDefault();
    const trimmed = inputValue.trim();
    if (trimmed) {
      onCustomerIdChange(trimmed);
      setInputValue('');
      setIsEditing(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSet();
    if (e.key === 'Escape') {
      setIsEditing(false);
      setInputValue('');
    }
  };

  const handleClear = () => {
    onCustomerIdChange(undefined);
  };

  return (
    <div className="flex items-center gap-2 flex-shrink-0">
      {/* Current customer ID tag */}
      {currentCustomerId && !isEditing && (
        <div className="flex items-center gap-1 bg-indigo-50 border border-indigo-200 rounded-full px-2.5 py-1">
          <span className="text-xs text-indigo-700 font-medium">
            👤 {currentCustomerId}
          </span>
          <button
            onClick={handleClear}
            className="text-indigo-400 hover:text-indigo-600 text-sm leading-none ml-0.5"
            aria-label="Clear customer ID"
          >
            ×
          </button>
        </div>
      )}

      {/* Edit/Add button or inline form */}
      {!isEditing ? (
        <button
          onClick={() => setIsEditing(true)}
          className="text-xs text-gray-500 hover:text-indigo-600 transition-colors border border-gray-300 hover:border-indigo-300 rounded-full px-2.5 py-1 bg-white"
          title={currentCustomerId ? 'Change Customer ID' : 'Set Customer ID'}
        >
          {currentCustomerId ? '✏️ Change' : '+ Customer ID'}
        </button>
      ) : (
        <form onSubmit={handleSet} className="flex items-center gap-1">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Customer ID…"
            autoFocus
            className="text-xs border border-gray-300 rounded-full px-2.5 py-1 outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-100 w-28"
          />
          <button
            type="submit"
            disabled={!inputValue.trim()}
            className="text-xs bg-indigo-600 text-white rounded-full px-2.5 py-1 hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            Set
          </button>
          <button
            type="button"
            onClick={() => { setIsEditing(false); setInputValue(''); }}
            className="text-xs text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </form>
      )}
    </div>
  );
}
