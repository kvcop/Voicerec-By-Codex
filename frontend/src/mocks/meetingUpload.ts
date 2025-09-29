const DEFAULT_MEETING_ID = 'mock-meeting-001';
const DEFAULT_DELAY_MS = 400;

export interface MockUploadProgress {
  loaded: number;
  total?: number;
  percent: number | null;
}

export interface MockUploadOptions {
  onProgress?: (progress: MockUploadProgress) => void;
}

export function __setMockUploadDelay__(delayMs: number) {
  (globalThis as { __mockUploadDelay__?: number }).__mockUploadDelay__ = delayMs;
}

export function __getMockUploadDelay__(): number {
  const stored = (globalThis as { __mockUploadDelay__?: number }).__mockUploadDelay__;
  return typeof stored === 'number' ? stored : DEFAULT_DELAY_MS;
}

export async function mockMeetingUpload(file: File, options?: MockUploadOptions): Promise<string> {
  const delay = __getMockUploadDelay__();
  const total = file.size || undefined;

  options?.onProgress?.({ loaded: 0, total, percent: total ? 0 : null });

  if (delay > 0) {
    await new Promise((resolve) => {
      setTimeout(() => {
        options?.onProgress?.({ loaded: file.size, total, percent: total ? 100 : null });
        resolve(undefined);
      }, delay);

      if (typeof queueMicrotask === 'function') {
        queueMicrotask(() => {
          // Provide an intermediate progress tick for a more lifelike mock upload.
          options?.onProgress?.({
            loaded: Math.min(file.size, Math.floor((file.size || 1) / 2)),
            total,
            percent: total ? 50 : null,
          });
        });
      }
    });
  } else {
    options?.onProgress?.({ loaded: file.size, total, percent: total ? 100 : null });
  }

  return DEFAULT_MEETING_ID;
}
