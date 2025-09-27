import React from 'react';
import { useTranslations } from '../../i18n';
import Dialog from '../Dialog';
import TranscriptStream from '../TranscriptStream';
import styles from './styles.module.css';

export function App() {
  const t = useTranslations();
  return (
    <div className={styles.container}>
      <h1 className={styles.title}>{t('title')}</h1>
      <div className={styles.content}>
        <Dialog triggerText={t('openDialog')}>
          <p>{t('dialogText')}</p>
        </Dialog>
        <TranscriptStream meetingId="demo-meeting" />
      </div>
    </div>
  );
}

export default App;
