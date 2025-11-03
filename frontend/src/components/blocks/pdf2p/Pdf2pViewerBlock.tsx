import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Box, Loader, Paper, Stack, Text } from '@mantine/core';

import PdfJsSinglePage, { type PdfJsSinglePageHandle } from './PdfJsSinglePage';

import './Pdf2pViewerBlock.css';

const MIN_SCALE = 0.5;
const MAX_SCALE = 3;
const SCALE_STEP = 0.25;

interface Pdf2pViewerBlockProps {
  fileUrl: string;
  filename?: string;
  fileSize?: string;
}

const clampPercent = (value: number) => Math.min(Math.max(value, 10), 400);

export const Pdf2pViewerBlock = ({ fileUrl, filename, fileSize }: Pdf2pViewerBlockProps) => {
  const viewerRef = useRef<PdfJsSinglePageHandle | null>(null);
  const [fileBlob, setFileBlob] = useState<File | Blob | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [scale, setScale] = useState(1.25);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [scaleInput, setScaleInput] = useState('125');
  const [pageInput, setPageInput] = useState('1');

  useEffect(() => {
    if (!fileUrl) {
      setFileBlob(null);
      setError('No document provided.');
      return;
    }

    const controller = new AbortController();
    let cancelled = false;

    const load = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(fileUrl, { signal: controller.signal });
        if (!response.ok) {
          throw new Error(`Unable to fetch PDF (${response.status})`);
        }
        const blob = await response.blob();
        if (cancelled) {
          return;
        }
        let resolvedFile: File | Blob;
        try {
          resolvedFile = new File([blob], filename ?? 'document.pdf', {
            type: blob.type || 'application/pdf'
          });
        } catch {
          resolvedFile = blob;
        }
        setFileBlob(resolvedFile);
      } catch (loadError) {
        if (controller.signal.aborted) {
          return;
        }
        console.error('Failed to prepare PDF viewer', loadError);
        setError(loadError instanceof Error ? loadError.message : 'Unable to load PDF.');
        setFileBlob(null);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    };

    load();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [fileUrl, filename]);

  const displayName = useMemo(() => {
    if (!filename) {
      return fileSize ?? 'PDF document';
    }
    return fileSize ? `${filename} (${fileSize})` : filename;
  }, [filename, fileSize]);

  const handleDocumentLoad = useCallback((pageCount: number) => {
    setTotalPages(pageCount);
    setPage((current) => {
      if (!pageCount) {
        setPageInput('1');
        return 1;
      }
      const next = Math.min(Math.max(current, 1), pageCount);
      setPageInput(String(next));
      return next;
    });
  }, []);

  const handlePageChange = useCallback((pageNumber: number) => {
    setPage(pageNumber);
    setPageInput(String(pageNumber));
  }, []);

  const handleScaleChange = useCallback((nextScale: number) => {
    setScale((current) => (Math.abs(current - nextScale) < 0.001 ? current : nextScale));
  }, []);

  useEffect(() => {
    setScaleInput(String(Math.round(scale * 100)));
  }, [scale]);

  useEffect(() => {
    setPageInput(String(page));
  }, [page]);

  const commitScaleInput = (inputValue: string) => {
    const numeric = Number.parseFloat(inputValue);
    if (Number.isNaN(numeric)) {
      setScaleInput(String(Math.round(scale * 100)));
      return;
    }
    const clamped = clampPercent(numeric);
    setScale(clamped / 100);
    setScaleInput(String(Math.round(clamped)));
  };

  const updateScale = (inputValue: string) => {
    setScaleInput(inputValue);
    const numeric = Number.parseFloat(inputValue);
    if (Number.isNaN(numeric)) {
      return;
    }
    const clamped = clampPercent(numeric);
    setScale(clamped / 100);
  };

  const commitPageInputValue = (inputValue: string) => {
    const numeric = Number.parseInt(inputValue, 10);
    if (Number.isNaN(numeric)) {
      setPageInput(String(page));
      return;
    }
    const upperBound = Math.max(totalPages || 1, 1);
    const clamped = Math.min(Math.max(numeric, 1), upperBound);
    setPage(clamped);
    setPageInput(String(clamped));
  };

  const updatePageValue = (inputValue: string) => {
    setPageInput(inputValue);
    const numeric = Number.parseInt(inputValue, 10);
    if (Number.isNaN(numeric) || !totalPages) {
      return;
    }
    const clamped = Math.min(Math.max(numeric, 1), totalPages);
    if (clamped !== page) {
      setPage(clamped);
    }
  };

  const handleFitHeight = useCallback(async () => {
    const scaleValue = await viewerRef.current?.fitToHeight?.();
    if (typeof scaleValue === 'number' && Number.isFinite(scaleValue)) {
      setScale(scaleValue);
    }
  }, []);

  const handleFitWidth = useCallback(async () => {
    const scaleValue = await viewerRef.current?.fitToWidth?.();
    if (typeof scaleValue === 'number' && Number.isFinite(scaleValue)) {
      setScale(scaleValue);
    }
  }, []);

  return (
    <Paper withBorder radius="sm" p="md" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Stack className="pdf2p-viewer">
        <Box className="pdf2p-viewer__meta">
          <Text fw={600}>{displayName}</Text>
          {totalPages ? (
            <Text size="xs" c="dimmed">
              {totalPages} page{totalPages === 1 ? '' : 's'}
            </Text>
          ) : null}
        </Box>

        <Box className="pdf2p-viewer__toolbar">
          <div className="pdf2p-viewer__control-group">
            <div className="pdf2p-viewer__zoom-toggle">
              <button
                type="button"
                onClick={() => setScale((value) => Math.max(value - SCALE_STEP, MIN_SCALE))}
                disabled={scale <= MIN_SCALE}
              >
                −
              </button>
              <div className="pdf2p-viewer__zoom-input-wrapper">
                <input
                  type="number"
                  min={10}
                  max={400}
                  value={scaleInput}
                  onChange={(event) => updateScale(event.target.value)}
                  onBlur={() => commitScaleInput(scaleInput)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') {
                      event.preventDefault();
                      commitScaleInput(scaleInput);
                    } else if (event.key === 'Escape') {
                      event.preventDefault();
                      setScaleInput(String(Math.round(scale * 100)));
                    }
                  }}
                />
                <span>%</span>
              </div>
              <button
                type="button"
                onClick={() => setScale((value) => Math.min(value + SCALE_STEP, MAX_SCALE))}
                disabled={scale >= MAX_SCALE}
              >
                +
              </button>
            </div>
            <button type="button" onClick={() => setScale(1.25)}>
              Reset
            </button>
            <button type="button" onClick={handleFitHeight}>
              Fit Page
            </button>
            <button type="button" onClick={handleFitWidth}>
              Fit Width
            </button>
          </div>

          <div className="pdf2p-viewer__control-group">
            <button type="button" onClick={() => setPage((value) => Math.max(value - 1, 1))} disabled={page <= 1}>
              Previous
            </button>
            <button
              type="button"
              onClick={() =>
                setPage((value) => {
                  if (!totalPages) {
                    return value;
                  }
                  return Math.min(value + 1, totalPages);
                })
              }
              disabled={!totalPages || page >= totalPages}
            >
              Next
            </button>
            {totalPages ? (
              <label className="pdf2p-viewer__page-input">
                <span>Page</span>
                <input
                  type="number"
                  min={1}
                  max={totalPages}
                  value={pageInput}
                  onChange={(event) => updatePageValue(event.target.value)}
                  onBlur={() => commitPageInputValue(pageInput)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') {
                      event.preventDefault();
                      commitPageInputValue(pageInput);
                    } else if (event.key === 'Escape') {
                      event.preventDefault();
                      setPageInput(String(page));
                    }
                  }}
                />
                <span>of {totalPages}</span>
              </label>
            ) : (
              <span className="pdf2p-viewer__status">Loading…</span>
            )}
          </div>
        </Box>

        {loading ? (
          <Box className="pdf2p-viewer__status">
            <Loader size="sm" color="teal" />
          </Box>
        ) : null}

        {error ? (
          <Text size="sm" c="red">
            {error}
          </Text>
        ) : null}

        <PdfJsSinglePage
          ref={(instance) => {
            viewerRef.current = instance;
          }}
          file={fileBlob}
          scale={scale}
          pageNumber={page}
          onDocumentLoad={handleDocumentLoad}
          onPageChange={handlePageChange}
          onScaleChange={handleScaleChange}
        />
      </Stack>
    </Paper>
  );
};

export default Pdf2pViewerBlock;
