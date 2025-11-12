import { useState, useCallback } from 'react';
import { Portal, Text, ActionIcon, Group, Box, TypographyStylesProvider } from '@mantine/core';
import { IconX } from '@tabler/icons-react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { getDrawerWidth, setDrawerWidth } from '../../utils/drawerWidth';

interface MarkdownWithDrawersProps {
  content: string;
}

const MIN_DRAWER_WIDTH = 30; // 30% of screen
const MAX_DRAWER_WIDTH = 70; // 70% of screen

export const MarkdownWithDrawers = ({ content }: MarkdownWithDrawersProps) => {
  const [drawerState, setDrawerState] = useState<{
    opened: boolean;
    drawerId: string;
    linkText: string;
  } | null>(null);

  const handlePanelLayout = useCallback((sizes: number[]) => {
    const rightPanelSize = sizes[1];
    if (typeof rightPanelSize === 'number') {
      setDrawerWidth(rightPanelSize);
    }
  }, []);

  return (
    <>
      <TypographyStylesProvider>
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[rehypeKatex]}
          components={{
            a: ({ href, children, ...props }) => {
              // Intercept drawer links
              if (href?.startsWith('?drawer=')) {
                const drawerId = href.replace('?drawer=', '');
                return (
                  <span
                    style={{
                      textDecoration: 'underline',
                      textDecorationStyle: 'dotted',
                      textDecorationColor: '#868e96',
                      textUnderlineOffset: '2px',
                      cursor: 'pointer',
                      color: 'inherit',
                    }}
                    onClick={() =>
                      setDrawerState({
                        opened: true,
                        drawerId,
                        linkText: String(children),
                      })
                    }
                  >
                    {children}
                  </span>
                );
              }
              // Regular link - unchanged
              return (
                <a href={href} {...props}>
                  {children}
                </a>
              );
            },
          }}
        >
          {content}
        </ReactMarkdown>
      </TypographyStylesProvider>

      {/* Resizable drawer portal */}
      {drawerState?.opened && (
        <Portal>
          <Box
            onClick={() => setDrawerState(null)}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 2000,
              backgroundColor: 'rgba(15, 23, 42, 0.1)',
            }}
          >
            <Box
              style={{ height: '100%', width: '100%' }}
              onClick={(event) => event.stopPropagation()}
            >
              <PanelGroup
                direction="horizontal"
                style={{ width: '100%', height: '100%' }}
                onLayout={handlePanelLayout}
              >
                {/* Left panel - transparent (click handled by outer Box) */}
                <Panel
                  minSize={100 - MAX_DRAWER_WIDTH}
                  maxSize={100 - MIN_DRAWER_WIDTH}
                  order={1}
                >
                  <Box style={{ width: '100%', height: '100%' }} />
                </Panel>

                {/* Resize handle */}
                <PanelResizeHandle
                  style={{
                    width: '16px',
                    marginLeft: '-8px',
                    marginRight: '-8px',
                    cursor: 'col-resize',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 1,
                  }}
                >
                  <Box
                    style={{
                      width: '3px',
                      height: '48px',
                      borderRadius: '999px',
                      backgroundColor: 'rgba(148, 163, 184, 0.8)',
                    }}
                  />
                </PanelResizeHandle>

                {/* Right panel - drawer content */}
                <Panel
                  minSize={MIN_DRAWER_WIDTH}
                  maxSize={MAX_DRAWER_WIDTH}
                  defaultSize={getDrawerWidth()}
                  order={2}
                >
                  <Box
                    style={{
                      height: '100%',
                      width: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      backgroundColor: '#ffffff',
                      boxShadow: '0 24px 48px rgba(15, 23, 42, 0.28)',
                      borderLeft: '1px solid rgba(226, 232, 240, 0.65)',
                    }}
                  >
                    {/* Header */}
                    <Group
                      justify="space-between"
                      p="md"
                      style={{
                        borderBottom: '1px solid #e9ecef',
                        flexShrink: 0,
                      }}
                    >
                      <Text fw={600} size="lg">
                        {drawerState?.linkText || 'Details'}
                      </Text>
                      <ActionIcon
                        variant="subtle"
                        color="gray"
                        onClick={() => setDrawerState(null)}
                      >
                        <IconX size={18} />
                      </ActionIcon>
                    </Group>

                    {/* iframe content */}
                    <Box style={{ flex: 1, overflow: 'hidden' }}>
                      <iframe
                        src={`http://localhost:8000/drawers/${drawerState.drawerId}.html`}
                        style={{
                          width: '100%',
                          height: '100%',
                          border: 'none',
                        }}
                        title={drawerState.linkText}
                        onError={(e) => {
                          console.warn(`Drawer not found: ${drawerState.drawerId}`);
                        }}
                      />
                    </Box>
                  </Box>
                </Panel>
              </PanelGroup>
            </Box>
          </Box>
        </Portal>
      )}
    </>
  );
};
