import { mockMeetingUpload } from '../mocks/meetingUpload';
import { authorizedFetch } from './client';

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

function extractMeetingId(payload: UploadResponse): string | null {
  const candidate = payload.meeting_id ?? payload.meetingId;
  return typeof candidate === 'string' && candidate.trim() ? candidate : null;
}

async function requestUpload(file: File): Promise<string> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await authorizedFetch('/api/meeting/upload', {
    method: 'POST',
    body: formData,
  });

  if (response.status === 401 || response.status === 403) {
    throw new MeetingUploadError('unauthorized');
  }

  if (!response.ok) {
    throw new MeetingUploadError('network');
  }

  let payload: UploadResponse;
  try {
    payload = (await response.json()) as UploadResponse;
  } catch (error) {
    throw new MeetingUploadError('invalidResponse', (error as Error).message);
  }

  const meetingId = extractMeetingId(payload);
  if (!meetingId) {
    throw new MeetingUploadError('missingMeetingId');
  }

  return meetingId;
}

const shouldUseMock = import.meta.env.VITE_USE_UPLOAD_MOCK === 'true';

export async function uploadMeetingAudio(file: File): Promise<string> {
  if (shouldUseMock) {
    return mockMeetingUpload(file);
  }

  return requestUpload(file);
}
