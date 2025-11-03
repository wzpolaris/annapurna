import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Box,
  Button,
  Drawer,
  Group,
  ScrollArea,
  SegmentedControl,
  Stack,
  Text,
  Textarea
} from '@mantine/core';

import Pdf2pViewerBlock from './pdf2p/Pdf2pViewerBlock';

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

const DELIMITER_CANDIDATES = [
  { char: ',', label: 'Comma' },
  { char: '\t', label: 'Tab' },
  { char: ';', label: 'Semicolon' },
  { char: '|', label: 'Pipe' }
] as const;

const MAX_PREVIEW_ROWS = 150;
const MAX_PREVIEW_COLUMNS = 24;
const MAX_PREVIEW_CHARS = 200_000;
const MAX_CELL_LENGTH = 200;

interface DelimitedPreview {
  headers: string[];
  rows: string[][];
  delimiterLabel: string;
}

const truncateCell = (value: string) => {
  if (value.length <= MAX_CELL_LENGTH) {
    return value;
  }
  return `${value.slice(0, MAX_CELL_LENGTH - 1)}…`;
};

const splitDelimitedLine = (line: string, delimiter: string): string[] => {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"') {
      const next = line[i + 1];
      if (inQuotes && next === '"') {
        current += '"';
        i += 1;
        continue;
      }
      inQuotes = !inQuotes;
      continue;
    }

    if (char === delimiter && !inQuotes) {
      result.push(truncateCell(current.trim()));
      current = '';
      continue;
    }

    current += char;
  }

  result.push(truncateCell(current.trim()));
  return result;
};

const analyzeDelimitedText = (text: string): DelimitedPreview | null => {
  if (!text) {
    return null;
  }

  const sample = text.slice(0, MAX_PREVIEW_CHARS);
  const lines = sample
    .split(/\r?\n/)
    .map((line) => line.trimEnd())
    .filter((line) => line.length > 0);

  if (lines.length < 2) {
    return null;
  }

  const limitedLines = lines.slice(0, MAX_PREVIEW_ROWS + 1);
  const majorityThreshold = Math.max(2, Math.floor(limitedLines.length * 0.6));

  for (const candidate of DELIMITER_CANDIDATES) {
    const parsed = limitedLines.map((line) => splitDelimitedLine(line, candidate.char));
    const columnCounts = parsed.map((row) => row.length);
    const firstCount = columnCounts[0];

    if (firstCount <= 1 || firstCount > MAX_PREVIEW_COLUMNS) {
      continue;
    }

    const consistent = columnCounts.filter((count) => count === firstCount).length;
    if (consistent < majorityThreshold) {
      continue;
    }

    const [headerRow, ...rows] = parsed;
    return {
      headers: headerRow,
      rows: rows.slice(0, MAX_PREVIEW_ROWS).map((row) => {
        if (row.length === firstCount) {
          return row;
        }
        const adjusted = [...row];
        while (adjusted.length < firstCount) {
          adjusted.push('');
        }
        return adjusted.slice(0, firstCount);
      }),
      delimiterLabel: candidate.label
    };
  }

  return null;
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
  };

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
      try {
        const decoder = new TextDecoder('utf-8', { fatal: true });
        const decoded = decoder.decode(new Uint8Array(result));
        setTextValue('');
        setPdfUrl(null);
        setIsTextPreview(true);
        const isTruncated = decoded.length > MAX_PREVIEW_CHARS;
        const truncated = isTruncated ? `${decoded.slice(0, MAX_PREVIEW_CHARS)}\n…` : decoded;
        setPreviewText(truncated);
        setIsPreviewTruncated(isTruncated);
        const analysis = analyzeDelimitedText(decoded);
        setTablePreview(analysis);
        setPreviewMode('actual');
        setErrorMessage(null);
      } catch {
        setErrorMessage('Preview not available for this file type.');
        setTextValue('');
        setPdfUrl(null);
        setIsTextPreview(false);
        setPreviewText(null);
        setIsPreviewTruncated(false);
        setTablePreview(null);
        setPreviewMode('actual');
      }
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
        }}
        title={selectedFileName || 'File preview'}
        position="right"
        size="66%"
        padding="md"
        styles={{
          content: {
            display: 'flex',
            flexDirection: 'column'
          },
          body: {
            flex: 1,
            display: 'flex',
            padding: 'var(--mantine-spacing-md)'
          }
        }}
      >
        {pdfUrl ? (
          <Box style={{ flex: 1, height: '100%', minHeight: 0 }}>
            <Pdf2pViewerBlock
              fileUrl={pdfUrl}
              filename={selectedFileName || undefined}
              fileSize={selectedFileSize || undefined}
            />
          </Box>
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
