export type ResponseBlockType = 'markdown' | 'image' | 'html';

export interface ResponseBlock {
  type: ResponseBlockType;
  content: string;
  altText?: string;
}

export interface ChatApiResponse {
  conversationId: string;
  outputs: ResponseBlock[];
  timestamp: string;
}
