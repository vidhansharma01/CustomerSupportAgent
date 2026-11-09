import type { Message } from '../types';
import { SourcesList } from './SourcesList';
import { EscalationBanner } from './EscalationBanner';

interface MessageBubbleProps {
  message: Message;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end px-4 py-1">
        <div className="max-w-[75%] flex flex-col items-end gap-1">
          <div className="bg-indigo-600 text-white px-4 py-2.5 rounded-2xl rounded-tr-sm shadow-sm">
            <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
              {message.content}
            </p>
          </div>
          <span className="text-xs text-gray-400 px-1">
            {formatTime(message.timestamp)}
          </span>
        </div>
      </div>
    );
  }

  // Assistant (or tool) message
  return (
    <div className="flex items-start gap-3 px-4 py-1">
      {/* Bot avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center mt-1">
        <span className="text-indigo-600 text-sm">🤖</span>
      </div>

      <div className="max-w-[75%] flex flex-col gap-1">
        <div className="bg-white border border-gray-200 text-gray-800 px-4 py-2.5 rounded-2xl rounded-tl-sm shadow-sm">
          <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
            {message.content}
          </p>

          {/* Sources */}
          {message.sources && message.sources.length > 0 && (
            <SourcesList sources={message.sources} />
          )}

          {/* Escalation banner */}
          {message.escalated && message.ticketId && (
            <EscalationBanner ticketId={message.ticketId} />
          )}
        </div>

        <span className="text-xs text-gray-400 px-1">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
}
