import { create } from 'zustand';
import type { AssistantBlock, ConversationPair } from '../types/chat';
import type { ResponseBlock } from '../types/api';
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
  sendUserMessage: (content: string) => {
    conversationId: string;
    pairId: string;
  };
  completeAssistantMessage: (
    conversationId: string,
    pairId: string,
    blocks: ResponseBlock[],
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
  sendUserMessage: (content) => {
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
  completeAssistantMessage: (conversationId, pairId, blocks, timestamp) => {
    const state = get();
    const conversation = state.conversations[conversationId];
    if (!conversation) {
      return;
    }

    const formattedBlocks: AssistantBlock[] = blocks.map((block, index) => {
      const blockId = `${pairId}-block-${index}`;
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

    if (formattedBlocks.length === 0) {
      formattedBlocks.push({
        id: `${pairId}-block-0`,
        type: 'markdown',
        content: 'Assistant response was empty.',
      });
    }

    const resolvedTimestamp = timestamp
      ? formatChatTimestamp(new Date(timestamp))
      : formatChatTimestamp(new Date());

    const assistantMessage = {
      id: `${pairId}-assistant`,
      role: 'assistant' as const,
      author: 'Atlas',
      content: formattedBlocks[0]?.content,
      blocks: formattedBlocks,
      timestamp: resolvedTimestamp
    };

    set({
      conversations: {
        ...state.conversations,
        [conversationId]: {
          ...conversation,
          pairs: conversation.pairs.map((pair) =>
            pair.id === pairId ? { ...pair, assistant: assistantMessage } : pair
          )
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
