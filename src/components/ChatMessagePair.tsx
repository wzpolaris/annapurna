import { Divider, Group, Loader, Paper, Stack, Text, Title } from '@mantine/core';
import type { ConversationPair } from '../types/chat';

interface ChatMessagePairProps {
  pair: ConversationPair;
}

const AssistantPending = () => (
  <Group align="center" gap="xs">
    <Loader size="sm" color="teal" type="dots" />
    <Text size="sm" c="dimmed">
      Atlas is thinking…
    </Text>
  </Group>
);

export const ChatMessagePair = ({ pair }: ChatMessagePairProps) => (
  <Paper
    withBorder
    radius="sm"
    shadow="xs"
    p="sm"
    bg="white"
    data-chat-pair={pair.id}
  >
    <Stack gap="xs">
      <Group justify="space-between" align="center">
        <Text size="xs" c="dimmed" fw={500}>
          {pair.user.author}
        </Text>
        <Text size="xs" c="dimmed">
          {pair.assistant?.timestamp ?? pair.user.timestamp}
        </Text>
      </Group>

      <Stack gap={2}>
        <Title order={4}>{pair.user.content}</Title>
      </Stack>

      <Divider />

      {pair.assistant ? (
        <Text size="sm" lh={1.6}>
          {pair.assistant.content}
        </Text>
      ) : (
        <AssistantPending />
      )}
    </Stack>
  </Paper>
);
