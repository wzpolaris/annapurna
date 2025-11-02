import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react';
import * as pdfjs from 'pdfjs-dist/build/pdf';
import workerSrc from 'pdfjs-dist/build/pdf.worker?url';
import { EventBus, TextLayerBuilder } from 'pdfjs-dist/web/pdf_viewer.mjs';
import 'pdfjs-dist/web/pdf_viewer.css';

pdfjs.GlobalWorkerOptions.workerSrc = workerSrc;

const PdfJsSimple = forwardRef(function PdfJsSimple(
  { file, scale = 1, pageNumber = 1, onDocumentLoad },
  ref,
) {
  const containerRef = useRef(null);
  const pdfRef = useRef(null);
  const renderTaskRef = useRef(null);
  const textLayerBuilderRef = useRef(null);
  const eventBusRef = useRef(null);
  const pageRef = useRef(pageNumber);
  const scaleRef = useRef(scale);

  useImperativeHandle(
    ref,
    () => ({
      async fitToHeight() {
        const pdf = pdfRef.current;
        const container = containerRef.current;
        if (!pdf || !container) {
          return null;
        }
        try {
          const currentPage = Math.min(Math.max(pageRef.current || 1, 1), pdf.numPages);
          const page = await pdf.getPage(currentPage);
          const viewport = page.getViewport({ scale: 1 });
          const parent = container.parentElement ?? container;
          const availableHeight =
            parent.clientHeight ||
            parent.getBoundingClientRect().height ||
            window.innerHeight * 0.8;
          if (!availableHeight || !viewport.height) {
            return null;
          }
          const padding = 16;
          const scale = Math.max(0.1, Math.min(4, (availableHeight - padding) / viewport.height));
          return scale;
        } catch (error) {
          console.error('Failed to compute fit scale for jsView', error);
          return null;
        }
      },
      async fitToWidth() {
        const pdf = pdfRef.current;
        const container = containerRef.current;
        if (!pdf || !container) {
          return null;
        }
        try {
          const currentPage = Math.min(Math.max(pageRef.current || 1, 1), pdf.numPages);
          const page = await pdf.getPage(currentPage);
          const viewport = page.getViewport({ scale: 1 });
          const parent = container.parentElement ?? container;
          const availableWidth =
            parent.clientWidth ||
            parent.getBoundingClientRect().width ||
            window.innerWidth * 0.8;
          if (!availableWidth || !viewport.width) {
            return null;
          }
          const padding = 16;
          const scale = Math.max(0.1, Math.min(4, (availableWidth - padding) / viewport.width));
          return scale;
        } catch (error) {
          console.error('Failed to compute fit width scale for jsView', error);
          return null;
        }
      },
    }),
    [],
  );

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
    container.innerHTML = '<p class="pdf-suite__status">Rendering…</p>';

    try {
      const page = await pdf.getPage(safePage);
      if (isCancelled?.()) {
        return;
      }

      const viewport = page.getViewport({ scale: targetScale });
      const outputScale = window.devicePixelRatio || 1;

      const canvas = document.createElement('canvas');
      canvas.width = Math.floor(viewport.width * outputScale);
      canvas.height = Math.floor(viewport.height * outputScale);
      canvas.style.width = `${viewport.width}px`;
      canvas.style.height = `${viewport.height}px`;
      canvas.className = 'pdf-suite__canvas';

      const wrapper = document.createElement('div');
      wrapper.className = 'pdf-suite__canvas-wrapper';
      wrapper.style.width = `${viewport.width}px`;
      wrapper.style.height = `${viewport.height}px`;
      wrapper.appendChild(canvas);

      container.innerHTML = '';
      container.appendChild(wrapper);

      const context = canvas.getContext('2d', { alpha: false });
      if (outputScale !== 1) {
        context.scale(outputScale, outputScale);
      }

      const renderTask = page.render({
        canvasContext: context,
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
      textLayerDiv.classList.add('pdf-suite__text-layer');
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
        container.innerHTML = '<p class="pdf-suite__error">Unable to render PDF with jsView.</p>';
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
            '<p class="pdf-suite__error">Unable to render PDF with jsView.</p>';
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

  return <div ref={containerRef} className="pdf-suite__simple-viewer" />;
});

export default PdfJsSimple;
