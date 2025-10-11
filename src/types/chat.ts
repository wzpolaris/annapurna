export type ChatRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: ChatRole;
  author: string;
  content: string;
  timestamp: string;
}

export interface ConversationPair {
  id: string;
  user: ChatMessage;
  assistant?: ChatMessage;
}
