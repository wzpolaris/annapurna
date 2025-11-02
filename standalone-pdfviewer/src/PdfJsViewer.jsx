import { useEffect, useRef } from 'react';
import * as pdfjs from 'pdfjs-dist/build/pdf';
import workerSrc from 'pdfjs-dist/build/pdf.worker?url';
import { EventBus, TextLayerBuilder } from 'pdfjs-dist/web/pdf_viewer.mjs';
import 'pdfjs-dist/web/pdf_viewer.css';

pdfjs.GlobalWorkerOptions.workerSrc = workerSrc;

export default function PdfJsViewer({ file, scale = 1, pageNumber = 1, onDocumentLoad }) {
  const containerRef = useRef(null);
  const pdfRef = useRef(null);
  const renderTaskRef = useRef(null);
  const textLayerBuilderRef = useRef(null);
  const eventBusRef = useRef(null);
  const pageRef = useRef(pageNumber);
  const scaleRef = useRef(scale);

  const renderPage = async (pdf, targetPage, targetScale, isCancelled) => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    const safePage = Math.min(Math.max(Math.floor(targetPage || 1), 1), pdf.numPages);

    if (renderTaskRef.current) {
      renderTaskRef.current.cancel();
      renderTaskRef.current = null;
    }
    if (textLayerBuilderRef.current) {
      textLayerBuilderRef.current.cancel();
      textLayerBuilderRef.current = null;
    }
    container.innerHTML = '<p class="pdfjs-status">Rendering…</p>';

    try {
      const page = await pdf.getPage(safePage);
      if (isCancelled?.()) {
        return;
      }

      const viewport = page.getViewport({ scale: targetScale });

      const canvas = document.createElement('canvas');
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      canvas.style.width = `${viewport.width}px`;
      canvas.style.height = `${viewport.height}px`;
      canvas.className = 'pdfjs-page';

      const wrapper = document.createElement('div');
      wrapper.className = 'pdfjs-page-wrapper';
      wrapper.style.width = `${viewport.width}px`;
      wrapper.style.height = `${viewport.height}px`;
      wrapper.appendChild(canvas);

      container.innerHTML = '';
      container.appendChild(wrapper);

      const renderTask = page.render({
        canvasContext: canvas.getContext('2d', { alpha: false }),
        viewport,
      });
      renderTaskRef.current = renderTask;

      if (!eventBusRef.current) {
        eventBusRef.current = new EventBus();
      }
      const textLayerBuilder = new TextLayerBuilder({
        pdfPage: page,
        eventBus: eventBusRef.current,
        highlighter: null,
      });
      textLayerBuilderRef.current = textLayerBuilder;
      const textLayerDiv = textLayerBuilder.div;
      textLayerDiv.classList.add('pdfjs-text-layer');
      textLayerDiv.style.width = `${viewport.width}px`;
      textLayerDiv.style.height = `${viewport.height}px`;
      textLayerDiv.style.pointerEvents = 'auto';
      wrapper.appendChild(textLayerDiv);

      const textLayerPromise = textLayerBuilder.render({
        viewport,
        textContentParams: {
          includeMarkedContent: true,
          disableNormalization: true,
        },
      });

      await Promise.all([renderTask.promise, textLayerPromise]);
      renderTaskRef.current = null;
      textLayerBuilderRef.current = null;
    } catch (error) {
      if (
        isCancelled?.() ||
        error?.name === 'AbortException' ||
        error instanceof pdfjs.RenderingCancelledException
      ) {
        return;
      }
      console.error('Failed to render PDF page with pdf.js', error);
      if (container) {
        container.innerHTML = '<p class="pdfjs-error">Unable to render PDF with jsView.</p>';
      }
    }
  };

  useEffect(() => {
    pageRef.current = pageNumber;
  }, [pageNumber]);

  useEffect(() => {
    scaleRef.current = scale;
  }, [scale]);

  useEffect(() => {
    let cancelled = false;
    let loadingTask;

    const cleanup = () => {
      if (renderTaskRef.current) {
        renderTaskRef.current.cancel();
        renderTaskRef.current = null;
      }
      if (textLayerBuilderRef.current) {
        textLayerBuilderRef.current.cancel();
        textLayerBuilderRef.current = null;
      }
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };

    const loadDocument = async () => {
      if (!file) {
        pdfRef.current = null;
        onDocumentLoad?.(0);
        cleanup();
        return;
      }

      onDocumentLoad?.(0);
      cleanup();

      try {
        const data = await file.arrayBuffer();
        if (cancelled) {
          return;
        }

        loadingTask = pdfjs.getDocument({ data });
        const pdf = await loadingTask.promise;
        if (cancelled) {
          await loadingTask.destroy?.();
          return;
        }

        pdfRef.current = pdf;
        onDocumentLoad?.(pdf.numPages);

        await renderPage(pdf, pageRef.current, scaleRef.current, () => cancelled);
      } catch (error) {
        if (
          cancelled ||
          error?.name === 'AbortException' ||
          error instanceof pdfjs.RenderingCancelledException
        ) {
          return;
        }
        console.error('Failed to render PDF with pdf.js', error);
        if (containerRef.current) {
          containerRef.current.innerHTML =
            '<p class="pdfjs-error">Unable to render PDF with jsView.</p>';
        }
      }
    };

    loadDocument();

    return () => {
      cancelled = true;
      if (renderTaskRef.current) {
        renderTaskRef.current.cancel();
        renderTaskRef.current = null;
      }
      if (textLayerBuilderRef.current) {
        textLayerBuilderRef.current.cancel();
        textLayerBuilderRef.current = null;
      }
      if (loadingTask) {
        loadingTask.destroy?.();
      }
      pdfRef.current = null;
      cleanup();
    };
  }, [file, onDocumentLoad]);

  useEffect(() => {
    const pdf = pdfRef.current;
    if (!pdf) {
      return;
    }

    let cancelled = false;

    renderPage(pdf, pageNumber, scale, () => cancelled);

    return () => {
      cancelled = true;
      if (renderTaskRef.current) {
        renderTaskRef.current.cancel();
        renderTaskRef.current = null;
      }
      if (textLayerBuilderRef.current) {
        textLayerBuilderRef.current.cancel();
        textLayerBuilderRef.current = null;
      }
    };
  }, [pageNumber, scale]);

  return <div ref={containerRef} className="pdfjs-viewer" />;
}
