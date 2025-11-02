import type { ChatMessage, ConversationPair } from '../types/chat';

let pairCount = 100;

const pad = (value: number, length = 2) => value.toString().padStart(length, '0');

export const formatChatTimestamp = (date: Date): string => {
  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1);
  const day = pad(date.getDate());
  const hour = pad(date.getHours());
  const minute = pad(date.getMinutes());
  const second = pad(date.getSeconds());
  const tenths = Math.floor(date.getMilliseconds() / 100);

  return `${year}-${month}-${day} ${hour}:${minute}:${second}.${tenths}`;
};

const formatTimestamp = () => formatChatTimestamp(new Date());

const createChatMessage = (
  role: ChatMessage['role'],
  pairId: string,
  author: string,
  content: string,
  timestamp = formatTimestamp()
): ChatMessage => ({
  id: `${pairId}-${role}`,
  role,
  author,
  content,
  timestamp
});

export const composeUserPair = (userMessage: string): ConversationPair => {
  pairCount += 1;
  const pairId = `pair-${pairCount}`;
  return {
    id: pairId,
    user: createChatMessage('user', pairId, 'You', userMessage)
  };
};
