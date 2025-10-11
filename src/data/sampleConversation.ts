import type { ConversationPair } from '../types/chat';

const timestamp = new Intl.DateTimeFormat('en', {
  hour: 'numeric',
  minute: '2-digit'
});

const now = new Date();

const formatTime = (deltaMinutes: number) =>
  timestamp.format(new Date(now.getTime() - deltaMinutes * 60_000));

export const initialConversation: ConversationPair[] = [
  {
    id: 'pair-1',
    user: {
      id: 'pair-1-user',
      role: 'user',
      author: 'You',
      content:
        'What React-based frameworks should I consider for layout and components for a web app?',
      timestamp: formatTime(32)
    },
    assistant: {
      id: 'pair-1-assistant',
      role: 'assistant',
      author: 'Atlas',
      content:
        'Great question! For versatile UI work consider Mantine, MUI, Chakra UI, or Radix. Each ships accessible primitives and has strong community momentum as of 2025.',
      timestamp: formatTime(31)
    }
  },
  {
    id: 'pair-2',
    user: {
      id: 'pair-2-user',
      role: 'user',
      author: 'You',
      content:
        'Which one is the easiest to customize for a productivity dashboard like the one above?',
      timestamp: formatTime(24)
    },
    assistant: {
      id: 'pair-2-assistant',
      role: 'assistant',
      author: 'Atlas',
      content:
        'Mantine and Chakra favor rapid customization. Mantine ships opinionated themes plus CSS-in-JS primitives, making it quick to restyle sidebars, cards, and chat panes.',
      timestamp: formatTime(23)
    }
  },
  {
    id: 'pair-3',
    user: {
      id: 'pair-3-user',
      role: 'user',
      author: 'You',
      content:
        'Could you suggest a sensible folder structure for keeping chat features organized?',
      timestamp: formatTime(12)
    },
    assistant: {
      id: 'pair-3-assistant',
      role: 'assistant',
      author: 'Atlas',
      content:
        'Sure! Split shared types, reusable components, and feature configs. For instance, keep navigation data in `data/`, UI pieces in `components/`, and chat helpers in `utils/`.',
      timestamp: formatTime(11)
    }
  }
];
