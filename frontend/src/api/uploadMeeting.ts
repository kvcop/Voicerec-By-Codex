import { loadToken } from '../auth/tokenStorage';
import { mockMeetingUpload, MockUploadOptions, MockUploadProgress } from '../mocks/meetingUpload';

export type MeetingUploadErrorReason =
  | 'network'
  | 'invalidResponse'
  | 'missingMeetingId'
  | 'unauthorized';

export class MeetingUploadError extends Error {
  public readonly reason: MeetingUploadErrorReason;

  constructor(reason: MeetingUploadErrorReason, message?: string) {
    super(message ?? reason);
    this.reason = reason;
  }
}

interface UploadResponse {
  meeting_id?: unknown;
  meetingId?: unknown;
}

export type UploadProgress = MockUploadProgress;

export interface UploadOptions extends MockUploadOptions {}

function extractMeetingId(payload: UploadResponse): string | null {
  const candidate = payload.meeting_id ?? payload.meetingId;
  return typeof candidate === 'string' && candidate.trim() ? candidate : null;
}

function withProgressCallback(
  file: File,
  options: UploadOptions | undefined,
  progress: MockUploadProgress
) {
  if (!options?.onProgress) {
    return;
  }

  const total = progress.total ?? (file.size || undefined);
  const percent =
    progress.percent !== null
      ? Math.max(0, Math.min(100, progress.percent))
      : null;

  options.onProgress({
    loaded: progress.loaded,
    total,
    percent,
  });
}

async function requestUpload(file: File, options?: UploadOptions): Promise<string> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/meeting/upload');

    const token = loadToken();
    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    }

    xhr.upload.onprogress = (event) => {
      withProgressCallback(file, options, {
        loaded: event.loaded,
        total: event.lengthComputable ? event.total : undefined,
        percent: event.lengthComputable
          ? Math.round((event.loaded / event.total) * 100)
          : null,
      });
    };

    xhr.onerror = () => {
      reject(new MeetingUploadError('network'));
    };

    xhr.ontimeout = () => {
      reject(new MeetingUploadError('network'));
    };

    xhr.onabort = () => {
      reject(new MeetingUploadError('network'));
    };

    xhr.onload = () => {
      if (xhr.status === 401 || xhr.status === 403) {
        reject(new MeetingUploadError('unauthorized'));
        return;
      }

      if (xhr.status < 200 || xhr.status >= 300) {
        reject(new MeetingUploadError('network'));
        return;
      }

      const responseText = xhr.responseText ?? '';
      let payload: UploadResponse;
      try {
        payload = responseText ? (JSON.parse(responseText) as UploadResponse) : {};
      } catch (error) {
        reject(new MeetingUploadError('invalidResponse', (error as Error).message));
        return;
      }

      const meetingId = extractMeetingId(payload);
      if (!meetingId) {
        reject(new MeetingUploadError('missingMeetingId'));
        return;
      }

      withProgressCallback(file, options, {
        loaded: file.size,
        total: file.size || undefined,
        percent: file.size ? 100 : null,
      });

      resolve(meetingId);
    };

    const formData = new FormData();
    formData.append('file', file);
    xhr.send(formData);
  });
}

const shouldUseMock = import.meta.env.VITE_USE_UPLOAD_MOCK === 'true';

export async function uploadMeetingAudio(file: File, options?: UploadOptions): Promise<string> {
  if (shouldUseMock) {
    return mockMeetingUpload(file, options);
  }

  return requestUpload(file, options);
}
