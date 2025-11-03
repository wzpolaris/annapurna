/// <reference lib="webworker" />

import { prepareTextPreview } from '../utils/textPreview';

type WorkerRequest = {
  id: number;
  buffer: ArrayBuffer;
};

type WorkerSuccess = {
  id: number;
  ok: true;
  preview: ReturnType<typeof prepareTextPreview>;
};

type WorkerFailure = {
  id: number;
  ok: false;
  error?: string;
};

const ctx: DedicatedWorkerGlobalScope = self as unknown as DedicatedWorkerGlobalScope;

ctx.onmessage = (event: MessageEvent<WorkerRequest>) => {
  const { id, buffer } = event.data;
  try {
    const decoder = new TextDecoder('utf-8', { fatal: true });
    const decoded = decoder.decode(buffer);
    const preview = prepareTextPreview(decoded);
    const payload: WorkerSuccess = { id, ok: true, preview };
    ctx.postMessage(payload);
  } catch (error) {
    const payload: WorkerFailure = {
      id,
      ok: false,
      error: error instanceof Error ? error.message : 'Unable to prepare preview.'
    };
    ctx.postMessage(payload);
  }
};
