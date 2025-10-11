import {
  Box,
  Divider,
  Group,
  Loader,
  Paper,
  Stack,
  Text,
  Title,
  TypographyStylesProvider
} from '@mantine/core';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import type { AssistantBlock, ConversationPair } from '../types/chat';

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

const renderBlock = (block: AssistantBlock): JSX.Element => {
  switch (block.type) {
    case 'image':
      return (
        <Paper withBorder radius="sm" p="sm" bg="gray.0">
          <img src={block.content} alt={block.altText ?? 'Generated visual'} style={{ maxWidth: '100%' }} />
          {block.altText && (
            <Text size="xs" c="dimmed" mt="xs">
              {block.altText}
            </Text>
          )}
        </Paper>
      );
    case 'html':
      return (
        <Paper withBorder radius="sm" p="sm">
          <Box dangerouslySetInnerHTML={{ __html: block.content }} />
        </Paper>
      );
    case 'markdown':
    default:
      return (
        <TypographyStylesProvider>
          <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkMath]}
            rehypePlugins={[rehypeKatex]}
          >
            {block.content}
          </ReactMarkdown>
        </TypographyStylesProvider>
      );
  }
};

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
        <Stack gap="sm">
          {(pair.assistant.blocks ?? []).map((block) => (
            <Box key={block.id}>{renderBlock(block)}</Box>
          ))}
        </Stack>
      ) : (
        <AssistantPending />
      )}
    </Stack>
  </Paper>
);
