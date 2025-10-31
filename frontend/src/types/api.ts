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

export interface ChatApiResponse {
  conversationId: string;
  outputs: ResponseBlock[];
  timestamp: string;
}
