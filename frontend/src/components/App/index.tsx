import React from 'react';
import { useTranslations } from 'next-intl';
import Dialog from '../Dialog';
import styles from './styles.module.css';

export function App() {
  const t = useTranslations();
  return (
    <div className={styles.container}>
      <h1 className={styles.title}>{t('title')}</h1>
      <Dialog triggerText={t('openDialog')}>
        <p>{t('dialogText')}</p>
      </Dialog>
    </div>
  );
}

export default App;
