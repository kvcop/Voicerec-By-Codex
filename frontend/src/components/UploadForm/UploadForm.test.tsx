import React from 'react';
import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest';
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UploadForm from './index';
import { TranslationProvider, Locale } from '../../i18n';

function renderWithIntl(ui: React.ReactElement, locale: Locale = 'en') {
  const Wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [currentLocale, setCurrentLocale] = React.useState<Locale>(locale);
    return (
      <TranslationProvider locale={currentLocale} onLocaleChange={setCurrentLocale}>
        {children}
      </TranslationProvider>
    );
  };

  return render(ui, { wrapper: Wrapper });
}

describe('UploadForm', () => {
  class MockXMLHttpRequest {
    public static instances: MockXMLHttpRequest[] = [];

    public method: string | null = null;
    public url: string | null = null;
    public requestHeaders: Record<string, string> = {};
    public responseText = '';
    public status = 0;
    public upload = { onprogress: null as ((event: ProgressEvent<EventTarget>) => void) | null };
    public onload: ((event: Event) => void) | null = null;
    public onerror: ((event: ProgressEvent<EventTarget>) => void) | null = null;
    public onabort: ((event: ProgressEvent<EventTarget>) => void) | null = null;
    public ontimeout: ((event: ProgressEvent<EventTarget>) => void) | null = null;

    open(method: string, url: string) {
      this.method = method;
      this.url = url;
    }

    setRequestHeader(name: string, value: string) {
      this.requestHeaders[name] = value;
    }

    send(_body?: Document | XMLHttpRequestBodyInit | null) {
      MockXMLHttpRequest.instances.push(this);
    }

    triggerProgress(loaded: number, total: number) {
      this.upload.onprogress?.({
        lengthComputable: true,
        loaded,
        total,
      } as ProgressEvent<EventTarget>);
    }

    succeed(body: string, status = 200) {
      this.status = status;
      this.responseText = body;
      this.onload?.(new Event('load'));
    }

    fail(status = 500) {
      this.status = status;
      this.onerror?.(new ProgressEvent('error'));
    }
  }

  const originalXHR = globalThis.XMLHttpRequest;

  beforeEach(() => {
    vi.restoreAllMocks();
    MockXMLHttpRequest.instances = [];
    globalThis.XMLHttpRequest = MockXMLHttpRequest as unknown as typeof XMLHttpRequest;
  });

  afterEach(() => {
    vi.restoreAllMocks();
    globalThis.XMLHttpRequest = originalXHR;
  });

  it('submits a WAV file and reports success', async () => {
    const user = userEvent.setup();
    const onMeetingReady = vi.fn();

    renderWithIntl(<UploadForm onMeetingReady={onMeetingReady} />);

    const fileInput = screen.getByLabelText(/drag & drop a wav file or click to browse/i) as HTMLInputElement;
    const file = new File(['123'], 'call.wav', { type: 'audio/wav' });
    await user.upload(fileInput, file);

    await user.click(screen.getByRole('button', { name: 'Upload' }));

    const instance = MockXMLHttpRequest.instances.at(-1);
    expect(instance).toBeDefined();

    act(() => {
      instance?.triggerProgress(5, 10);
    });

    await screen.findByText('Upload progress: 50%', {
      exact: false,
    });

    act(() => {
      instance?.succeed(JSON.stringify({ meeting_id: 'meeting-777' }));
    });

    await waitFor(() => expect(onMeetingReady).toHaveBeenCalledWith('meeting-777'));
    expect(
      screen.getByText('Meeting uploaded. ID: meeting-777', { exact: false })
    ).toBeTruthy();
    expect(instance?.method).toBe('POST');
    expect(instance?.url).toBe('/api/meeting/upload');
  });

  it('shows an error when no file is selected', async () => {
    const user = userEvent.setup();
    const onMeetingReady = vi.fn();

    renderWithIntl(<UploadForm onMeetingReady={onMeetingReady} />);

    await user.click(screen.getByRole('button', { name: 'Upload' }));

    expect(onMeetingReady).not.toHaveBeenCalled();
    expect(screen.getByText('Select a WAV file before uploading.')).toBeTruthy();
  });

  it('handles missing meeting ID responses', async () => {
    const user = userEvent.setup();
    const onMeetingReady = vi.fn();

    renderWithIntl(<UploadForm onMeetingReady={onMeetingReady} />);

    const fileInput = screen.getByLabelText(/drag & drop a wav file or click to browse/i) as HTMLInputElement;
    const file = new File(['123'], 'call.wav', { type: 'audio/wav' });
    await user.upload(fileInput, file);

    await user.click(screen.getByRole('button', { name: 'Upload' }));

    const instance = MockXMLHttpRequest.instances.at(-1);
    expect(instance).toBeDefined();

    act(() => {
      instance?.succeed(JSON.stringify({}));
    });

    await waitFor(() => {
      expect(screen.getByText('The server did not provide a meeting ID.')).toBeTruthy();
    });
    expect(onMeetingReady).not.toHaveBeenCalled();
  });
});
