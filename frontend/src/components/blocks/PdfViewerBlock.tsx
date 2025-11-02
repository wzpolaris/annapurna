import { useMemo, useState } from 'react';
import { Box, Button, Group, Paper, Stack, Text } from '@mantine/core';
import { Document, Page } from 'react-pdf';
import { pdfjs } from 'react-pdf';

import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js`;

interface PdfViewerBlockProps {
  fileUrl: string;
  filename?: string;
  fileSize?: string;
}

const MIN_SCALE = 0.5;
const MAX_SCALE = 3;
const SCALE_STEP = 0.25;

export const PdfViewerBlock = ({ fileUrl, filename, fileSize }: PdfViewerBlockProps) => {
  const [scale, setScale] = useState(1);
  const [numPages, setNumPages] = useState<number | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const displayName = useMemo(() => {
    if (!filename) {
      return fileSize ?? 'PDF document';
    }
    return fileSize ? `${filename} (${fileSize})` : filename;
  }, [filename, fileSize]);

  const onDocumentLoadSuccess = ({ numPages: pages }: { numPages: number }) => {
    setNumPages(pages);
    setLoadError(null);
  };

  return (
    <Stack gap="xs">
      <Group justify="space-between" align="center" wrap="wrap">
        <Stack gap={2}>
          <Text fw={600} size="sm">
            {displayName}
          </Text>
          {numPages ? (
            <Text size="xs" c="dimmed">
              {numPages} page{numPages === 1 ? '' : 's'}
            </Text>
          ) : null}
        </Stack>
        <Group gap="xs">
          <Button
            size="xs"
            variant="light"
            color="teal"
            disabled={scale <= MIN_SCALE}
            onClick={() => setScale((current) => Math.max(current - SCALE_STEP, MIN_SCALE))}
          >
            Zoom out
          </Button>
          <Button
            size="xs"
            variant="light"
            color="teal"
            disabled={scale >= MAX_SCALE}
            onClick={() => setScale((current) => Math.min(current + SCALE_STEP, MAX_SCALE))}
          >
            Zoom in
          </Button>
        </Group>
      </Group>

      <Paper withBorder radius="sm" p="sm">
        <Box style={{ overflow: 'auto', maxHeight: 600 }}>
          <Document
            file={fileUrl}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={(error) => setLoadError(error?.message ?? 'Unable to load PDF')}
            loading={
              <Text size="sm" c="dimmed">
                Loading PDF…
              </Text>
            }
          >
            <Page pageNumber={1} scale={scale} />
          </Document>
        </Box>
        {loadError ? (
          <Text size="xs" c="red" mt="xs">
            {loadError}
          </Text>
        ) : null}
      </Paper>
    </Stack>
  );
};
