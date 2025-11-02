import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from 'react';
import * as pdfjs from 'pdfjs-dist/build/pdf';
import workerSrc from 'pdfjs-dist/build/pdf.worker?url';
import {
  EventBus,
  PDFLinkService,
  PDFFindController,
  PDFViewer,
} from 'pdfjs-dist/web/pdf_viewer.mjs';
import 'pdfjs-dist/web/pdf_viewer.css';

pdfjs.GlobalWorkerOptions.workerSrc = workerSrc;

const EPSILON = 0.001;

const PdfJsManaged = forwardRef(function PdfJsManaged(
  { file, scale = 1, pageNumber = 1, onDocumentLoad, onPageChange, onScaleChange },
  ref,
) {
  const outerContainerRef = useRef(null);
  const viewerRef = useRef(null);
  const pdfViewerRef = useRef(null);
  const pdfDocumentRef = useRef(null);
  const linkServiceRef = useRef(null);
  const eventBusRef = useRef(null);
  const latestScaleRef = useRef(scale);
  const latestPageRef = useRef(pageNumber);
  const [viewerReady, setViewerReady] = useState(false);

  useEffect(() => {
    latestScaleRef.current = scale;
  }, [scale]);

  useEffect(() => {
    latestPageRef.current = pageNumber;
  }, [pageNumber]);

  const cleanupDocument = useCallback(async () => {
    const pdfViewer = pdfViewerRef.current;
    pdfViewer?.setDocument(null);

    const linkService = linkServiceRef.current;
    linkService?.setDocument(null);

    const existingDoc = pdfDocumentRef.current;
    pdfDocumentRef.current = null;
    await existingDoc?.destroy?.();
  }, []);

  useEffect(() => {
    const outerContainer = outerContainerRef.current;
    const viewer = viewerRef.current;
    if (!outerContainer || !viewer) {
      return undefined;
    }

    const eventBus = new EventBus();
    const linkService = new PDFLinkService({ eventBus });
    const findController = new PDFFindController({ eventBus, linkService });

    const pdfViewer = new PDFViewer({
      container: outerContainer,
      viewer,
      eventBus,
      linkService,
      findController,
      annotationMode: 0,
      textLayerMode: 1,
      removePageBorders: true,
    });

    linkService.setViewer(pdfViewer);

    const handlePagesInit = () => {
      const desiredScale = latestScaleRef.current;
      if (typeof desiredScale === 'number') {
        pdfViewer.currentScale = desiredScale;
      } else {
        pdfViewer.currentScaleValue = desiredScale ?? 'auto';
      }
      const desiredPage = latestPageRef.current;
      if (desiredPage) {
        pdfViewer.currentPageNumber = desiredPage;
      }
      onDocumentLoad?.(pdfViewer.pagesCount ?? 0);
      onPageChange?.(pdfViewer.currentPageNumber ?? 1);
      onScaleChange?.(pdfViewer.currentScale ?? desiredScale ?? 1);
    };

    const handlePagesLoaded = (evt) => {
      onDocumentLoad?.(evt.pagesCount ?? pdfViewer.pagesCount ?? 0);
    };

    const handlePageChanging = (evt) => {
      onPageChange?.(evt.pageNumber);
    };

    const handleScaleChanging = (evt) => {
      onScaleChange?.(evt.scale);
    };

    eventBus.on('pagesinit', handlePagesInit);
    eventBus.on('pagesloaded', handlePagesLoaded);
    eventBus.on('pagechanging', handlePageChanging);
    eventBus.on('scalechanging', handleScaleChanging);

    pdfViewerRef.current = pdfViewer;
    linkServiceRef.current = linkService;
    eventBusRef.current = eventBus;
    setViewerReady(true);

    return () => {
      eventBus.off('pagesinit', handlePagesInit);
      eventBus.off('pagesloaded', handlePagesLoaded);
      eventBus.off('pagechanging', handlePageChanging);
      eventBus.off('scalechanging', handleScaleChanging);
      pdfViewer.setDocument(null);
      pdfViewerRef.current = null;
      linkServiceRef.current = null;
      eventBusRef.current = null;
      setViewerReady(false);
    };
  }, [onDocumentLoad, onPageChange, onScaleChange]);

  useEffect(() => {
    if (!viewerReady) {
      return undefined;
    }
    let cancelled = false;
    let loadingTask;

    const loadDocument = async () => {
      const pdfViewer = pdfViewerRef.current;
      const linkService = linkServiceRef.current;
      if (!pdfViewer || !linkService) {
        return;
      }

      await cleanupDocument();

      if (!file) {
        onDocumentLoad?.(0);
        return;
      }

      try {
        const data = await file.arrayBuffer();
        if (cancelled) {
          return;
        }

        loadingTask = pdfjs.getDocument({ data });
        const pdfDocument = await loadingTask.promise;

        if (cancelled) {
          await loadingTask.destroy?.();
          await pdfDocument.destroy();
          return;
        }

        pdfDocumentRef.current = pdfDocument;
        linkService.setDocument(pdfDocument);
        pdfViewer.setDocument(pdfDocument);
      } catch (error) {
        if (cancelled) {
          return;
        }
        console.error('Failed to load PDF with pdf.js viewer', error);
        onDocumentLoad?.(0);
        if (viewerRef.current) {
          viewerRef.current.innerHTML =
            '<p class="pdf-suite__error">Unable to render PDF with pdfView2.</p>';
        }
      }
    };

    loadDocument();

    return () => {
      cancelled = true;
      loadingTask?.destroy?.();
    };
  }, [cleanupDocument, file, onDocumentLoad, viewerReady]);

  useEffect(() => {
    const pdfViewer = pdfViewerRef.current;
    if (!pdfViewer || !pdfViewer.pdfDocument) {
      return;
    }
    const clampedPage = Math.min(
      Math.max(1, Math.floor(pageNumber)),
      pdfViewer.pagesCount || 1,
    );
    if (pdfViewer.currentPageNumber !== clampedPage) {
      pdfViewer.currentPageNumber = clampedPage;
    }
  }, [pageNumber]);

  useEffect(() => {
    const pdfViewer = pdfViewerRef.current;
    if (!pdfViewer || !pdfViewer.pdfDocument) {
      return;
    }
    if (Math.abs((pdfViewer.currentScale ?? 0) - scale) > EPSILON) {
      pdfViewer.currentScale = scale;
    }
  }, [scale]);

  useEffect(() => () => {
    cleanupDocument();
  }, [cleanupDocument]);

  useImperativeHandle(
    ref,
    () => ({
      fitToHeight() {
        const pdfViewer = pdfViewerRef.current;
        if (!pdfViewer) {
          return null;
        }
        pdfViewer.currentScaleValue = 'page-fit';
        return pdfViewer.currentScale;
      },
      fitToWidth() {
        const pdfViewer = pdfViewerRef.current;
        if (!pdfViewer) {
          return null;
        }
        pdfViewer.currentScaleValue = 'page-width';
        return pdfViewer.currentScale;
      },
    }),
    [],
  );

  return (
    <div className="pdf-suite__managed-viewer">
      <div ref={outerContainerRef} className="pdf-suite__managed-scroll">
        <div ref={viewerRef} className="pdfViewer" />
      </div>
    </div>
  );
});

export default PdfJsManaged;
