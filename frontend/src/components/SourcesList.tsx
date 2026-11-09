import { useState } from 'react';
import type { SourceDoc } from '../types';

interface SourcesListProps {
  sources: SourceDoc[];
}

export function SourcesList({ sources }: SourcesListProps) {
  const [expanded, setExpanded] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3 border-t border-gray-100 pt-2">
      <button
        onClick={() => setExpanded((prev) => !prev)}
        className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-700 transition-colors font-medium"
        aria-expanded={expanded}
      >
        <span className={`transform transition-transform ${expanded ? 'rotate-90' : 'rotate-0'}`}>
          ▶
        </span>
        {sources.length} Source{sources.length !== 1 ? 's' : ''}
      </button>

      {expanded && (
        <div className="mt-2 flex flex-col gap-1.5">
          {sources.map((source, index) => (
            <div
              key={index}
              className="flex items-center gap-2 flex-wrap"
            >
              {/* Category chip */}
              <span className="inline-flex items-center rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700 border border-indigo-100">
                {source.category}
              </span>

              {/* Title */}
              <span className="text-xs text-gray-600 flex-1 min-w-0 truncate">
                {source.title}
              </span>

              {/* Relevance score */}
              <span className="text-xs text-gray-400 flex-shrink-0">
                {Math.round(source.relevance * 100)}% match
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
