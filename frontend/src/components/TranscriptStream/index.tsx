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

function parseEventData(raw: string): TranscriptChunk | null {
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
  const [chunks, setChunks] = React.useState<TranscriptChunk[]>([]);

  React.useEffect(() => {
    const factory = eventSourceFactory ?? resolveDefaultFactory();
    if (!factory) {
      setConnectionState('unsupported');
      return undefined;
    }

    const source = factory(`/api/meeting/stream/${meetingId}`);
    let isActive = true;

    setChunks([]);
    setConnectionState('connecting');

    const handleOpen = () => {
      if (!isActive) {
        return;
      }
      setConnectionState('open');
    };

    const handleMessage = (data: string) => {
      if (!isActive) {
        return;
      }

      const chunk = parseEventData(data);
      if (!chunk) {
        return;
      }

      setChunks((previous) => [...previous, chunk]);
    };

    const handleError = () => {
      if (!isActive) {
        return;
      }

      setConnectionState('error');
      source.close();
    };

    source.onopen = handleOpen;
    source.onmessage = (event) => {
      if (!isActive) {
        return;
      }
      const data =
        typeof event === 'string'
          ? event
          : (event as { data?: string }).data ?? '';
      handleMessage(data);
    };
    source.onerror = handleError;

    return () => {
      isActive = false;
      source.onopen = null;
      source.onmessage = null;
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
      ) : chunks.length === 0 ? (
        <p className={styles.placeholder}>{t('transcriptStream.empty')}</p>
      ) : (
        <ol className={styles.list}>
          {chunks.map((chunk, index) => {
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
    </section>
  );
}
