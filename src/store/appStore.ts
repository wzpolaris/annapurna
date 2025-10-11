import { create } from 'zustand';
import type { ConversationPair } from '../types/chat';
import { initialConversation } from '../data/sampleConversation';
import { composeAssistantMessage, composeUserPair } from '../utils/chat';

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
    prompt: string;
  };
  completeAssistantMessage: (conversationId: string, pairId: string, prompt: string) => void;
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

    const pair = composeUserPair(content);

    set({
      conversations: {
        ...get().conversations,
        [conversationId]: {
          ...conversation,
          pairs: [...conversation.pairs, pair]
        }
      }
    });

    return { conversationId, pairId: pair.id, prompt: content };
  },
  completeAssistantMessage: (conversationId, pairId, prompt) => {
    const state = get();
    const conversation = state.conversations[conversationId];
    if (!conversation) {
      return;
    }

    const assistantMessage = composeAssistantMessage(prompt, pairId);

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
