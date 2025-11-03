import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Box,
  Button,
  Drawer,
  Group,
  Loader,
  ScrollArea,
  SegmentedControl,
  Stack,
  Text,
  Textarea
} from '@mantine/core';

import Pdf2pViewerBlock from './pdf2p/Pdf2pViewerBlock';
import type { DelimitedPreview, TextPreviewResult } from '../../utils/textPreview';
import { MAX_PREVIEW_CHARS, prepareTextPreview } from '../../utils/textPreview';

interface UploadBlockProps {
  content: string;
}

interface UploadBlockConfig {
  title: string;
  placeholder: string;
}

const DEFAULT_CONFIG: UploadBlockConfig = {
  title: 'Upload a file or paste data in the text area below',
  placeholder: 'Paste CSV or text data here'
};

const formatSize = (byteSize: number) => {
  if (Number.isNaN(byteSize)) {
    return '';
  }
  if (byteSize >= 1024 * 1024) {
    return `${(byteSize / (1024 * 1024)).toFixed(1)} MB`;
  }
  if (byteSize >= 1024) {
    return `${(byteSize / 1024).toFixed(1)} KB`;
  }
  return `${byteSize} B`;
};

export const UploadBlock = ({ content }: UploadBlockProps) => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [textValue, setTextValue] = useState('');
  const [selectedFileName, setSelectedFileName] = useState('');
  const [selectedFileSize, setSelectedFileSize] = useState('');
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isViewerOpen, setIsViewerOpen] = useState(false);
  const [isTextPreview, setIsTextPreview] = useState(false);
  const [previewText, setPreviewText] = useState<string | null>(null);
  const [isPreviewTruncated, setIsPreviewTruncated] = useState(false);
  const [tablePreview, setTablePreview] = useState<DelimitedPreview | null>(null);
  const [previewMode, setPreviewMode] = useState<'actual' | 'table'>('actual');
  const [drawerWidth, setDrawerWidth] = useState(66);
  const isDraggingResize = useRef(false);
  const [isHandleHover, setIsHandleHover] = useState(false);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const workerRef = useRef<Worker | null>(null);
  const workerRequestIdRef = useRef(0);
  const pendingWorkerRequestRef = useRef<number | null>(null);

  const config = useMemo<UploadBlockConfig>(() => {
    if (!content) {
      return DEFAULT_CONFIG;
    }
    try {
      const parsed = JSON.parse(content) as Partial<UploadBlockConfig>;
      return {
        title: parsed.title ?? DEFAULT_CONFIG.title,
        placeholder: parsed.placeholder ?? DEFAULT_CONFIG.placeholder
      };
    } catch {
      return DEFAULT_CONFIG;
    }
  }, [content]);

useEffect(() => {
  if (!tablePreview && previewMode === 'table') {
    setPreviewMode('actual');
  }
}, [tablePreview, previewMode]);

useEffect(() => {
  const handlePointerMove = (event: PointerEvent) => {
    if (!isDraggingResize.current) {
      return;
    }
    const viewportWidth = window.innerWidth || 1;
    const distanceFromRight = Math.max(0, viewportWidth - event.clientX);
    const percent = Math.min(Math.max((distanceFromRight / viewportWidth) * 100, 30), 90);
    setDrawerWidth(percent);
    document.body.style.cursor = 'col-resize';
  };

  const handlePointerUp = () => {
    if (isDraggingResize.current) {
      isDraggingResize.current = false;
      document.body.style.cursor = '';
      setIsHandleHover(false);
    }
  };

  window.addEventListener('pointermove', handlePointerMove);
  window.addEventListener('pointerup', handlePointerUp);

  return () => {
    window.removeEventListener('pointermove', handlePointerMove);
    window.removeEventListener('pointerup', handlePointerUp);
    if (isDraggingResize.current) {
      isDraggingResize.current = false;
    }
    document.body.style.cursor = '';
    setIsHandleHover(false);
  };
}, []);

const handleResizeStart: React.PointerEventHandler<HTMLDivElement> = (event) => {
  event.preventDefault();
  event.stopPropagation();
  isDraggingResize.current = true;
  document.body.style.cursor = 'col-resize';
  setIsHandleHover(true);
};

const handleBrowseClick = () => {
  fileInputRef.current?.click();
};

const resetStates = () => {
  setPdfUrl(null);
  setTextValue('');
  setIsViewerOpen(false);
  setIsTextPreview(false);
  setPreviewText(null);
  setIsPreviewTruncated(false);
  setTablePreview(null);
  setPreviewMode('actual');
  setIsPreviewLoading(false);
  pendingWorkerRequestRef.current = null;
};

const applyPreviewResult = useCallback((previewPayload: TextPreviewResult) => {
  setTextValue('');
  setPdfUrl(null);
  setIsTextPreview(true);
  setPreviewText(previewPayload.truncatedText);
  setIsPreviewTruncated(previewPayload.truncated);
  setTablePreview(previewPayload.tablePreview);
  setPreviewMode('actual');
  setErrorMessage(null);
}, []);

const handlePreviewFailure = useCallback((message?: string) => {
  setIsTextPreview(false);
  setPreviewText(null);
  setIsPreviewTruncated(false);
  setTablePreview(null);
  setPreviewMode('actual');
  if (message) {
    setErrorMessage(message);
  } else {
    setErrorMessage('Preview not available for this file type.');
  }
}, []);

const processBufferSynchronously = useCallback(
  (buffer: ArrayBuffer) => {
    try {
      const decoder = new TextDecoder('utf-8', { fatal: true });
      const decoded = decoder.decode(new Uint8Array(buffer));
      const previewPayload = prepareTextPreview(decoded);
      applyPreviewResult(previewPayload);
    } catch (error) {
      console.error('Failed to prepare preview synchronously', error);
      handlePreviewFailure();
    } finally {
      setIsPreviewLoading(false);
    }
  },
  [applyPreviewResult, handlePreviewFailure]
);

useEffect(() => {
  if (typeof window === 'undefined') {
    return;
  }

  const worker = new Worker(new URL('../../workers/textPreviewWorker.ts', import.meta.url), {
    type: 'module'
  });
  workerRef.current = worker;

  type WorkerResponse =
    | { id: number; ok: true; preview: TextPreviewResult }
    | { id: number; ok: false; error?: string };

  const handleMessage = (event: MessageEvent<WorkerResponse>) => {
    const data = event.data;
    if (pendingWorkerRequestRef.current !== data.id) {
      return;
    }
    pendingWorkerRequestRef.current = null;
    setIsPreviewLoading(false);
    if (data.ok) {
      applyPreviewResult(data.preview);
    } else {
      handlePreviewFailure(data.error);
    }
  };

  const handleError = () => {
    if (pendingWorkerRequestRef.current !== null) {
      pendingWorkerRequestRef.current = null;
      setIsPreviewLoading(false);
      handlePreviewFailure('Preview worker failed to process the file.');
    }
  };

  worker.onmessage = handleMessage;
  worker.onerror = handleError;

  return () => {
    worker.onmessage = null;
    worker.onerror = null;
    worker.terminate();
    workerRef.current = null;
  };
}, [applyPreviewResult, handlePreviewFailure]);

const handleFileChange: React.ChangeEventHandler<HTMLInputElement> = (event) => {
  const { files } = event.target;
  const file = files?.[0];
  if (!file) {
    setSelectedFileName('');
    setSelectedFileSize('');
    setErrorMessage(null);
    resetStates();
    event.target.value = '';
    return;
  }

  setSelectedFileName(file.name);
  setSelectedFileSize(formatSize(file.size));
  setErrorMessage(null);

  const reader = new FileReader();

  reader.onerror = () => {
    setErrorMessage('Unable to read file.');
    setIsPreviewLoading(false);
    resetStates();
  };

  if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
    reader.onload = () => {
      const result = reader.result;
        if (typeof result === 'string') {
          setPdfUrl(result);
          setTextValue('');
          setIsTextPreview(false);
          setPreviewText(null);
          setIsPreviewTruncated(false);
          setTablePreview(null);
          setPreviewMode('actual');
          setErrorMessage(null);
          setIsPreviewLoading(false);
        } else {
          setErrorMessage('Unable to read PDF contents.');
          resetStates();
        }
    };
    reader.readAsDataURL(file);
    return;
  }

  reader.onload = () => {
    const result = reader.result;
    if (!(result instanceof ArrayBuffer)) {
      setErrorMessage('Unable to read file contents.');
      resetStates();
      return;
    }
    const worker = workerRef.current;
    if (worker) {
      setIsPreviewLoading(true);
      const requestId = workerRequestIdRef.current + 1;
      workerRequestIdRef.current = requestId;
      pendingWorkerRequestRef.current = requestId;
      worker.postMessage({ id: requestId, buffer: result }, [result]);
      return;
    }

    setIsPreviewLoading(true);
    processBufferSynchronously(result);
  };
  reader.readAsArrayBuffer(file);
  event.target.value = '';
};

  return (
    <Stack gap="md">
      <Group justify="space-between" align="flex-start" wrap="wrap" gap="sm">
        <Stack gap={4} style={{ flex: 1, minWidth: 0 }}>
          <Text fw={600}>{config.title}</Text>
          {selectedFileName ? (
            <Group gap="xs" align="center" wrap="nowrap" justify="flex-start">
              <Text size="xs" c="dark.7" truncate>
                {selectedFileSize ? `${selectedFileName} (${selectedFileSize})` : selectedFileName}
              </Text>
              {(pdfUrl || (isTextPreview && previewText)) ? (
                <Button
                  size="xs"
                  variant="subtle"
                  color="teal"
                  onClick={() => {
                    setPreviewMode('actual');
                    setIsViewerOpen(true);
                  }}
                >
                  View
                </Button>
              ) : null}
            </Group>
          ) : null}
        </Stack>
        <Button
          size="xs"
          variant="light"
          color="teal"
          onClick={handleBrowseClick}
        >
          Upload file
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.txt,.pdf,text/csv,text/plain,application/pdf"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
      </Group>

      <Textarea
        value={textValue}
        onChange={(event) => setTextValue(event.currentTarget.value)}
        minRows={8}
        placeholder={config.placeholder}
        autosize={false}
        styles={{
          input: {
            resize: 'none'
          }
        }}
      />

      {errorMessage ? (
        <Text size="xs" c="red">
          {errorMessage}
        </Text>
      ) : null}

      <Drawer
        opened={isViewerOpen}
        onClose={() => {
          setIsViewerOpen(false);
          setPreviewMode('actual');
          if (isDraggingResize.current) {
            isDraggingResize.current = false;
          }
          document.body.style.cursor = '';
          setIsHandleHover(false);
        }}
        title={selectedFileName || 'File preview'}
        position="right"
        size={`${drawerWidth}%`}
        padding="md"
        styles={{
          content: {
            display: 'flex',
            flexDirection: 'column',
            position: 'relative'
          },
          body: {
            flex: 1,
            display: 'flex',
            padding: 'var(--mantine-spacing-md)'
          }
        }}
      >
        <Box
          onPointerDown={handleResizeStart}
          onPointerEnter={() => setIsHandleHover(true)}
          onPointerLeave={() => {
            if (!isDraggingResize.current) {
              setIsHandleHover(false);
            }
          }}
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            bottom: 0,
            width: '12px',
            cursor: 'col-resize',
            zIndex: 10,
            background: isHandleHover || isDraggingResize.current ? 'rgba(37, 99, 235, 0.1)' : 'transparent',
            transition: 'background 120ms ease'
          }}
        />
        {pdfUrl ? (
          <Box style={{ flex: 1, height: '100%', minHeight: 0 }}>
            <Pdf2pViewerBlock
              fileUrl={pdfUrl}
              filename={selectedFileName || undefined}
              fileSize={selectedFileSize || undefined}
            />
          </Box>
        ) : isPreviewLoading ? (
          <Stack style={{ flex: 1 }} justify="center" align="center" gap="sm">
            <Loader color="teal" size="md" variant="dots" />
            <Text size="sm" c="dimmed">
              Preparing preview…
            </Text>
          </Stack>
        ) : isTextPreview && previewText ? (
          <Stack gap="sm" style={{ flex: 1, width: '100%', minHeight: 0 }}>
            {tablePreview ? (
              <Group justify="space-between" align="center" wrap="wrap">
                <SegmentedControl
                  value={previewMode}
                  onChange={(value) => setPreviewMode(value as 'actual' | 'table')}
                  data={[
                    { label: 'Actual', value: 'actual' },
                    { label: 'Table', value: 'table' }
                  ]}
                  size="xs"
                />
                <Text size="xs" c="dimmed">
                  {tablePreview.delimiterLabel}-delimited preview
                </Text>
              </Group>
            ) : null}

            {previewMode === 'table' && tablePreview ? (
              <ScrollArea style={{ flex: 1, width: '100%', minHeight: 0 }} offsetScrollbars>
                <Box
                  component="table"
                  style={{
                    width: '100%',
                    borderCollapse: 'collapse',
                    fontSize: '0.875rem'
                  }}
                >
                  <thead>
                    <tr>
                      {tablePreview.headers.map((header, index) => (
                        <Box
                          component="th"
                          key={`header-${index}`}
                          style={{
                            textAlign: 'left',
                            padding: '0.5rem 0.75rem',
                            borderBottom: '1px solid rgba(148, 163, 184, 0.6)',
                            position: 'sticky',
                            top: 0,
                            backgroundColor: 'var(--mantine-color-body, #ffffff)',
                            fontWeight: 600,
                            zIndex: 1
                          }}
                        >
                          {header || `Column ${index + 1}`}
                        </Box>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {tablePreview.rows.map((row, rowIndex) => (
                      <tr key={`row-${rowIndex}`}>
                        {row.map((cell, cellIndex) => (
                          <Box
                            component="td"
                            key={`cell-${rowIndex}-${cellIndex}`}
                            style={{
                              padding: '0.45rem 0.75rem',
                              borderBottom: '1px solid rgba(226, 232, 240, 0.8)',
                              fontFamily: 'Menlo, Consolas, "Courier New", monospace',
                              whiteSpace: 'nowrap',
                              textOverflow: 'ellipsis',
                              overflow: 'hidden',
                              maxWidth: 320
                            }}
                            title={cell}
                          >
                            {cell}
                          </Box>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </Box>
              </ScrollArea>
            ) : (
              <ScrollArea style={{ flex: 1, width: '100%', minHeight: 0 }} offsetScrollbars>
                <Box
                  component="pre"
                  style={{
                    margin: 0,
                    whiteSpace: 'pre-wrap',
                    fontFamily: 'Menlo, Consolas, "Courier New", monospace',
                    fontSize: '0.875rem',
                    lineHeight: 1.5,
                    paddingRight: '0.5rem'
                  }}
                >
                  {previewText}
                </Box>
              </ScrollArea>
            )}

            {tablePreview ? (
              <Text size="xs" c="dimmed">
                Showing up to {tablePreview.rows.length} rows.
              </Text>
            ) : null}
            {isPreviewTruncated ? (
              <Text size="xs" c="dimmed">
                Preview truncated to the first {MAX_PREVIEW_CHARS.toLocaleString()} characters.
              </Text>
            ) : null}
          </Stack>
        ) : (
          <Stack style={{ flex: 1 }} justify="center" align="center">
            <Text size="sm" c="dimmed">
              Preview unavailable for this file type.
            </Text>
          </Stack>
        )}
      </Drawer>
    </Stack>
  );
};
