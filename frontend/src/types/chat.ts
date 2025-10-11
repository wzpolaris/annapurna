export type ChatRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: ChatRole;
  author: string;
  content?: string;
  timestamp: string;
}

export type AssistantBlockType = 'markdown' | 'image' | 'html' | 'queryButtons';

export interface AssistantActionButton {
  id: string;
  label: string;
  submission: string;
  userMessage?: string;
}

export interface AssistantBlock {
  id: string;
  type: AssistantBlockType;
  content: string;
  altText?: string;
  buttons?: AssistantActionButton[];
  interactionCompleted?: boolean;
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
