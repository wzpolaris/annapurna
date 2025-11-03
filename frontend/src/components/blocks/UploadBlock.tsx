import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActionIcon,
  Box,
  Button,
  Group,
  Loader,
  Portal,
  ScrollArea,
  SegmentedControl,
  Stack,
  Text,
  Textarea
} from '@mantine/core';
import { IconX } from '@tabler/icons-react';
import { Panel, PanelGroup, PanelResizeHandle, type ImperativePanelHandle } from 'react-resizable-panels';

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

type UploadStatus = 'loading' | 'ready' | 'error';

type UploadType = 'pdf' | 'text';

interface UploadEntry {
  id: string;
  name: string;
  sizeLabel: string;
  status: UploadStatus;
  type?: UploadType;
  pdfUrl?: string;
  previewText?: string;
  truncated?: boolean;
  tablePreview?: DelimitedPreview | null;
  error?: string;
}

const DEFAULT_CONFIG: UploadBlockConfig = {
  title: 'Upload a file or paste data in the text area below',
  placeholder: 'Paste CSV or text data here'
};

const DEFAULT_DRAWER_WIDTH = 66;
const MIN_DRAWER_WIDTH = 32;
const MAX_DRAWER_WIDTH = 92;

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

const createUploadId = () => `upload-${Date.now().toString(36)}-${Math.random().toString(16).slice(2, 8)}`;

export const UploadBlock = ({ content }: UploadBlockProps) => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [textValue, setTextValue] = useState('');
  const [isViewerOpen, setIsViewerOpen] = useState(false);
  const [uploads, setUploads] = useState<UploadEntry[]>([]);
  const [activeUploadId, setActiveUploadId] = useState<string | null>(null);
  const [previewMode, setPreviewMode] = useState<'actual' | 'table'>('actual');
  const [drawerWidth, setDrawerWidth] = useState<number>(DEFAULT_DRAWER_WIDTH);
  const workerRef = useRef<Worker | null>(null);
  const workerRequestIdRef = useRef(0);
  const pendingWorkerRequestsRef = useRef<Map<number, string>>(new Map());
  const previewPanelRef = useRef<ImperativePanelHandle | null>(null);

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

  const activeUpload = useMemo(
    () => (activeUploadId ? uploads.find((entry) => entry.id === activeUploadId) ?? null : null),
    [uploads, activeUploadId]
  );

  const activeStatus = activeUpload?.status ?? 'ready';
  const activePdfUrl = activeUpload?.type === 'pdf' ? activeUpload.pdfUrl ?? null : null;
  const activePreviewText = activeUpload?.type === 'text' ? activeUpload.previewText ?? null : null;
  const activeTablePreview = activeUpload?.type === 'text' ? activeUpload.tablePreview ?? null : null;
  const activeTruncated = activeUpload?.type === 'text' ? Boolean(activeUpload.truncated) : false;

  useEffect(() => {
    if (!activeTablePreview && previewMode === 'table') {
      setPreviewMode('actual');
    }
  }, [activeTablePreview, previewMode]);

  const updateUploadEntry = useCallback((uploadId: string, partial: Partial<UploadEntry>) => {
    setUploads((prev) =>
      prev.map((entry) => (entry.id === uploadId ? { ...entry, ...partial } : entry))
    );
  }, []);

  const applyPreviewResult = useCallback(
    (uploadId: string, previewPayload: TextPreviewResult) => {
      updateUploadEntry(uploadId, {
        status: 'ready',
        type: 'text',
        previewText: previewPayload.truncatedText,
        truncated: previewPayload.truncated,
        tablePreview: previewPayload.tablePreview,
        error: undefined
      });
      setActiveUploadId(uploadId);
      setPreviewMode('actual');
    },
    [updateUploadEntry]
  );

  const handlePreviewFailure = useCallback(
    (uploadId: string, message?: string) => {
      updateUploadEntry(uploadId, {
        status: 'error',
        type: undefined,
        pdfUrl: undefined,
        previewText: undefined,
        tablePreview: null,
        truncated: false,
        error: message ?? 'Preview not available for this file type.'
      });
    },
    [updateUploadEntry]
  );

  const processBufferSynchronously = useCallback(
    (uploadId: string, buffer: ArrayBuffer) => {
      try {
        const decoder = new TextDecoder('utf-8', { fatal: true });
        const decoded = decoder.decode(new Uint8Array(buffer));
        applyPreviewResult(uploadId, prepareTextPreview(decoded));
      } catch (error) {
        console.error('Failed to prepare preview synchronously', error);
        handlePreviewFailure(uploadId);
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

    worker.onmessage = (event: MessageEvent<WorkerResponse>) => {
      const data = event.data;
      const uploadId = pendingWorkerRequestsRef.current.get(data.id);
      if (!uploadId) {
        return;
      }
      pendingWorkerRequestsRef.current.delete(data.id);
      if (data.ok) {
        applyPreviewResult(uploadId, data.preview);
      } else {
        handlePreviewFailure(uploadId, data.error);
      }
    };

    worker.onerror = () => {
      if (pendingWorkerRequestsRef.current.size === 0) {
        return;
      }
      for (const uploadId of pendingWorkerRequestsRef.current.values()) {
        handlePreviewFailure(uploadId, 'Preview worker failed to process the file.');
      }
      pendingWorkerRequestsRef.current.clear();
    };

    return () => {
      worker.onmessage = null;
      worker.onerror = null;
      worker.terminate();
      workerRef.current = null;
      pendingWorkerRequestsRef.current.clear();
    };
  }, [applyPreviewResult, handlePreviewFailure]);

  useEffect(() => {
    if (!isViewerOpen) {
      return;
    }
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isViewerOpen]);

  const handlePanelLayout = useCallback((sizes: number[]) => {
    const nextRight = sizes[1];
    if (typeof nextRight !== 'number') {
      return;
    }
    const clamped = Math.min(Math.max(nextRight, MIN_DRAWER_WIDTH), MAX_DRAWER_WIDTH);
    setDrawerWidth((prev) => (Math.abs(prev - clamped) < 0.1 ? prev : clamped));
  }, []);

  const handleDefaultWidth = useCallback(() => {
    setDrawerWidth(DEFAULT_DRAWER_WIDTH);
    previewPanelRef.current?.resize(DEFAULT_DRAWER_WIDTH);
  }, []);

  useEffect(() => {
    if (!isViewerOpen) {
      return;
    }
    const panel = previewPanelRef.current;
    if (!panel) {
      return;
    }
    const frame = requestAnimationFrame(() => {
      panel.resize(drawerWidth);
    });
    return () => cancelAnimationFrame(frame);
  }, [isViewerOpen, drawerWidth]);

  const handleCloseViewer = useCallback(() => {
    setIsViewerOpen(false);
  }, []);

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const processFile = useCallback(
    (file: File) => {
      const uploadId = createUploadId();
      const sizeLabel = formatSize(file.size);
      const newEntry: UploadEntry = {
        id: uploadId,
        name: file.name,
        sizeLabel,
        status: 'loading',
        tablePreview: null
      };
      setUploads((prev) => [...prev, newEntry]);

      const reader = new FileReader();

      reader.onerror = () => {
        handlePreviewFailure(uploadId, 'Unable to read file.');
      };

      if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
        reader.onload = () => {
          const result = reader.result;
          if (typeof result === 'string') {
            updateUploadEntry(uploadId, {
              status: 'ready',
              type: 'pdf',
              pdfUrl: result,
              error: undefined
            });
            setActiveUploadId(uploadId);
            setPreviewMode('actual');
          } else {
            handlePreviewFailure(uploadId, 'Unable to read PDF contents.');
          }
        };
        reader.readAsDataURL(file);
        return;
      }

      reader.onload = () => {
        const result = reader.result;
        if (!(result instanceof ArrayBuffer)) {
          handlePreviewFailure(uploadId, 'Unable to read file contents.');
          return;
        }
        const worker = workerRef.current;
        if (worker) {
          const requestId = workerRequestIdRef.current + 1;
          workerRequestIdRef.current = requestId;
          pendingWorkerRequestsRef.current.set(requestId, uploadId);
          worker.postMessage({ id: requestId, buffer: result }, [result]);
          return;
        }
        processBufferSynchronously(uploadId, result);
      };
      reader.readAsArrayBuffer(file);
    },
    [handlePreviewFailure, processBufferSynchronously, updateUploadEntry]
  );

  const handleFileChange: React.ChangeEventHandler<HTMLInputElement> = (event) => {
    const { files } = event.target;
    if (files && files.length > 0) {
      Array.from(files).forEach(processFile);
    }
    event.target.value = '';
  };

  const isDefaultWidth = Math.abs(drawerWidth - DEFAULT_DRAWER_WIDTH) < 0.5;

  return (
    <Stack gap="md">
      <Group justify="space-between" align="flex-start" wrap="wrap" gap="sm">
        <Stack gap={4} style={{ flex: 1, minWidth: 0 }}>
          <Text fw={600}>{config.title}</Text>
          {uploads.length > 0 ? (
            <Stack gap="xs">
              {uploads.map((entry) => (
                <Stack key={entry.id} gap={2}>
                  <Group align="center" gap="xs" wrap="nowrap">
                    {entry.status === 'loading' ? (
                      <Loader size="xs" color="teal" />
                    ) : (
                      <Button
                        size="xs"
                        variant="subtle"
                        color="teal"
                        disabled={entry.status !== 'ready'}
                        onClick={() => {
                          setActiveUploadId(entry.id);
                          setPreviewMode('actual');
                          setIsViewerOpen(true);
                        }}
                      >
                        View
                      </Button>
                    )}
                    <Text
                      size="xs"
                      c="dark.7"
                      style={{ flex: 1, minWidth: 0 }}
                      truncate
                    >
                      {entry.name}
                      {entry.sizeLabel ? ` (${entry.sizeLabel})` : ''}
                    </Text>
                  </Group>
                  {entry.status === 'error' ? (
                    <Text size="xs" c="red" pl="md">
                      {entry.error ?? 'Preview failed.'}
                    </Text>
                  ) : null}
                </Stack>
              ))}
            </Stack>
          ) : (
            <Text size="xs" c="dimmed">
              No uploads yet.
            </Text>
          )}
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
          multiple
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
      {isViewerOpen && (
        <Portal>
          <Box
            onClick={handleCloseViewer}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 2000,
              backgroundColor: 'rgba(15, 23, 42, 0.1)'
            }}
          >
            <Box
              style={{ height: '100%', width: '100%' }}
              onClick={(event) => event.stopPropagation()}
            >
              <PanelGroup
                direction="horizontal"
                onLayout={handlePanelLayout}
                style={{ width: '100%', height: '100%' }}
              >
                <Panel
                  minSize={100 - MAX_DRAWER_WIDTH}
                  maxSize={100 - MIN_DRAWER_WIDTH}
                  order={1}
                >
                  <Box style={{ width: '100%', height: '100%' }} />
                </Panel>
                <PanelResizeHandle
                  style={{
                    width: '16px',
                    marginLeft: '-8px',
                    marginRight: '-8px',
                    cursor: 'col-resize',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <Box
                    style={{
                      width: '3px',
                      height: '48px',
                      borderRadius: '999px',
                      backgroundColor: 'rgba(148, 163, 184, 0.8)'
                    }}
                  />
                </PanelResizeHandle>
                <Panel
                  ref={previewPanelRef}
                  minSize={MIN_DRAWER_WIDTH}
                  maxSize={MAX_DRAWER_WIDTH}
                  order={2}
                  defaultSize={drawerWidth}
                >
                  <Box
                    style={{
                      height: '100%',
                      width: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      backgroundColor: '#ffffff',
                      boxShadow: '0 24px 48px rgba(15, 23, 42, 0.28)',
                      borderLeft: '1px solid rgba(226, 232, 240, 0.65)'
                    }}
                  >
                    <Box
                      style={{
                        padding: 'var(--mantine-spacing-md)',
                        borderBottom: '1px solid rgba(226, 232, 240, 0.7)'
                      }}
                    >
                      <Group justify="space-between" align="center">
                        <Text fw={600}>
                          {activeUpload?.name ?? 'File preview'}
                        </Text>
                        <Group gap="xs">
                          <Button
                            size="xs"
                            variant="light"
                            color="gray"
                            onClick={handleDefaultWidth}
                            disabled={isDefaultWidth}
                          >
                            Default width
                          </Button>
                          <ActionIcon
                            size="sm"
                            variant="subtle"
                            color="gray"
                            aria-label="Close preview"
                            onClick={handleCloseViewer}
                          >
                            <IconX size={16} />
                          </ActionIcon>
                        </Group>
                      </Group>
                    </Box>
                    <Box
                      style={{
                        flex: 1,
                        padding: 'var(--mantine-spacing-md)',
                        display: 'flex',
                        minHeight: 0,
                        overflow: 'hidden'
                      }}
                    >
                      {activeStatus === 'loading' ? (
                        <Stack style={{ flex: 1 }} justify="center" align="center" gap="sm">
                          <Loader color="teal" size="md" variant="dots" />
                          <Text size="sm" c="dimmed">
                            Preparing preview…
                          </Text>
                        </Stack>
                      ) : activeStatus === 'error' ? (
                        <Stack style={{ flex: 1 }} justify="center" align="center">
                          <Text size="sm" c="red">
                            {activeUpload?.error ?? 'Preview unavailable.'}
                          </Text>
                        </Stack>
                      ) : activeUpload && activeUpload.type === 'pdf' && activePdfUrl ? (
                        <Box style={{ flex: 1, minHeight: 0 }}>
                          <Pdf2pViewerBlock
                            fileUrl={activePdfUrl}
                            filename={activeUpload.name}
                            fileSize={activeUpload.sizeLabel}
                          />
                        </Box>
                      ) : activeUpload && activeUpload.type === 'text' && activePreviewText ? (
                        <Stack gap="sm" style={{ flex: 1, minHeight: 0 }}>
                          {activeTablePreview ? (
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
                                {activeTablePreview.delimiterLabel}-delimited preview
                              </Text>
                            </Group>
                          ) : null}

                          {previewMode === 'table' && activeTablePreview ? (
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
                                    {activeTablePreview.headers.map((header, index) => (
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
                                  {activeTablePreview.rows.map((row, rowIndex) => (
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
                                {activePreviewText}
                              </Box>
                            </ScrollArea>
                          )}

                          {activeTablePreview ? (
                            <Text size="xs" c="dimmed">
                              Showing up to {activeTablePreview.rows.length} rows.
                            </Text>
                          ) : null}
                          {activeTruncated ? (
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
                    </Box>
                  </Box>
                </Panel>
              </PanelGroup>
            </Box>
          </Box>
        </Portal>
      )}
    </Stack>
  );
};
