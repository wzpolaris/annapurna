import {
  Box,
  Button,
  Divider,
  Group,
  Loader,
  Paper,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { useEffect, useRef } from 'react';
import 'katex/dist/katex.min.css';
import type { AssistantBlock, ConversationPair } from '../types/chat';
import { conversationExchangeTitleColor } from '../theme/colors';
import { UploadBlock } from './blocks/UploadBlock';
import { MarkdownWithDrawers } from './blocks/MarkdownWithDrawers';
import Pdf2pViewerBlock from './blocks/pdf2p/Pdf2pViewerBlock';
import { runKatexAutoRender } from '../utils/katex';

interface ChatMessagePairProps {
  pair: ConversationPair;
  onQuickReply?: (submission: string, displayMessage?: string) => void;
}

const HtmlBlock = ({ content }: { content: string }) => {
  const htmlRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    runKatexAutoRender(htmlRef.current);
  }, [content]);

  return (
    <Paper withBorder radius="sm" p="sm">
      <Box ref={htmlRef} dangerouslySetInnerHTML={{ __html: content }} />
    </Paper>
  );
};

const AssistantPending = () => (
  <Group align="center" gap="xs" data-testid="assistant-pending">
    <Loader size="sm" color="teal" type="dots" />
    <Text size="sm" c="dimmed">
      Lumenta is thinking…
    </Text>
  </Group>
);

const renderBlock = (
  block: AssistantBlock,
  onQuickReply?: (submission: string, displayMessage?: string) => void
): JSX.Element => {
  switch (block.type) {
    case 'queryButtons':
      return (
        <Stack gap="xs">
          <Text fw={500}>{block.content}</Text>
          <Group gap="xs" wrap="wrap">
            {(block.buttons ?? []).map((button) => (
              <Button
                key={button.id}
                variant="light"
                color={block.interactionCompleted ? 'gray' : 'teal'}
                size="xs"
                disabled={block.interactionCompleted}
                onClick={() => {
                  if (block.interactionCompleted) {
                    return;
                  }
                  onQuickReply?.(button.submission, button.userMessage ?? button.label);
                }}
              >
                {button.label}
              </Button>
            ))}
          </Group>
        </Stack>
      );
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
    case 'pdf2p':
      return block.fileUrl ? (
        <Pdf2pViewerBlock
          fileUrl={block.fileUrl}
          filename={block.filename}
          fileSize={block.fileSize}
        />
      ) : (
        <Paper withBorder radius="sm" p="sm" bg="gray.0">
          <Text size="sm" c="dimmed">
            PDF unavailable.
          </Text>
        </Paper>
      );
    case 'upload':
      return <UploadBlock content={block.content} />;
    case 'html':
      return <HtmlBlock content={block.content} />;
    case 'markdown':
    default:
      return <MarkdownWithDrawers content={block.content} />;
  }
};

export const ChatMessagePair = ({ pair, onQuickReply }: ChatMessagePairProps) => {
  const hasUser = Boolean(pair.user?.content);
  const headerLabel = hasUser ? pair.user?.author ?? 'You' : 'Lumenta';
  const timestamp = pair.assistant?.timestamp ?? pair.user?.timestamp ?? '';

  return (
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
            {headerLabel}
          </Text>
          <Text size="xs" c="dimmed">
            {timestamp}
          </Text>
        </Group>

        {hasUser && (
          <Stack gap={2}>
            <Title order={4} c={conversationExchangeTitleColor}>
              {pair.user?.content}
            </Title>
          </Stack>
        )}

        {hasUser && <Divider />}

        {pair.assistant ? (
          <Stack gap="sm" data-testid="assistant-response">
            {(pair.assistant.blocks ?? []).map((block) => (
              <Box key={block.id}>{renderBlock(block, onQuickReply)}</Box>
            ))}
          </Stack>
        ) : (
          <AssistantPending />
        )}
      </Stack>
    </Paper>
  );
};
