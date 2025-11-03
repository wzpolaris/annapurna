import { create } from 'zustand';
import type { AssistantBlock, ConversationPair } from '../types/chat';
import type { ResponseBlock, ResponseCard } from '../types/api';
import { initialConversation } from '../data/sampleConversation';
import { composeUserPair, formatChatTimestamp } from '../utils/chat';

export const DEFAULT_SPACE_KEY = 'home';
export const DEFAULT_SPACE_TITLE = 'Home';
export const DEFAULT_CONVERSATION_LABEL = 'conversation_1';

const slugify = (value: string) =>
  value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '') || DEFAULT_CONVERSATION_LABEL;

const buildConversationId = (spaceKey: string, conversationLabel: string) =>
  `${slugify(spaceKey)}-${slugify(conversationLabel)}`;

const defaultConversationId = buildConversationId(
  DEFAULT_SPACE_KEY,
  DEFAULT_CONVERSATION_LABEL
);

export interface ConversationMeta {
  id: string;
  spaceKey: string;
  spaceTitle: string;
  label: string;
  displayLabel: string;
  pairs: ConversationPair[];
}

export interface AppStoreState {
  activeNav: string;
  activeSpaceKey: string;
  activeSpaceTitle: string | null;
  activeConversationId: string;
  conversations: Record<string, ConversationMeta>;
  selectNav: (navId: string) => void;
  selectSpace: (spaceKey: string, spaceTitle: string) => void;
  ensureConversation: (spaceKey: string, spaceTitle: string, conversationLabel?: string) => string;
  createConversation: (spaceKey: string, spaceTitle: string, conversationLabel?: string) => string;
  sendUserMessage: (
    content: string,
    options?: {
      suppressUser?: boolean;
    }
  ) => {
    conversationId: string;
    pairId: string;
  };
  completeAssistantMessage: (
    conversationId: string,
    pairId: string,
    cards: ResponseCard[],
    timestamp?: string
  ) => void;
  setConversationLabel: (conversationId: string, displayLabel: string) => void;
  resetConversation: (conversationId: string) => void;
}

export const useAppStore = create<AppStoreState>((set, get) => ({
  activeNav: 'home',
  activeSpaceKey: DEFAULT_SPACE_KEY,
  activeSpaceTitle: null,
  activeConversationId: defaultConversationId,
  conversations: {
    [defaultConversationId]: {
      id: defaultConversationId,
      spaceKey: DEFAULT_SPACE_KEY,
      spaceTitle: DEFAULT_SPACE_TITLE,
      label: DEFAULT_CONVERSATION_LABEL,
      displayLabel: DEFAULT_CONVERSATION_LABEL,
      pairs: initialConversation
    }
  },
  selectNav: (navId) => {
    set({ activeNav: navId });
  },
  selectSpace: (spaceKey, spaceTitle) => {
    const conversationId = get().ensureConversation(spaceKey, spaceTitle);
    set({
      activeSpaceKey: spaceKey,
      activeSpaceTitle: spaceTitle,
      activeConversationId: conversationId
    });
  },
  ensureConversation: (spaceKey, spaceTitle, conversationLabel = DEFAULT_CONVERSATION_LABEL) => {
    const labelSlug = slugify(conversationLabel);
    const conversationId = buildConversationId(spaceKey, labelSlug);
    const state = get();
    const existingConversation = state.conversations[conversationId];

    if (!existingConversation) {
      set({
        conversations: {
          ...state.conversations,
          [conversationId]: {
            id: conversationId,
            spaceKey,
            spaceTitle,
            label: labelSlug,
            displayLabel: conversationLabel,
            pairs:
              spaceKey === DEFAULT_SPACE_KEY ? [...initialConversation] : []
          }
        }
      });
    } else if (existingConversation.spaceTitle !== spaceTitle) {
      set({
        conversations: {
          ...state.conversations,
          [conversationId]: {
            ...existingConversation,
            spaceTitle
          }
        }
      });
    }

    return conversationId;
  },
  createConversation: (spaceKey, spaceTitle, conversationLabel) => {
    const state = get();
    const existingCount = Object.values(state.conversations).filter(
      (conversation) => conversation.spaceKey === spaceKey
    ).length;
    const fallbackLabel = `conversation_${existingCount + 1}`;
    const label = conversationLabel ?? fallbackLabel;
    const labelSlug = slugify(label);
    const conversationId = buildConversationId(spaceKey, labelSlug);
    const conversations = get().conversations;

    if (conversations[conversationId]) {
      set({
        conversations: {
          ...conversations,
          [conversationId]: {
            ...conversations[conversationId],
            pairs: []
          }
        }
      });
    } else {
      set({
        conversations: {
          ...conversations,
          [conversationId]: {
            id: conversationId,
            spaceKey,
            spaceTitle,
            label: labelSlug,
            displayLabel: label,
            pairs: []
          }
        }
      });
    }

    set({
      activeConversationId: conversationId,
      activeSpaceKey: spaceKey,
      activeSpaceTitle: spaceTitle
    });

    return conversationId;
  },
  sendUserMessage: (content, options) => {
    const state = get();
    const { activeConversationId, conversations, activeSpaceKey, activeSpaceTitle } = state;
    let conversationId = activeConversationId;
    let conversation = conversations[conversationId];

    if (!conversation) {
      conversationId = state.ensureConversation(
        activeSpaceKey,
        activeSpaceTitle ?? DEFAULT_SPACE_TITLE
      );
      conversation = get().conversations[conversationId];
      set({ activeConversationId: conversationId });
    }

    const resolvedConversation = conversation ?? get().conversations[conversationId];
    const pair = composeUserPair(content);
    if (options?.suppressUser) {
      pair.cardType = 'assistant-only';
      pair.user = undefined;
    }
    const updatedPairs =
      resolvedConversation?.pairs.map((existingPair) => {
        if (!existingPair.assistant) {
          return existingPair;
        }

        let blocksChanged = false;
        const updatedBlocks = existingPair.assistant.blocks.map((block) => {
          if (block.type === 'queryButtons' && !block.interactionCompleted) {
            blocksChanged = true;
            return {
              ...block,
              interactionCompleted: true
            };
          }
          return block;
        });

        return blocksChanged
          ? {
              ...existingPair,
              assistant: {
                ...existingPair.assistant,
                blocks: updatedBlocks
              }
            }
          : existingPair;
      }) ?? [];

    set({
      conversations: {
        ...get().conversations,
        [conversationId]: {
          ...resolvedConversation,
          pairs: [...updatedPairs, pair]
        }
      }
    });

    return { conversationId, pairId: pair.id };
  },
  completeAssistantMessage: (conversationId, pairId, cards, timestamp) => {
    const state = get();
    const conversation = state.conversations[conversationId];
    if (!conversation || !cards || cards.length === 0) {
      return;
    }

    const resolvedTimestamp = timestamp
      ? formatChatTimestamp(new Date(timestamp))
      : formatChatTimestamp(new Date());

    const convertBlocks = (baseId: string, blocks: ResponseBlock[]): AssistantBlock[] =>
      blocks.map((block, index) => {
        const blockId = `${baseId}-block-${index}`;
        const buttons =
          block.type === 'queryButtons'
            ? (block.buttons ?? []).map((button, buttonIndex) => ({
                id: button.id || `${blockId}-action-${buttonIndex}`,
                label: button.label,
                submission: button.submission,
                userMessage: button.userMessage
              }))
            : undefined;

        return {
          id: blockId,
          type: block.type,
          content: block.content,
          altText: block.altText,
          buttons,
          interactionCompleted:
            block.type === 'queryButtons'
              ? Boolean(block.interactionCompleted)
              : undefined
        };
      });

    const primaryCard = cards[0];
    const primaryBlocks = convertBlocks(pairId, primaryCard.assistantBlocks);
    const primaryAssistant = {
      id: `${pairId}-assistant`,
      role: 'assistant' as const,
      author: 'Atlas',
      content: primaryBlocks[0]?.content,
      blocks: primaryBlocks,
      timestamp: resolvedTimestamp
    };

    let pairs = conversation.pairs.map((pair) => {
      if (pair.id !== pairId) {
        return pair;
      }

      const showUserText = primaryCard.metadata?.showUserText !== false;
      let updatedUser = undefined;
      if (showUserText) {
        const userMessage = primaryCard.userText ?? pair.user?.content ?? '';
        updatedUser = pair.user
          ? { ...pair.user, content: userMessage || pair.user.content }
          : userMessage
          ? {
              id: `${pairId}-user`,
              role: 'user' as const,
              author: 'You',
              content: userMessage,
              timestamp: resolvedTimestamp
            }
          : undefined;
      }

      return {
        ...pair,
        cardType: primaryCard.cardType,
        user: updatedUser,
        assistant: primaryAssistant
      };
    });

    const extraPairs: ConversationPair[] = cards.slice(1).map((card, index) => {
      const newPairId = `${pairId}-extra-${index + 1}`;
      const formattedBlocks = convertBlocks(newPairId, card.assistantBlocks);
      const assistantMessage = {
        id: `${newPairId}-assistant`,
        role: 'assistant' as const,
        author: 'Atlas',
        content: formattedBlocks[0]?.content,
        blocks: formattedBlocks,
        timestamp: resolvedTimestamp
      };

      const newPair: ConversationPair = {
        id: newPairId,
        cardType: card.cardType,
        assistant: assistantMessage
      };

      const showExtraUser = card.cardType === 'user-assistant' && card.metadata?.showUserText !== false;
      if (showExtraUser && card.userText) {
        newPair.user = {
          id: `${newPairId}-user`,
          role: 'user' as const,
          author: 'You',
          content: card.userText,
          timestamp: resolvedTimestamp
        };
      }

      return newPair;
    });

    pairs = [...pairs, ...extraPairs];

    set({
      conversations: {
        ...state.conversations,
        [conversationId]: {
          ...conversation,
          pairs
        }
      }
    });
  },
  setConversationLabel: (conversationId, displayLabel) => {
    const state = get();
    const conversation = state.conversations[conversationId];
    if (!conversation) {
      return;
    }

    const newLabelSlug = slugify(displayLabel);
    const newConversationId = buildConversationId(conversation.spaceKey, newLabelSlug);

    if (newConversationId === conversationId) {
      set({
        conversations: {
          ...state.conversations,
          [conversationId]: {
            ...conversation,
            displayLabel,
            label: newLabelSlug
          }
        }
      });
      return;
    }

    const { [conversationId]: _removed, ...rest } = state.conversations;
    set({
      conversations: {
        ...rest,
        [newConversationId]: {
          ...conversation,
          id: newConversationId,
          displayLabel,
          label: newLabelSlug
        }
      },
      activeConversationId:
        state.activeConversationId === conversationId
          ? newConversationId
          : state.activeConversationId
    });
  },
  resetConversation: (conversationId) => {
    const state = get();
    const conversation = state.conversations[conversationId];
    if (!conversation) {
      return;
    }

    set({
      conversations: {
        ...state.conversations,
        [conversationId]: {
          ...conversation,
          pairs: []
        }
      }
    });
  }
}));

export const selectActiveConversationPairs = (state: AppStoreState) => {
  const conversation = state.conversations[state.activeConversationId];
  return conversation?.pairs ?? [];
};
