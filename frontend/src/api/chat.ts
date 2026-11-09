import type { ChatRequest, ChatResponse, Message } from '../types';

const BASE_URL = '/api';

export async function sendMessage(req: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(req),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(
      `Failed to send message: ${response.status} ${response.statusText}. ${errorBody}`
    );
  }

  return response.json() as Promise<ChatResponse>;
}

export async function getHistory(conversationId: string): Promise<Message[]> {
  const response = await fetch(
    `${BASE_URL}/chat/history/${encodeURIComponent(conversationId)}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(
      `Failed to fetch history: ${response.status} ${response.statusText}. ${errorBody}`
    );
  }

  const raw = await response.json() as Array<Omit<Message, 'timestamp'> & { timestamp: string }>;
  return raw.map((msg) => ({
    ...msg,
    timestamp: new Date(msg.timestamp),
  }));
}
