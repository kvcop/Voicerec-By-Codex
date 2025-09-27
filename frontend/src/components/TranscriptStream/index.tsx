/* global EventSource */
import React from 'react';
import { useTranslations } from '../../i18n';
import styles from './styles.module.css';

type ConnectionState = 'connecting' | 'open' | 'error' | 'unsupported';

export type EventSourceFactory = (url: string) => EventSource; // eslint-disable-line no-unused-vars

interface TranscriptChunk {
  id?: string;
  text: string;
  speaker?: string | null;
}

export interface TranscriptStreamProps {
  meetingId: string;
  eventSourceFactory?: EventSourceFactory;
}

function isEventSourceSupported(): boolean {
  return typeof window !== 'undefined' && typeof window.EventSource !== 'undefined';
}

function parseTranscriptData(raw: string): TranscriptChunk | null {
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    const text = typeof parsed.text === 'string' ? parsed.text.trim() : '';
    if (!text) {
      return null;
    }

    return {
      id: typeof parsed.id === 'string' ? parsed.id : undefined,
      text,
      speaker:
        typeof parsed.speaker === 'string' && parsed.speaker.trim()
          ? parsed.speaker
          : null,
    };
  } catch {
    const text = raw.trim();
    if (!text || text === '[DONE]') {
      return null;
    }

    return { text };
  }
}

function parseSummaryData(raw: string): string | null {
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    const summaryCandidate =
      typeof parsed.summary === 'string'
        ? parsed.summary
        : typeof parsed.text === 'string'
          ? parsed.text
          : '';
    const summary = summaryCandidate.trim();
    return summary ? summary : null;
  } catch {
    const summary = raw.trim();
    if (!summary || summary === '[DONE]') {
      return null;
    }
    return summary;
  }
}

function extractEventData(event: unknown): string {
  if (typeof event === 'string') {
    return event;
  }

  if (
    typeof event === 'object' &&
    event !== null &&
    'data' in event &&
    typeof (event as { data?: unknown }).data === 'string'
  ) {
    return (event as { data: string }).data;
  }

  return '';
}

function resolveDefaultFactory(): EventSourceFactory | null {
  if (!isEventSourceSupported()) {
    return null;
  }

  return (url: string) => new window.EventSource(url);
}

export default function TranscriptStream({
  meetingId,
  eventSourceFactory,
}: TranscriptStreamProps) {
  const t = useTranslations();
  const [connectionState, setConnectionState] = React.useState<ConnectionState>(() =>
    isEventSourceSupported() ? 'connecting' : 'unsupported'
  );
  const [transcriptChunks, setTranscriptChunks] = React.useState<TranscriptChunk[]>([]);
  const [summary, setSummary] = React.useState<string | null>(null);

  React.useEffect(() => {
    const factory = eventSourceFactory ?? resolveDefaultFactory();
    if (!factory) {
      setConnectionState('unsupported');
      return undefined;
    }

    const source = factory(`/api/meeting/stream/${meetingId}`);
    let isActive = true;

    setTranscriptChunks([]);
    setSummary(null);
    setConnectionState('connecting');

    const handleOpen = () => {
      if (!isActive) {
        return;
      }
      setConnectionState('open');
    };

    const handleTranscriptEvent = (event: unknown) => {
      if (!isActive) {
        return;
      }

      const chunk = parseTranscriptData(extractEventData(event));
      if (!chunk) {
        return;
      }

      setTranscriptChunks((previous) => [...previous, chunk]);
    };

    const handleSummaryEvent = (event: unknown) => {
      if (!isActive) {
        return;
      }

      const parsedSummary = parseSummaryData(extractEventData(event));
      if (!parsedSummary) {
        return;
      }

      setSummary(parsedSummary);
    };

    const handleError = () => {
      if (!isActive) {
        return;
      }

      setConnectionState('error');
      source.close();
    };

    source.onopen = handleOpen;
    const transcriptListener = (event: unknown) => {
      handleTranscriptEvent(event);
    };
    const summaryListener = (event: unknown) => {
      handleSummaryEvent(event);
    };
    source.addEventListener('transcript', transcriptListener as any);
    source.addEventListener('summary', summaryListener as any);
    source.onerror = handleError;

    return () => {
      isActive = false;
      source.onopen = null;
      source.removeEventListener('transcript', transcriptListener as any);
      source.removeEventListener('summary', summaryListener as any);
      source.onerror = null;
      source.close();
    };
  }, [meetingId, eventSourceFactory]);

  const statusLabel = React.useMemo(() => {
    switch (connectionState) {
      case 'open':
        return t('transcriptStream.status.open');
      case 'error':
        return t('transcriptStream.status.error');
      case 'unsupported':
        return t('transcriptStream.status.unsupported');
      case 'connecting':
      default:
        return t('transcriptStream.status.connecting');
    }
  }, [connectionState, t]);

  return (
    <section className={styles.container} aria-live="polite">
      <div className={styles.header}>
        <h2 className={styles.title}>{t('transcriptStream.title')}</h2>
        <span className={styles.status} data-state={connectionState}>
          {statusLabel}
        </span>
      </div>
      {connectionState === 'unsupported' ? (
        <p className={styles.placeholder}>{statusLabel}</p>
      ) : transcriptChunks.length === 0 ? (
        summary ? null : (
          <p className={styles.placeholder}>{t('transcriptStream.empty')}</p>
        )
      ) : (
        <ol className={styles.list}>
          {transcriptChunks.map((chunk, index) => {
            const key = chunk.id ?? `${index}-${chunk.text}`;
            return (
              <li key={key} className={styles.item}>
                {chunk.speaker ? (
                  <span>
                    <strong>{chunk.speaker}</strong>
                    <span className={styles.separator}>: </span>
                    {chunk.text}
                  </span>
                ) : (
                  chunk.text
                )}
              </li>
            );
          })}
        </ol>
      )}
      {summary ? (
        <div className={styles.summarySection}>
          <h3 className={styles.summaryTitle}>{t('transcriptStream.summary.title')}</h3>
          <p className={styles.summaryText}>{summary}</p>
        </div>
      ) : null}
    </section>
  );
}
