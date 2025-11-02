import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import PdfJsSimple from './PdfJsSimple.jsx';
import PdfJsManaged from './PdfJsManaged.jsx';
import PdfJsSinglePage from './PdfJsSinglePage.jsx';
import './PdfViewer.css';

const formatBytes = (bytes) => {
  if (!Number.isFinite(bytes) || bytes <= 0) return '';
  const units = ['B', 'KB', 'MB', 'GB'];
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / 1024 ** exponent;
  return `${value.toFixed(value >= 10 || exponent === 0 ? 0 : 1)} ${units[exponent]}`;
};

const DEFAULT_SCALE = 1.25;

export default function PdfViewer({ title = 'Standalone PDF Viewer' }) {
  const fileInputRef = useRef(null);
  const simpleViewerRef = useRef(null);
  const managedViewerRef = useRef(null);
  const singleViewerRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [viewerUrl, setViewerUrl] = useState(null);
  const [message, setMessage] = useState('');
  const [activeViewer, setActiveViewer] = useState(null);
  const [simpleScale, setSimpleScale] = useState(DEFAULT_SCALE);
  const [simplePage, setSimplePage] = useState(1);
  const [simpleTotalPages, setSimpleTotalPages] = useState(0);
  const [managedScale, setManagedScale] = useState(DEFAULT_SCALE);
  const [managedPage, setManagedPage] = useState(1);
  const [managedTotalPages, setManagedTotalPages] = useState(0);
  const [singleScale, setSingleScale] = useState(DEFAULT_SCALE);
  const [singlePage, setSinglePage] = useState(1);
  const [singleTotalPages, setSingleTotalPages] = useState(0);
  const [simpleScaleInput, setSimpleScaleInput] = useState(
    String(Math.round(DEFAULT_SCALE * 100)),
  );
  const [managedScaleInput, setManagedScaleInput] = useState(
    String(Math.round(DEFAULT_SCALE * 100)),
  );
  const [singleScaleInput, setSingleScaleInput] = useState(
    String(Math.round(DEFAULT_SCALE * 100)),
  );
  const [simplePageInput, setSimplePageInput] = useState('1');
  const [managedPageInput, setManagedPageInput] = useState('1');
  const [singlePageInput, setSinglePageInput] = useState('1');

  useEffect(() => {
    return () => {
      if (viewerUrl) {
        URL.revokeObjectURL(viewerUrl);
      }
    };
  }, [viewerUrl]);

  const fileInfo = useMemo(() => {
    if (!selectedFile) {
      return '';
    }
    const sizeText = formatBytes(selectedFile.size);
    const parts = [selectedFile.name];
    if (sizeText) {
      parts.push(`(${sizeText})`);
    }
    return parts.join(' ');
  }, [selectedFile]);

  const resetViewerState = () => {
    setActiveViewer(null);
    setSimpleScale(DEFAULT_SCALE);
    setSimplePage(1);
    setSimpleTotalPages(0);
    setManagedScale(DEFAULT_SCALE);
    setManagedPage(1);
    setManagedTotalPages(0);
    setSingleScale(DEFAULT_SCALE);
    setSinglePage(1);
    setSingleTotalPages(0);
    setSimpleScaleInput(String(Math.round(DEFAULT_SCALE * 100)));
    setManagedScaleInput(String(Math.round(DEFAULT_SCALE * 100)));
    setSingleScaleInput(String(Math.round(DEFAULT_SCALE * 100)));
    setSimplePageInput('1');
    setManagedPageInput('1');
    setSinglePageInput('1');
  };

  const handleUploadClick = () => {
    setMessage('');
    fileInputRef.current?.click();
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      if (viewerUrl) {
        URL.revokeObjectURL(viewerUrl);
      }
      setViewerUrl(null);
      setSelectedFile(file);
      setMessage('');
      resetViewerState();
    }
  };

  const ensurePdf = () => {
    if (!selectedFile) {
      setMessage('Please upload a file first.');
      return false;
    }
    const extension = selectedFile.name.split('.').pop()?.toLowerCase();
    if (extension !== 'pdf') {
      setMessage('The selected file is not a PDF.');
      setActiveViewer(null);
      return false;
    }
    return true;
  };

  const handleNativeView = () => {
    if (!ensurePdf()) {
      return;
    }
    if (viewerUrl) {
      URL.revokeObjectURL(viewerUrl);
    }
    setViewerUrl(URL.createObjectURL(selectedFile));
    setMessage('');
    setActiveViewer('native');
  };

  const handleSimpleView = () => {
    if (!ensurePdf()) {
      return;
    }
    if (viewerUrl) {
      URL.revokeObjectURL(viewerUrl);
    }
    setViewerUrl(null);
    setMessage('');
    resetViewerState();
    setActiveViewer('simple');
  };

  const handleManagedView = () => {
    if (!ensurePdf()) {
      return;
    }
    if (viewerUrl) {
      URL.revokeObjectURL(viewerUrl);
    }
    setViewerUrl(null);
    setMessage('');
    resetViewerState();
    setActiveViewer('managed');
  };

  const handleSingleView = () => {
    if (!ensurePdf()) {
      return;
    }
    if (viewerUrl) {
      URL.revokeObjectURL(viewerUrl);
    }
    setViewerUrl(null);
    setMessage('');
    resetViewerState();
    setActiveViewer('managed-single');
  };

  const handleSimpleZoomIn = () => {
    setSimpleScale((value) => Math.min(value + 0.25, 3));
  };

  const handleSimpleZoomOut = () => {
    setSimpleScale((value) => Math.max(value - 0.25, 0.5));
  };

  const handleSimpleResetZoom = () => {
    setSimpleScale(DEFAULT_SCALE);
  };

  const handleSimplePrevPage = () => {
    setSimplePage((page) => {
      const next = Math.max(page - 1, 1);
      setSimplePageInput(String(next));
      return next;
    });
  };

  const handleSimpleNextPage = () => {
    setSimplePage((page) => {
      if (!simpleTotalPages) {
        return page;
      }
      const next = Math.min(page + 1, simpleTotalPages);
      setSimplePageInput(String(next));
      return next;
    });
  };

  const handleSimpleDocumentLoad = useCallback((pageCount) => {
    setSimpleTotalPages(pageCount);
    setSimplePage((page) => {
      if (!pageCount) {
        setSimplePageInput('1');
        return 1;
      }
      const next = Math.min(Math.max(page, 1), pageCount);
      setSimplePageInput(String(next));
      return next;
    });
  }, []);

  const handleManagedZoomIn = () => {
    setManagedScale((value) => Math.min(value + 0.25, 3));
  };

  const handleManagedZoomOut = () => {
    setManagedScale((value) => Math.max(value - 0.25, 0.5));
  };

  const handleManagedResetZoom = () => {
    setManagedScale(DEFAULT_SCALE);
  };

  const handleManagedPrevPage = () => {
    setManagedPage((page) => {
      const next = Math.max(page - 1, 1);
      setManagedPageInput(String(next));
      return next;
    });
  };

  const handleManagedNextPage = () => {
    setManagedPage((page) => {
      if (!managedTotalPages) {
        return page;
      }
      const next = Math.min(page + 1, managedTotalPages);
      setManagedPageInput(String(next));
      return next;
    });
  };

  const handleManagedDocumentLoad = useCallback((pageCount) => {
    setManagedTotalPages(pageCount);
    setManagedPage((page) => {
      if (!pageCount) {
        setManagedPageInput('1');
        return 1;
      }
      const next = Math.min(Math.max(page, 1), pageCount);
      setManagedPageInput(String(next));
      return next;
    });
  }, []);

  const handleManagedPageChange = useCallback((pageNumber) => {
    setManagedPage(pageNumber);
    setManagedPageInput(String(pageNumber));
  }, []);

  const handleManagedScaleChange = useCallback((newScale) => {
    setManagedScale((current) => (Math.abs(current - newScale) < 0.001 ? current : newScale));
  }, []);
  const clampPercent = (value) => Math.min(Math.max(value, 10), 400);

  const commitScaleInput = (inputValue, currentScale, setScale, setInput) => {
    const numeric = Number.parseFloat(inputValue);
    if (Number.isNaN(numeric)) {
      setInput(String(Math.round(currentScale * 100)));
      return;
    }
    const clamped = clampPercent(numeric);
    setScale(clamped / 100);
    setInput(String(Math.round(clamped)));
  };

  const updateScaleInput = (inputValue, setInput, setScale) => {
    setInput(inputValue);
    const numeric = Number.parseFloat(inputValue);
    if (Number.isNaN(numeric)) {
      return;
    }
    const clamped = clampPercent(numeric);
    setScale(clamped / 100);
  };

  const commitPageInput = (inputValue, currentPage, totalPages, setPage, setInput) => {
    const numeric = Number.parseInt(inputValue, 10);
    if (Number.isNaN(numeric)) {
      setInput(String(currentPage));
      return;
    }
    const upperBound = Math.max(totalPages || 1, 1);
    const clamped = Math.min(Math.max(numeric, 1), upperBound);
    setPage(clamped);
    setInput(String(clamped));
  };

  const updatePageInput = (inputValue, currentPage, totalPages, setInput, setPage) => {
    setInput(inputValue);
    const numeric = Number.parseInt(inputValue, 10);
    if (Number.isNaN(numeric) || !totalPages) {
      return;
    }
    const clamped = Math.min(Math.max(numeric, 1), totalPages);
    if (clamped !== currentPage) {
      setPage(clamped);
    }
  };

  useEffect(() => {
    setSimpleScaleInput(String(Math.round(simpleScale * 100)));
  }, [simpleScale]);

  useEffect(() => {
    setManagedScaleInput(String(Math.round(managedScale * 100)));
  }, [managedScale]);

  useEffect(() => {
    setSingleScaleInput(String(Math.round(singleScale * 100)));
  }, [singleScale]);

  useEffect(() => {
    setSimplePageInput(String(simplePage));
  }, [simplePage]);

  useEffect(() => {
    setManagedPageInput(String(managedPage));
  }, [managedPage]);

  useEffect(() => {
    setSinglePageInput(String(singlePage));
  }, [singlePage]);

  const handleSimpleFitPage = useCallback(async () => {
    const scale = await simpleViewerRef.current?.fitToHeight?.();
    if (typeof scale === 'number' && Number.isFinite(scale)) {
      setSimpleScale(scale);
    }
  }, []);

  const handleManagedFitPage = useCallback(() => {
    const scale = managedViewerRef.current?.fitToHeight?.();
    if (typeof scale === 'number' && Number.isFinite(scale)) {
      setManagedScale(scale);
    }
  }, []);

  const handleSingleFitPage = useCallback(() => {
    const scale = singleViewerRef.current?.fitToHeight?.();
    if (typeof scale === 'number' && Number.isFinite(scale)) {
      setSingleScale(scale);
    }
  }, []);

  const handleManagedFitWidth = useCallback(() => {
    const scale = managedViewerRef.current?.fitToWidth?.();
    if (typeof scale === 'number' && Number.isFinite(scale)) {
      setManagedScale(scale);
    }
  }, []);

  const handleSingleFitWidth = useCallback(() => {
    const scale = singleViewerRef.current?.fitToWidth?.();
    if (typeof scale === 'number' && Number.isFinite(scale)) {
      setSingleScale(scale);
    }
  }, []);

  const handleSingleZoomIn = () => {
    setSingleScale((value) => Math.min(value + 0.25, 3));
  };

  const handleSingleZoomOut = () => {
    setSingleScale((value) => Math.max(value - 0.25, 0.5));
  };

  const handleSingleResetZoom = () => {
    setSingleScale(DEFAULT_SCALE);
  };

const handleSinglePrevPage = () => {
  setSinglePage((page) => {
    const next = Math.max(page - 1, 1);
    setSinglePageInput(String(next));
    return next;
  });
};

const handleSingleNextPage = () => {
  setSinglePage((page) => {
    if (!singleTotalPages) {
      return page;
    }
    const next = Math.min(page + 1, singleTotalPages);
    setSinglePageInput(String(next));
    return next;
  });
};

const handleSingleDocumentLoad = useCallback((pageCount) => {
  setSingleTotalPages(pageCount);
  setSinglePage((page) => {
    if (!pageCount) {
      setSinglePageInput('1');
      return 1;
    }
    const next = Math.min(Math.max(page, 1), pageCount);
    setSinglePageInput(String(next));
    return next;
  });
}, []);

const handleSinglePageChange = useCallback((pageNumber) => {
  setSinglePage(pageNumber);
  setSinglePageInput(String(pageNumber));
}, []);

  const handleSingleScaleChange = useCallback((newScale) => {
    setSingleScale((current) => (Math.abs(current - newScale) < 0.001 ? current : newScale));
  }, []);

  return (
    <div className="pdf-suite">
      <div className="pdf-suite__card">
        <h1 className="pdf-suite__heading">{title}</h1>
        <div className="pdf-suite__controls">
          <button type="button" onClick={handleUploadClick}>
            Upload
          </button>
          <button type="button" onClick={handleNativeView}>
            View
          </button>
          <button type="button" onClick={handleSimpleView}>
            jsView
          </button>
          <button type="button" onClick={handleManagedView}>
            pdfView2
          </button>
          <button type="button" onClick={handleSingleView}>
            pdfView2p
          </button>
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
        </div>
        {fileInfo && <p className="pdf-suite__file-info">{fileInfo}</p>}
        {message && <p className="pdf-suite__message">{message}</p>}

        {activeViewer === 'native' && viewerUrl && (
          <div className="pdf-suite__panel">
            <h2 className="pdf-suite__panel-title">Native Viewer</h2>
            <iframe
              title={selectedFile?.name ?? 'PDF Document'}
              src={viewerUrl}
              className="pdf-suite__iframe"
            />
          </div>
        )}

        {activeViewer === 'simple' && (
          <div className="pdf-suite__panel">
            <h2 className="pdf-suite__panel-title">jsView</h2>
            <div className="pdf-suite__toolbar">
              <div className="pdf-suite__control-group pdf-suite__control-group--compact">
                <div className="pdf-suite__zoom-toggle">
                  <button
                    type="button"
                    onClick={handleSimpleZoomOut}
                    aria-label="Zoom out"
                  >
                    −
                  </button>
                  <div className="pdf-suite__zoom-input-wrapper">
                    <input
                      type="number"
                      min="10"
                      max="400"
                      value={simpleScaleInput}
                      onChange={(event) =>
                        updateScaleInput(event.target.value, setSimpleScaleInput, setSimpleScale)
                      }
                      onKeyDown={(event) => {
                        if (event.key === 'Enter') {
                          event.preventDefault();
                          commitScaleInput(
                            simpleScaleInput,
                            simpleScale,
                            setSimpleScale,
                            setSimpleScaleInput,
                          );
                        } else if (event.key === 'Escape') {
                          event.preventDefault();
                          setSimpleScaleInput(String(Math.round(simpleScale * 100)));
                        }
                      }}
                      onBlur={() =>
                        commitScaleInput(simpleScaleInput, simpleScale, setSimpleScale, setSimpleScaleInput)
                      }
                    />
                    <span>%</span>
                  </div>
                  <button
                    type="button"
                    onClick={handleSimpleZoomIn}
                    aria-label="Zoom in"
                  >
                    +
                  </button>
                </div>
                <button type="button" onClick={handleSimpleResetZoom}>
                  Reset
                </button>
                <button type="button" onClick={handleSimpleFitPage}>
                  Fit Page
                </button>
                <button type="button" onClick={handleSimpleFitWidth}>
                  Fit Width
                </button>
              </div>
              <div className="pdf-suite__control-group pdf-suite__control-group--compact">
                <button type="button" onClick={handleSimplePrevPage} disabled={simplePage <= 1}>
                  Previous
                </button>
                <button
                  type="button"
                  onClick={handleSimpleNextPage}
                  disabled={!simpleTotalPages || simplePage >= simpleTotalPages}
                >
                  Next
                </button>
                {simpleTotalPages ? (
                  <label className="pdf-suite__page-input">
                    <span>Page</span>
                    <input
                      type="number"
                      min="1"
                      max={simpleTotalPages}
                      value={simplePageInput}
                      onChange={(event) =>
                        updatePageInput(
                          event.target.value,
                          simplePage,
                          simpleTotalPages,
                          setSimplePageInput,
                          setSimplePage,
                        )
                      }
                      onKeyDown={(event) => {
                        if (event.key === 'Enter') {
                          event.preventDefault();
                          commitPageInput(
                            simplePageInput,
                            simplePage,
                            simpleTotalPages,
                            setSimplePage,
                            setSimplePageInput,
                          );
                        } else if (event.key === 'Escape') {
                          event.preventDefault();
                          setSimplePageInput(String(simplePage));
                        }
                      }}
                      onBlur={() =>
                        commitPageInput(
                          simplePageInput,
                          simplePage,
                          simpleTotalPages,
                          setSimplePage,
                          setSimplePageInput,
                        )
                      }
                    />
                    <span>of {simpleTotalPages}</span>
                  </label>
                ) : (
                  <span className="pdf-suite__value-label pdf-suite__value-label--wide">Loading…</span>
                )}
              </div>
            </div>
            <PdfJsSimple
              ref={simpleViewerRef}
              file={selectedFile}
              scale={simpleScale}
              pageNumber={simplePage}
              onDocumentLoad={handleSimpleDocumentLoad}
            />
          </div>
        )}

        {activeViewer === 'managed' && (
          <div className="pdf-suite__panel">
            <h2 className="pdf-suite__panel-title">pdfView2</h2>
            <div className="pdf-suite__toolbar">
              <div className="pdf-suite__control-group pdf-suite__control-group--compact">
                <div className="pdf-suite__zoom-toggle">
                  <button
                    type="button"
                    onClick={handleManagedZoomOut}
                    aria-label="Zoom out"
                  >
                    −
                  </button>
                  <div className="pdf-suite__zoom-input-wrapper">
                    <input
                      type="number"
                      min="10"
                      max="400"
                      value={managedScaleInput}
                      onChange={(event) =>
                        updateScaleInput(event.target.value, setManagedScaleInput, setManagedScale)
                      }
                      onKeyDown={(event) => {
                        if (event.key === 'Enter') {
                          event.preventDefault();
                          commitScaleInput(
                            managedScaleInput,
                            managedScale,
                            setManagedScale,
                            setManagedScaleInput,
                          );
                        } else if (event.key === 'Escape') {
                          event.preventDefault();
                          setManagedScaleInput(String(Math.round(managedScale * 100)));
                        }
                      }}
                      onBlur={() =>
                        commitScaleInput(
                          managedScaleInput,
                          managedScale,
                          setManagedScale,
                          setManagedScaleInput,
                        )
                      }
                    />
                    <span>%</span>
                  </div>
                  <button
                    type="button"
                    onClick={handleManagedZoomIn}
                    aria-label="Zoom in"
                  >
                    +
                  </button>
                </div>
                <button type="button" onClick={handleManagedResetZoom}>
                  Reset
                </button>
                <button type="button" onClick={handleManagedFitPage}>
                  Fit Page
                </button>
                <button type="button" onClick={handleManagedFitWidth}>
                  Fit Width
                </button>
              </div>
              <div className="pdf-suite__control-group pdf-suite__control-group--compact">
                <button type="button" onClick={handleManagedPrevPage} disabled={managedPage <= 1}>
                  Previous
                </button>
                <button
                  type="button"
                  onClick={handleManagedNextPage}
                  disabled={!managedTotalPages || managedPage >= managedTotalPages}
                >
                  Next
                </button>
                {managedTotalPages ? (
                  <label className="pdf-suite__page-input">
                    <span>Page</span>
                    <input
                      type="number"
                      min="1"
                      max={managedTotalPages}
                      value={managedPageInput}
                      onChange={(event) =>
                        updatePageInput(
                          event.target.value,
                          managedPage,
                          managedTotalPages,
                          setManagedPageInput,
                          setManagedPage,
                        )
                      }
                      onKeyDown={(event) => {
                        if (event.key === 'Enter') {
                          event.preventDefault();
                          commitPageInput(
                            managedPageInput,
                            managedPage,
                            managedTotalPages,
                            setManagedPage,
                            setManagedPageInput,
                          );
                        } else if (event.key === 'Escape') {
                          event.preventDefault();
                          setManagedPageInput(String(managedPage));
                        }
                      }}
                      onBlur={() =>
                        commitPageInput(
                          managedPageInput,
                          managedPage,
                          managedTotalPages,
                          setManagedPage,
                          setManagedPageInput,
                        )
                      }
                    />
                    <span>of {managedTotalPages}</span>
                  </label>
                ) : (
                  <span className="pdf-suite__value-label pdf-suite__value-label--wide">Loading…</span>
                )}
              </div>
            </div>
            <PdfJsManaged
              ref={managedViewerRef}
              file={selectedFile}
              scale={managedScale}
              pageNumber={managedPage}
              onDocumentLoad={handleManagedDocumentLoad}
              onPageChange={handleManagedPageChange}
              onScaleChange={handleManagedScaleChange}
            />
          </div>
        )}

        {activeViewer === 'managed-single' && (
          <div className="pdf-suite__panel">
            <h2 className="pdf-suite__panel-title">pdfView2p</h2>
            <div className="pdf-suite__toolbar">
              <div className="pdf-suite__control-group pdf-suite__control-group--compact">
                <div className="pdf-suite__zoom-toggle">
                  <button
                    type="button"
                    onClick={handleSingleZoomOut}
                    aria-label="Zoom out"
                  >
                    −
                  </button>
                  <div className="pdf-suite__zoom-input-wrapper">
                    <input
                      type="number"
                      min="10"
                      max="400"
                      value={singleScaleInput}
                      onChange={(event) =>
                        updateScaleInput(event.target.value, setSingleScaleInput, setSingleScale)
                      }
                      onKeyDown={(event) => {
                        if (event.key === 'Enter') {
                          event.preventDefault();
                          commitScaleInput(
                            singleScaleInput,
                            singleScale,
                            setSingleScale,
                            setSingleScaleInput,
                          );
                        } else if (event.key === 'Escape') {
                          event.preventDefault();
                          setSingleScaleInput(String(Math.round(singleScale * 100)));
                        }
                      }}
                      onBlur={() =>
                        commitScaleInput(
                          singleScaleInput,
                          singleScale,
                          setSingleScale,
                          setSingleScaleInput,
                        )
                      }
                    />
                    <span>%</span>
                  </div>
                  <button
                    type="button"
                    onClick={handleSingleZoomIn}
                    aria-label="Zoom in"
                  >
                    +
                  </button>
                </div>
                <button type="button" onClick={handleSingleResetZoom}>
                  Reset
                </button>
                <button type="button" onClick={handleSingleFitPage}>
                  Fit Page
                </button>
                <button type="button" onClick={handleSingleFitWidth}>
                  Fit Width
                </button>
              </div>
              <div className="pdf-suite__control-group pdf-suite__control-group--compact">
                <button type="button" onClick={handleSinglePrevPage} disabled={singlePage <= 1}>
                  Previous
                </button>
                <button
                  type="button"
                  onClick={handleSingleNextPage}
                  disabled={!singleTotalPages || singlePage >= singleTotalPages}
                >
                  Next
                </button>
                {singleTotalPages ? (
                  <label className="pdf-suite__page-input">
                    <span>Page</span>
                    <input
                      type="number"
                      min="1"
                      max={singleTotalPages}
                      value={singlePageInput}
                      onChange={(event) =>
                        updatePageInput(
                          event.target.value,
                          singlePage,
                          singleTotalPages,
                          setSinglePageInput,
                          setSinglePage,
                        )
                      }
                      onKeyDown={(event) => {
                        if (event.key === 'Enter') {
                          event.preventDefault();
                          commitPageInput(
                            singlePageInput,
                            singlePage,
                            singleTotalPages,
                            setSinglePage,
                            setSinglePageInput,
                          );
                        } else if (event.key === 'Escape') {
                          event.preventDefault();
                          setSinglePageInput(String(singlePage));
                        }
                      }}
                      onBlur={() =>
                        commitPageInput(
                          singlePageInput,
                          singlePage,
                          singleTotalPages,
                          setSinglePage,
                          setSinglePageInput,
                        )
                      }
                    />
                    <span>of {singleTotalPages}</span>
                  </label>
                ) : (
                  <span className="pdf-suite__value-label pdf-suite__value-label--wide">Loading…</span>
                )}
              </div>
            </div>
            <PdfJsSinglePage
              ref={singleViewerRef}
              file={selectedFile}
              scale={singleScale}
              pageNumber={singlePage}
              onDocumentLoad={handleSingleDocumentLoad}
              onPageChange={handleSinglePageChange}
              onScaleChange={handleSingleScaleChange}
            />
          </div>
        )}
      </div>
    </div>
  );
}
