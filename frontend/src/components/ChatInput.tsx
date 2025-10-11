import { ActionIcon, Group, Paper, Textarea, Tooltip, rem } from '@mantine/core';
import { IconArrowUp } from '@tabler/icons-react';
import { useCallback } from 'react';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
}

export const ChatInput = ({ value, onChange, onSubmit, disabled }: ChatInputProps) => {
  const handleSubmit = useCallback(
    (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (!disabled) {
        onSubmit();
      }
    },
    [disabled, onSubmit]
  );

  return (
    <Paper
      component="form"
      onSubmit={handleSubmit}
      withBorder
      radius="xl"
      px="md"
      py="xs"
      shadow="sm"
    >
      <Group align="flex-end" gap="xs" wrap="nowrap">
        <Textarea
          aria-label="Send a message"
          placeholder="Ask a follow-up"
          variant="unstyled"
          autosize
          minRows={1}
          maxRows={4}
          value={value}
          onChange={(event) => onChange(event.currentTarget.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              if (!disabled && value.trim().length > 0) {
                onSubmit();
              }
            }
          }}
          style={{ flex: 1 }}
        />
        <Tooltip label="Send message" withArrow>
          <ActionIcon
            type="submit"
            radius="xl"
            size={rem(36)}
            color="teal"
            variant="filled"
            disabled={disabled || value.trim().length === 0}
          >
            <IconArrowUp size={20} stroke={1.5} />
          </ActionIcon>
        </Tooltip>
      </Group>
    </Paper>
  );
};
