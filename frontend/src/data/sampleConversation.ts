import type { ConversationPair } from '../types/chat';
import { formatChatTimestamp } from '../utils/chat';

const now = new Date();

const formatTime = (deltaMinutes: number) =>
  formatChatTimestamp(new Date(now.getTime() - deltaMinutes * 60_000));

export const initialConversation: ConversationPair[] = [
  {
    id: 'pair-1',
    cardType: 'user-assistant',
    user: {
      id: 'pair-1-user',
      role: 'user',
      author: 'You',
      content:
        'Where is Paris?'
    },
    assistant: {
      id: 'pair-1-assistant',
      role: 'assistant',
      author: 'Atlas',
      content:
        'Hmmmm.... Texas !! .. just kidding France 🇫🇷!!!',
      blocks: [
        {
          id: 'pair-1-assistant-block-0',
          type: 'markdown',
          content:
            'Hmmmm.... Texas !! .. just kidding France 🇫🇷!!!',
        }
      ],
      timestamp: formatTime(31)
    }
  },
  {
    id: 'pair-2',
    cardType: 'user-assistant',
    user: {
      id: 'pair-2-user',
      role: 'user',
      author: 'You',
      content:
        'When did the Red Sox first win the World Series?',
      timestamp: formatTime(24)
    },
    assistant: {
      id: 'pair-2-assistant',
      role: 'assistant',
      author: 'Atlas',
      content:
        'In 1903, the Boston Americans (now known as the Red Sox) won the first-ever World Series by defeating the Pittsburgh Pirates in a best-of-nine series, five games to three.',
      blocks: [
        {
          id: 'pair-2-assistant-block-0',
          type: 'markdown',
          content:
            'In 1903, the Boston Americans (now known as the Red Sox) won the first-ever World Series by defeating the Pittsburgh Pirates in a best-of-nine series, five games to three.',
        }
        // ,
        // {
        //   id: 'pair-2-assistant-block-1',
        //   type: 'queryButtons',
        //   content: 'RedSox World Series Championships',
        //   buttons: [
        //     {
        //       id: 'pair-2-assistant-block-1-1903',
        //       label: '1903',
        //       submission: 'Tell me about RedSox 1903 World Series Championship',
        //       userMessage: 'Tell me about RedSox 1903 World Series Championship'
        //     },
        //     {
        //       id: 'pair-2-assistant-block-1-1912',
        //       label: '1912',
        //       submission: 'Tell me about RedSox 1912 World Series Championship',
        //       userMessage: 'Tell me about RedSox 1912 World Series Championship'
        //     },
        //     {
        //       id: 'pair-2-assistant-block-1-1915',
        //       label: '1915',
        //       submission: 'Tell me about RedSox 1915 World Series Championship',
        //       userMessage: 'Tell me about RedSox 1915 World Series Championship'
        //     },
        //     {
        //       id: 'pair-2-assistant-block-1-1916',
        //       label: '1916',
        //       submission: 'Tell me about RedSox 1916 World Series Championship',
        //       userMessage: 'Tell me about RedSox 1916 World Series Championship'
        //     },
        //     {
        //       id: 'pair-2-assistant-block-1-1918',
        //       label: '1918',
        //       submission: 'Tell me about RedSox 1918 World Series Championship',
        //       userMessage: 'Tell me about RedSox 1918 World Series Championship'
        //     },
        //     // ,
        //     // {
        //     //   id: 'pair-3-assistant-block-1-no',
        //     //   label: 'No thank you',
        //     //   submission: '',
        //     //   userMessage: ''
        //     // }
        //   ]
        // }

      ],
      timestamp: formatTime(23)
    }
  },
  {
    id: 'pair-3',
    cardType: 'user-assistant',
    user: {
      id: 'pair-3-user',
      role: 'user',
      author: 'You',
      content:
        'Is Pluto a planet?',
      timestamp: formatTime(12)
    },
    assistant: {
      id: 'pair-3-assistant',
      role: 'assistant',
      author: 'Atlas',
      content:
        'Well it depends who you ask! The International Astronomical Union reclassified Pluto in 2006, because it has not "cleared its neighborhood," one of the criteria established to be a planet. However, many of us still affectionately consider Pluto the ninth planet in our solar system.',
      blocks: [
        {
          id: 'pair-3-assistant-block-0',
          type: 'markdown',
          content:
            'Well it depends who you ask! The International Astronomical Union reclassified Pluto in 2006, because it has not "cleared its neighborhood," one of the criteria established to be a planet. However, many of us still affectionately consider Pluto the ninth planet in our solar system.',
        },
        {
          id: 'pair-3-assistant-block-1',
          type: 'queryButtons',
          content: 'Would you like me to provide greater detail?',
          buttons: [
            {
              id: 'pair-3-assistant-block-1-yes',
              label: 'Yes, tell me more',
              submission: 'Tell me more about Pluto',
              userMessage: 'Tell me more about Pluto'
            }
            // ,
            // {
            //   id: 'pair-3-assistant-block-1-no',
            //   label: 'No thank you',
            //   submission: '',
            //   userMessage: ''
            // }
          ]
        }
      ],
      timestamp: formatTime(11)
    }
  }
];
