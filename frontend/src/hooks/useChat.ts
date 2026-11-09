import { useState, useCallback, useMemo } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { sendMessage as apiSendMessage } from '../api/chat';
import type { Message } from '../types';

interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  conversationId: string;
  sendMessage: (text: string) => Promise<void>;
  clearChat: () => void;
}

export function useChat(customerId?: string): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Generate a stable conversation ID per hook instance
  const conversationId = useMemo(() => uuidv4(), []);

  const sendMessage = useCallback(
    async (text: string): Promise<void> => {
      const trimmed = text.trim();
      if (!trimmed) return;

      const userMessage: Message = {
        id: uuidv4(),
        role: 'user',
        content: trimmed,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      try {
        const response = await apiSendMessage({
          conversation_id: conversationId,
          message: trimmed,
          ...(customerId ? { customer_id: customerId } : {}),
        });

        const assistantMessage: Message = {
          id: uuidv4(),
          role: 'assistant',
          content: response.message,
          timestamp: new Date(),
          sources: response.sources.length > 0 ? response.sources : undefined,
          escalated: response.escalated,
          ticketId: response.ticket_id,
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } catch (error) {
        const errorMessage: Message = {
          id: uuidv4(),
          role: 'assistant',
          content:
            'Sorry, I encountered an error while processing your request. Please try again.',
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
        console.error('Chat error:', error);
      } finally {
        setIsLoading(false);
      }
    },
    [conversationId, customerId]
  );

  const clearChat = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    isLoading,
    conversationId,
    sendMessage,
    clearChat,
  };
}
