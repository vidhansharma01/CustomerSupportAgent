import { useEffect, useRef, useState } from 'react';
import { useChat } from '../hooks/useChat';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import { ChatInput } from './ChatInput';
import { CustomerIdInput } from './CustomerIdInput';

export function ChatWindow() {
  const [customerId, setCustomerId] = useState<string | undefined>(undefined);
  const { messages, isLoading, sendMessage, clearChat, conversationId } = useChat(customerId);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom whenever messages change or loading state changes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex flex-col h-full bg-white rounded-2xl shadow-2xl overflow-hidden border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 px-4 py-3 bg-white border-b border-gray-200">
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex-shrink-0 w-9 h-9 rounded-full bg-indigo-600 flex items-center justify-center shadow-sm">
            <span className="text-white text-lg">🤖</span>
          </div>
          <div className="min-w-0">
            <h1 className="text-base font-semibold text-gray-900 leading-tight truncate">
              Customer Support
            </h1>
            <p className="text-xs text-gray-500 leading-tight truncate">
              ID: <span className="font-mono text-gray-400">{conversationId.slice(0, 8)}…</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <CustomerIdInput
            onCustomerIdChange={setCustomerId}
            currentCustomerId={customerId}
          />

          {/* Clear chat button */}
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="text-xs text-gray-400 hover:text-red-500 transition-colors border border-gray-200 hover:border-red-200 rounded-full px-2.5 py-1 bg-white"
              title="Clear conversation"
            >
              🗑 Clear
            </button>
          )}
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto py-4 bg-gray-50">
        {messages.length === 0 && !isLoading ? (
          /* Empty state */
          <div className="h-full flex flex-col items-center justify-center gap-4 px-8 text-center">
            <div className="w-16 h-16 rounded-full bg-indigo-100 flex items-center justify-center">
              <span className="text-3xl">🤖</span>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-800 mb-1">
                Hi! How can I help you today?
              </h2>
              <p className="text-sm text-gray-500 max-w-xs">
                Ask me anything about your account, orders, or any issues you're experiencing.
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-2 mt-2">
              {[
                'Track my order',
                'Request a refund',
                'Update my account',
                'Report an issue',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => sendMessage(suggestion)}
                  disabled={isLoading}
                  className="text-xs text-indigo-600 border border-indigo-200 bg-indigo-50 hover:bg-indigo-100 rounded-full px-3 py-1.5 transition-colors disabled:opacity-50"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Message list */
          <div className="flex flex-col gap-1">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {isLoading && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
}
