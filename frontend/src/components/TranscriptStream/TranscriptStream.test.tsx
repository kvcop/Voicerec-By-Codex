import React from 'react';
import { describe, expect, it, beforeEach, afterEach } from 'vitest';
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TranslationProvider, Locale } from '../../i18n';
import TranscriptStream, { EventSourceFactory } from './index';

/* eslint-disable-next-line no-unused-vars */
type GenericListener = (payload: unknown) => void;

class MockEventSource {
  public static instances: MockEventSource[] = [];
  public readonly url: string;
  public onopen: (() => void) | null = null;
<<<<<< codex/2025-09-27-add-frontend-upload-form-for-wav
  public onmessage: ((data: string) => void) | null = null;
=======
>>>>>> main
  public onerror: (() => void) | null = null;
  private closed = false;
  private readonly listeners: Record<string, Set<GenericListener>> = {};

  constructor(url: string) {
    this.url = url;
    MockEventSource.instances.push(this);
  }

  addEventListener(type: string, listener: GenericListener) {
    if (!this.listeners[type]) {
      this.listeners[type] = new Set();
    }
    this.listeners[type].add(listener);
  }

  removeEventListener(type: string, listener: GenericListener) {
    this.listeners[type]?.delete(listener);
    if (this.listeners[type] && this.listeners[type]?.size === 0) {
      delete this.listeners[type];
    }
  }

  private emit(type: string, payload: unknown) {
    if (this.closed) {
      return;
    }
    const data = typeof payload === 'string' ? payload : JSON.stringify(payload);
    const event = { data };
    this.listeners[type]?.forEach((listener) => {
      listener(event);
    });
  }

  emitOpen() {
    if (this.closed) {
      return;
    }
    this.onopen?.();
  }

  emitTranscript(payload: unknown) {
    this.emit('transcript', payload);
  }

  emitSummary(payload: unknown) {
    this.emit('summary', payload);
  }

  emitError() {
    if (this.closed) {
      return;
    }
    this.onerror?.();
  }

  close(): void {
    this.closed = true;
  }
}

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

describe('TranscriptStream', () => {
  beforeEach(() => {
    MockEventSource.instances = [];
  });

  afterEach(() => {
    MockEventSource.instances = [];
  });

  it('streams transcript updates and renders speaker labels', async () => {
    const factory = ((url: string) => new MockEventSource(url)) as EventSourceFactory;
    renderWithIntl(<TranscriptStream meetingId="meeting-42" eventSourceFactory={factory} />);

    expect(MockEventSource.instances).toHaveLength(1);
    expect(MockEventSource.instances[0].url).toBe('/api/meeting/meeting-42/stream');
    expect(
      screen.getByText('Connecting to live transcript…', { exact: false })
    ).toBeTruthy();

    await act(async () => {
      MockEventSource.instances[0].emitOpen();
    });

    await waitFor(() =>
      expect(
        screen.getByText('Live transcription in progress', { exact: false })
      ).toBeTruthy(),
    );

    await act(async () => {
      MockEventSource.instances[0].emitTranscript({
        id: 'chunk-1',
        text: 'Добро пожаловать',
        speaker: 'Speaker 1',
      });
    });

    const transcriptItem = await screen.findByRole('listitem');
    expect(transcriptItem.textContent?.replace(/\s+/g, ' ').trim()).toBe(
      'Speaker 1: Добро пожаловать',
    );

    await act(async () => {
      MockEventSource.instances[0].emitSummary({
        summary: 'Основные итоги встречи',
      });
    });

    expect(
      await screen.findByRole('heading', { level: 3, name: 'Meeting summary' })
    ).toBeTruthy();
    expect(screen.getByText('Основные итоги встречи')).toBeTruthy();
  });

  it('shows an error status when the stream fails', async () => {
    const factory = ((url: string) => new MockEventSource(url)) as EventSourceFactory;
    renderWithIntl(<TranscriptStream meetingId="meeting-42" eventSourceFactory={factory} />);

    await act(async () => {
      MockEventSource.instances[0].emitOpen();
    });
    await act(async () => {
      MockEventSource.instances[0].emitError();
    });

    await waitFor(() =>
      expect(screen.getByText('Connection lost. Please retry.')).toBeTruthy(),
    );
  });

  it('falls back to unsupported state when EventSource is unavailable', () => {
    const globalWindow = globalThis as { EventSource?: unknown };
    const original = globalWindow.EventSource;
    globalWindow.EventSource = undefined;

    renderWithIntl(<TranscriptStream meetingId="meeting-99" />);

    expect(
      screen.getByText('Live transcript is unavailable in this environment.', {
        selector: 'p',
      }),
    ).toBeTruthy();

    if (typeof original !== 'undefined') {
      globalWindow.EventSource = original;
    } else {
      delete globalWindow.EventSource;
    }
  });

<<<<<< codex/2025-09-27-add-frontend-upload-form-for-wav
  it('resets state and reconnects when meetingId changes', async () => {
    const factory = ((url: string) => new MockEventSource(url)) as EventSourceFactory;

    const TestHarness: React.FC = () => {
      const [currentId, setCurrentId] = React.useState('meeting-a');

      return (
        <div>
          <button type="button" onClick={() => setCurrentId('meeting-b')}>
            change
          </button>
          <TranscriptStream meetingId={currentId} eventSourceFactory={factory} />
        </div>
      );
    };

    renderWithIntl(<TestHarness />);

    expect(MockEventSource.instances).toHaveLength(1);
    await act(async () => {
      MockEventSource.instances[0].emitOpen();
      MockEventSource.instances[0].emitMessage({ text: 'First message' });
    });

    expect(await screen.findByText('First message')).toBeTruthy();

    await userEvent.click(screen.getByRole('button', { name: 'change' }));

    await waitFor(() => expect(MockEventSource.instances).toHaveLength(2));
    expect(MockEventSource.instances[1].url).toBe('/api/meeting/stream/meeting-b');

    await waitFor(() =>
      expect(
        screen.getByText('Waiting for transcript updates…', { selector: 'p' })
      ).toBeTruthy(),
    );
=======
  it('creates a meeting-specific stream endpoint on meeting change', async () => {
    const factory = ((url: string) => new MockEventSource(url)) as EventSourceFactory;
    const { rerender } = renderWithIntl(
      <TranscriptStream meetingId="meeting-1" eventSourceFactory={factory} />,
    );

    expect(MockEventSource.instances).toHaveLength(1);
    expect(MockEventSource.instances[0].url).toBe('/api/meeting/meeting-1/stream');

    await act(async () => {
      rerender(<TranscriptStream meetingId="meeting-2" eventSourceFactory={factory} />);
    });

    expect(MockEventSource.instances).toHaveLength(2);
    expect(MockEventSource.instances[1].url).toBe('/api/meeting/meeting-2/stream');
>>>>>> main
  });
});
