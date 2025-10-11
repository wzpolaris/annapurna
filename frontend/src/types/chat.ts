export type ChatRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: ChatRole;
  author: string;
  content?: string;
  timestamp: string;
}

export type AssistantBlockType = 'markdown' | 'image' | 'html';

export interface AssistantBlock {
  id: string;
  type: AssistantBlockType;
  content: string;
  altText?: string;
}

export interface AssistantMessage extends Omit<ChatMessage, 'role'> {
  role: 'assistant';
  blocks: AssistantBlock[];
  content?: string;
}

export interface ConversationPair {
  id: string;
  user: ChatMessage;
  assistant?: AssistantMessage;
}
