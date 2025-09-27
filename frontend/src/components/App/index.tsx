import React from 'react';
import { useTranslations } from '../../i18n';
import Dialog from '../Dialog';
import TranscriptStream from '../TranscriptStream';
import UploadForm from '../UploadForm';
import styles from './styles.module.css';

export function App() {
  const t = useTranslations();
  const [meetingId, setMeetingId] = React.useState<string | null>(null);

  const handleMeetingReady = React.useCallback((id: string) => {
    setMeetingId(id);
  }, []);

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>{t('title')}</h1>
      <div className={styles.content}>
        <Dialog triggerText={t('openDialog')}>
          <p>{t('dialogText')}</p>
        </Dialog>
        <UploadForm onMeetingReady={handleMeetingReady} className={styles.upload} />
        {meetingId ? (
          <TranscriptStream key={meetingId} meetingId={meetingId} />
        ) : (
          <section className={styles.streamPlaceholder}>
            <h2 className={styles.streamPlaceholderTitle}>{t('transcriptStream.title')}</h2>
            <p className={styles.streamPlaceholderText}>
              {t('transcriptStream.placeholder.noMeeting')}
            </p>
          </section>
        )}
      </div>
    </div>
  );
}

export default App;
