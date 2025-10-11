import type { ChatMessage, ConversationPair } from '../types/chat';

let pairCount = 100;

const timestampFormatter = new Intl.DateTimeFormat('en', {
  hour: 'numeric',
  minute: '2-digit'
});

const formatTimestamp = () => timestampFormatter.format(new Date());

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
