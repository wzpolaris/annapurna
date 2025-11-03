export type ResponseBlockType = 'markdown' | 'image' | 'html' | 'queryButtons' | 'upload';

export interface ResponseActionButton {
  id: string;
  label: string;
  submission: string;
  userMessage?: string;
}

export interface ResponseBlock {
  type: ResponseBlockType;
  content: string;
  altText?: string;
  buttons?: ResponseActionButton[];
  interactionCompleted?: boolean;
}

export type ResponseCardType = 'user-assistant' | 'assistant-only' | 'system';

export interface ResponseCard {
  cardType: ResponseCardType;
  userText?: string;
  assistantBlocks: ResponseBlock[];
  metadata?: Record<string, unknown>;
}

export interface ChatApiResponse {
  conversationId: string;
  cards: ResponseCard[];
  timestamp: string;
}
