const DEFAULT_MEETING_ID = 'mock-meeting-001';
const DEFAULT_DELAY_MS = 400;

export function __setMockUploadDelay__(delayMs: number) {
  (globalThis as { __mockUploadDelay__?: number }).__mockUploadDelay__ = delayMs;
}

export function __getMockUploadDelay__(): number {
  const stored = (globalThis as { __mockUploadDelay__?: number }).__mockUploadDelay__;
  return typeof stored === 'number' ? stored : DEFAULT_DELAY_MS;
}

export async function mockMeetingUpload(_file: File): Promise<string> {
  const delay = __getMockUploadDelay__();
  if (delay > 0) {
    await new Promise((resolve) => {
      setTimeout(resolve, delay);
    });
  }
  return DEFAULT_MEETING_ID;
}
