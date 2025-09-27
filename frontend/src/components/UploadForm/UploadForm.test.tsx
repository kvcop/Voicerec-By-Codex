import React from 'react';
import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
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
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    globalThis.fetch = originalFetch;
  });

  it('submits a WAV file and reports success', async () => {
    const user = userEvent.setup();
    const onMeetingReady = vi.fn();
    const mockResponse = new Response(JSON.stringify({ meeting_id: 'meeting-777' }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });

    const fetchMock = vi.fn().mockResolvedValue(mockResponse as Response);
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    renderWithIntl(<UploadForm onMeetingReady={onMeetingReady} />);

    const fileInput = screen.getByLabelText('Choose WAV file') as HTMLInputElement;
    const file = new File(['123'], 'call.wav', { type: 'audio/wav' });
    await user.upload(fileInput, file);

    await user.click(screen.getByRole('button', { name: 'Upload' }));

    await waitFor(() => expect(onMeetingReady).toHaveBeenCalledWith('meeting-777'));
    expect(
      screen.getByText('Meeting uploaded. ID: meeting-777', { exact: false })
    ).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const requestInit = fetchMock.mock.calls[0][1];
    expect(requestInit?.method).toBe('POST');
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
    const mockResponse = new Response(JSON.stringify({}), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });

    const fetchMock = vi.fn().mockResolvedValue(mockResponse as Response);
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    renderWithIntl(<UploadForm onMeetingReady={onMeetingReady} />);

    const fileInput = screen.getByLabelText('Choose WAV file') as HTMLInputElement;
    const file = new File(['123'], 'call.wav', { type: 'audio/wav' });
    await user.upload(fileInput, file);

    await user.click(screen.getByRole('button', { name: 'Upload' }));

    await waitFor(() =>
      expect(screen.getByText('The server did not provide a meeting ID.')).toBeTruthy(),
    );
    expect(onMeetingReady).not.toHaveBeenCalled();
  });
});
