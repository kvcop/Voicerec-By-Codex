import React from 'react';
import { useTranslations } from '../../i18n';
import Dialog from '../Dialog';
import TranscriptStream from '../TranscriptStream';
import UploadForm from '../UploadForm';
import LoginForm from '../LoginForm';
import RegisterForm from '../RegisterForm';
import { useAuth } from '../AuthProvider';
import styles from './styles.module.css';

export function App() {
  const t = useTranslations();
  const { isAuthenticated, logout } = useAuth();
  const [meetingId, setMeetingId] = React.useState<string | null>(null);
  const [authView, setAuthView] = React.useState<'login' | 'register'>('login');

  const handleMeetingReady = React.useCallback((id: string) => {
    setMeetingId(id);
  }, []);

  const handleShowLogin = React.useCallback(() => {
    setAuthView('login');
  }, []);

  const handleShowRegister = React.useCallback(() => {
    setAuthView('register');
  }, []);

  React.useEffect(() => {
    if (!isAuthenticated) {
      setMeetingId(null);
    }
  }, [isAuthenticated]);

  React.useEffect(() => {
    if (isAuthenticated) {
      setAuthView('login');
    }
  }, [isAuthenticated]);

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>{t('title')}</h1>
      <div className={styles.content}>
        <Dialog triggerText={t('openDialog')}>
          <p>{t('dialogText')}</p>
        </Dialog>
        {isAuthenticated ? (
          <>
            <div className={styles.authActions}>
              <button type="button" className={styles.logoutButton} onClick={logout}>
                {t('auth.logout')}
              </button>
            </div>
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
          </>
        ) : authView === 'login' ? (
          <LoginForm className={styles.login} onRequestRegister={handleShowRegister} />
        ) : (
          <RegisterForm className={styles.login} onRequestLogin={handleShowLogin} />
        )}
      </div>
    </div>
  );
}

export default App;
