declare module 'pdfjs-dist/build/pdf';

declare module 'pdfjs-dist/build/pdf.worker?url' {
  const workerSrc: string;
  export default workerSrc;
}

declare module 'pdfjs-dist/web/pdf_viewer.mjs';
