import { useState } from 'react';
import { TypographyStylesProvider } from '@mantine/core';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { DrawerPortal } from '../DrawerPortal';

interface MarkdownWithDrawersProps {
  content: string;
}

export const MarkdownWithDrawers = ({ content }: MarkdownWithDrawersProps) => {
  const [drawerState, setDrawerState] = useState<{
    opened: boolean;
    drawerId: string;
    linkText: string;
  } | null>(null);

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

      {/* Drawer portal */}
      <DrawerPortal
        isOpen={drawerState?.opened ?? false}
        drawerId={drawerState?.drawerId ?? ''}
        title={drawerState?.linkText ?? 'Details'}
        onClose={() => setDrawerState(null)}
      />
    </>
  );
};
