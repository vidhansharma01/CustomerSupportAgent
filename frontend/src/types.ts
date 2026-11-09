export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'tool';
  content: string;
  timestamp: Date;
  sources?: SourceDoc[];
  escalated?: boolean;
  ticketId?: string;
}

export interface SourceDoc {
  title: string;
  category: string;
  relevance: number;
}

export interface ChatRequest {
  conversation_id: string;
  message: string;
  customer_id?: string;
}

export interface ChatResponse {
  conversation_id: string;
  message: string;
  sources: SourceDoc[];
  escalated: boolean;
  ticket_id?: string;
}
