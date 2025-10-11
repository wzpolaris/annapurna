import { Flex } from '@mantine/core';
import type { ReactNode } from 'react';

interface ConversationContainerProps {
  children: ReactNode;
}

export const ConversationContainer = ({ children }: ConversationContainerProps) => (
  <Flex
    direction="column"
    flex={1}
    gap="lg"
    maw={800}
    w="100%"
    mx="auto"
    style={{ minHeight: 0 }}
  >
    {children}
  </Flex>
);
