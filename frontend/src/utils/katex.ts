import renderMathInElement, {
  type RenderMathInElementOptions,
} from 'katex/contrib/auto-render';

const RENDER_OPTIONS: RenderMathInElementOptions = {
  delimiters: [
    { left: '$$', right: '$$', display: true },
    { left: '\\(', right: '\\)', display: false },
    { left: '\\[', right: '\\]', display: true },
    { left: '$', right: '$', display: false },
  ],
  throwOnError: false,
  strict: 'ignore',
  globalGroup: true,
  ignoredTags: ['script', 'noscript', 'style', 'textarea'],
  ignoredClasses: ['no-mathjax', 'katex'],
};

export const runKatexAutoRender = (element: HTMLElement | null): void => {
  if (!element) {
    return;
  }

  try {
    renderMathInElement(element, RENDER_OPTIONS);
  } catch (error) {
    // eslint-disable-next-line no-console
    console.warn('KaTeX render error:', error);
  }
};
