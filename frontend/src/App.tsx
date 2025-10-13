import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Box,
  Button,
  Card,
  Flex,
  Group,
  Paper,
  ScrollArea,
  SimpleGrid,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { IconSearch } from '@tabler/icons-react';
import { conversationExchangeTitleColor } from './theme/colors';
type TablerIconComponent = typeof IconSearch;

const homePrompt =
  '';
import {
  primaryNavigation,
  secondaryNavigation
} from './data/navigation';
import { Sidebar } from './components/Sidebar';
import { ChatMessagePair } from './components/ChatMessagePair';
import { ChatInput } from './components/ChatInput';
import { ConversationContainer } from './components/ConversationContainer';
import {
  DEFAULT_SPACE_KEY,
  DEFAULT_SPACE_TITLE,
  selectActiveConversationPairs,
  useAppStore
} from './store/appStore';
import type { ChatApiResponse, ResponseBlock } from './types/api';

const spacesCardDescriptions = {
  'ai-fundmodeler': 'Build predictive fund models with AI-assisted workflows.',
  'sherlock-holmes': 'Investigate anomalies with forensic analytics.',
  'risk-chat': 'Converse with risk metrics to surface edge cases.',
  'private-illiquids': 'Stress test private and illiquid holdings.',
  optimize: 'Tune portfolio exposures across constraints.',
  scenarios: 'Simulate future paths and macro scenarios.'
} as const;

interface SpacesCardConfig {
  id: keyof typeof spacesCardDescriptions;
  title: string;
  icon?: TablerIconComponent;
}

const spacesCards: SpacesCardConfig[] = [
  { id: 'ai-fundmodeler', title: 'AI FundModeler' },
  { id: 'sherlock-holmes', title: 'Sherlock Holmes', icon: IconSearch },
  { id: 'risk-chat', title: 'Risk Chat' },
  { id: 'private-illiquids', title: 'Private & Illiquids' },
  { id: 'optimize', title: 'Optimize' },
  { id: 'scenarios', title: 'Scenarios' }
];

export default function App() {
  const [inputValue, setInputValue] = useState('');
  const conversationPairs = useAppStore(selectActiveConversationPairs);
  const activeNav = useAppStore((state) => state.activeNav);
  const activeSpaceKey = useAppStore((state) => state.activeSpaceKey);
  const activeSpaceTitle = useAppStore((state) => state.activeSpaceTitle);
  const selectNav = useAppStore((state) => state.selectNav);
  const selectSpace = useAppStore((state) => state.selectSpace);
  const ensureConversation = useAppStore((state) => state.ensureConversation);
  const createConversation = useAppStore((state) => state.createConversation);
  const sendUserMessage = useAppStore((state) => state.sendUserMessage);
  const completeAssistantMessage = useAppStore((state) => state.completeAssistantMessage);
  const viewportRef = useRef<HTMLDivElement>(null);
  const isChatView = activeNav !== 'spaces';
  const headerText = isChatView
    ? activeSpaceKey !== DEFAULT_SPACE_KEY && activeSpaceTitle
      ? activeSpaceTitle
      : `Home ${homePrompt}`
    : activeSpaceTitle ?? 'Choose an analysis workspace to launch.';

  const navigationSections = useMemo(
    () => [
      { id: 'primary', items: primaryNavigation },
      { id: 'secondary', items: secondaryNavigation }
    ],
    []
  );

  useEffect(() => {
    if (!isChatView) {
      return;
    }

    const viewport = viewportRef.current;
    if (!viewport || conversationPairs.length === 0) {
      return;
    }

    const latestPairId = conversationPairs[conversationPairs.length - 1]?.id;
    if (!latestPairId) {
      return;
    }

    const scrollToLatest = () => {
      const latestNode = viewport.querySelector<HTMLElement>(
        `[data-chat-pair="${latestPairId}"]`
      );

      if (!latestNode) {
        return;
      }

      const viewportHeight = viewport.clientHeight;
      const fitsInViewport = latestNode.offsetHeight <= viewportHeight;
      const bottomScrollTop = Math.max(viewport.scrollHeight - viewportHeight, 0);
      const targetTop = fitsInViewport ? bottomScrollTop : latestNode.offsetTop;

      viewport.scrollTo({
        top: targetTop,
        behavior: 'smooth'
      });
    };

    const runScrollAfterPaint = () => {
      scrollToLatest();

      const latestNode = viewport.querySelector<HTMLElement>(
        `[data-chat-pair="${latestPairId}"]`
      );

      if (
        !latestNode ||
        typeof window === 'undefined' ||
        !('ResizeObserver' in window)
      ) {
        return;
      }

      const resizeObserver = new window.ResizeObserver(() => {
        scrollToLatest();
        resizeObserver.disconnect();
      });

      resizeObserver.observe(latestNode);

      return () => {
        resizeObserver.disconnect();
      };
    };

    let cleanupResizeObserver: (() => void) | undefined;
    const scheduleScroll = () => {
      cleanupResizeObserver?.();
      const cleanup = runScrollAfterPaint();
      if (cleanup) {
        cleanupResizeObserver = cleanup;
      }
    };

    let rafId: number | null = null;

    if (typeof window !== 'undefined' && 'requestAnimationFrame' in window) {
      rafId = window.requestAnimationFrame(scheduleScroll);
    } else {
      scheduleScroll();
    }

    return () => {
      if (rafId !== null) {
        cancelAnimationFrame(rafId);
      }
      cleanupResizeObserver?.();
    };
  }, [conversationPairs, isChatView]);

  const submitMessage = async (message: string, options?: { displayMessage?: string }) => {
    const trimmedMessage = message.trim();
    if (!trimmedMessage) {
      return;
    }

    const displayMessage = options?.displayMessage?.trim() || trimmedMessage;
    const spaceKey = activeSpaceKey ?? DEFAULT_SPACE_KEY;
    const spaceTitle = resolveSpaceTitle(spaceKey);
    const { conversationId, pairId } = sendUserMessage(displayMessage);
    try {
      const conversationState = useAppStore.getState().conversations[conversationId];
      const history =
        conversationState?.pairs.slice(0, -1).flatMap((pair) => {
          const messages = [] as Array<{ role: 'user' | 'assistant'; content: string }>;
          if (pair.user.content) {
            messages.push({ role: 'user', content: pair.user.content });
          }
          if (pair.assistant?.blocks?.length) {
            const combined = pair.assistant.blocks.map((block) => block.content).join('\n\n');
            messages.push({ role: 'assistant', content: combined });
          }
          return messages;
        }) ?? [];

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          conversationId,
          spaceKey,
          spaceTitle,
          message: trimmedMessage,
          history
        })
      });

      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
      }

      const data: ChatApiResponse = await response.json();
      completeAssistantMessage(conversationId, pairId, data.outputs, data.timestamp);
    } catch (error) {
      console.error('Failed to fetch assistant response', error);
      const fallbackBlocks: ResponseBlock[] = [
        {
          type: 'markdown',
          content: 'Sorry, something went wrong while contacting the assistant. Please try again.'
        }
      ];
      completeAssistantMessage(conversationId, pairId, fallbackBlocks);
    }
  };

  const handleSend = async () => {
    const trimmed = inputValue.trim();
    if (!trimmed) {
      return;
    }

    setInputValue('');
    await submitMessage(trimmed);
  };

  const handleQuickReply = (submission: string, displayMessage?: string) => {
    setInputValue('');
    void submitMessage(submission, { displayMessage });
  };

  const resolveSpaceTitle = (spaceKey: string) => {
    if (spaceKey === DEFAULT_SPACE_KEY) {
      return DEFAULT_SPACE_TITLE;
    }

    return (
      spacesCards.find((card) => card.id === spaceKey)?.title ??
      activeSpaceTitle ??
      spaceKey
    );
  };

  const handleNavigationSelect = (id: string) => {
    if (id === 'new-chat') {
      const spaceKey = activeSpaceKey ?? DEFAULT_SPACE_KEY;
      const spaceTitle = resolveSpaceTitle(spaceKey);
      createConversation(spaceKey, spaceTitle);
      setInputValue('');
      selectNav('home');
      return;
    }

    selectNav(id);

    if (id !== 'spaces') {
      const spaceTitle = resolveSpaceTitle(activeSpaceKey ?? DEFAULT_SPACE_KEY);
      ensureConversation(activeSpaceKey ?? DEFAULT_SPACE_KEY, spaceTitle);
    }
  };

  return (
    <Flex h="100dvh" bg="gray.0">
      <Sidebar
        sections={navigationSections}
        activeId={activeNav}
        onSelect={handleNavigationSelect}
      />

      <Flex
        direction="column"
        flex={1}
        px="xl"
        py="xl"
        gap="lg"
        bg="white"
        style={{ minHeight: 0, overflow: 'hidden' }}
      >
        <Group justify="space-between" align="center" style={{ flexShrink: 0 }}>
          <Title order={2} fw={600} c={conversationExchangeTitleColor}>
            NORTHFIELD{' '}
            <Text component="span" inherit fs="italic">
              ai
            </Text>
          </Title>
          <Group gap="xs">
            <Button variant="light" size="sm" color="teal">
              Summarise
            </Button>
            <Button variant="light" size="sm" color="gray">
              Export
            </Button>
            <Button variant="subtle" size="sm" color="gray">
              Share
            </Button>
          </Group>
        </Group>

        <Text fz="sm" c="dimmed" style={{ flexShrink: 0 }}>
          {headerText}
        </Text>

        <ConversationContainer>
          <Paper
            withBorder
            radius="lg"
            p="xl"
            shadow="sm"
            bg="gray.0"
            style={{
              flex: 1,
              minHeight: 0,
              display: 'flex',
              flexDirection: 'column',
              gap: '1.5rem',
              overflow: 'hidden'
            }}
          >
            {isChatView ? (
              <ScrollArea
                type="auto"
                viewportRef={viewportRef}
                style={{ flex: 1, minHeight: 0 }}
              >
                <Stack gap="lg" pr="md">
                  {conversationPairs.map((pair) => (
                    <ChatMessagePair
                      key={pair.id}
                      pair={pair}
                      onQuickReply={handleQuickReply}
                    />
                  ))}
                </Stack>
              </ScrollArea>
            ) : (
              <Box style={{ flex: 1, minHeight: 0 }}>
                <SimpleGrid
                  cols={{ base: 1, xs: 2, md: 3 }}
                  spacing="lg"
                  verticalSpacing="lg"
                >
                  {spacesCards.map(({ id, title, icon: Icon }) => {
                    const isSelected = activeSpaceKey === id;
                    return (
                      <Card
                        key={id}
                        withBorder
                        radius="md"
                        shadow="sm"
                        p="lg"
                        onClick={() => selectSpace(id, title)}
                      style={{
                        cursor: 'pointer',
                        borderColor: isSelected ? conversationExchangeTitleColor : undefined,
                        boxShadow: isSelected ? '0 0 0 1px rgba(2, 189, 157, 0.35)' : undefined
                      }}
                    >
                        <Stack gap="sm">
                          <Group gap="xs" align="center">
                            <Title order={4}>{title}</Title>
                            {Icon ? <Icon size={18} stroke={1.6} /> : null}
                          </Group>
                          <Text size="sm" c="dimmed">
                            {spacesCardDescriptions[id]}
                          </Text>
                        </Stack>
                      </Card>
                    );
                  })}
                </SimpleGrid>
              </Box>
            )}
          </Paper>

          {isChatView && (
            <Box px="xs" style={{ flexShrink: 0 }}>
              <ChatInput
                value={inputValue}
                onChange={setInputValue}
                onSubmit={handleSend}
              />
            </Box>
          )}
        </ConversationContainer>
      </Flex>
    </Flex>
  );
}
