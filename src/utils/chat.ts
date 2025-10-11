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

const createAssistantReply = (prompt: string) => {
  const topic = prompt.length > 72 ? `${prompt.slice(0, 69)}…` : prompt;
  return `Here is a quick take on "${topic}". Focus on prioritising sources, then capture follow-up ideas from your teammates.`;
};

export const composeUserPair = (userMessage: string): ConversationPair => {
  pairCount += 1;
  const pairId = `pair-${pairCount}`;
  return {
    id: pairId,
    user: createChatMessage('user', pairId, 'You', userMessage)
  };
};

export const composeAssistantMessage = (userMessage: string, pairId: string): ChatMessage =>
  createChatMessage('assistant', pairId, 'Atlas', createAssistantReply(userMessage));
