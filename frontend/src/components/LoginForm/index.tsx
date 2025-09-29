import React from 'react';
import { useTranslations } from '../../i18n';
import { useAuth } from '../AuthProvider';
import { LoginError } from '../../api/auth';
import styles from './styles.module.css';

interface LoginFormProps {
  className?: string;
  onRequestRegister?: () => void;
}

export default function LoginForm({ className, onRequestRegister }: LoginFormProps) {
  const t = useTranslations();
  const { login } = useAuth();
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      await login({ email, password });
    } catch (submissionError) {
      if (submissionError instanceof LoginError) {
        const key =
          submissionError.reason === 'invalidCredentials'
            ? 'auth.login.error.invalidCredentials'
            : 'auth.login.error.generic';
        setError(t(key));
      } else {
        setError(t('auth.login.error.generic'));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const containerClassName = [styles.container, className].filter(Boolean).join(' ');

  return (
    <section className={containerClassName}>
      <h2 className={styles.title}>{t('auth.login.title')}</h2>
      <form className={styles.form} onSubmit={handleSubmit}>
        <label className={styles.label} htmlFor="email">
          {t('auth.login.emailLabel')}
        </label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          className={styles.input}
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          disabled={isSubmitting}
          required
        />
        <label className={styles.label} htmlFor="password">
          {t('auth.login.passwordLabel')}
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          className={styles.input}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          disabled={isSubmitting}
          required
        />
        <button type="submit" className={styles.submit} disabled={isSubmitting}>
          {isSubmitting ? t('auth.login.submitting') : t('auth.login.submit')}
        </button>
      </form>
      {error ? (
        <p className={styles.error} role="alert">
          {error}
        </p>
      ) : null}
      {onRequestRegister ? (
        <p className={styles.helper}>
          {t('auth.login.noAccount')}{' '}
          <button type="button" className={styles.linkButton} onClick={onRequestRegister}>
            {t('auth.login.switchToRegister')}
          </button>
        </p>
      ) : null}
    </section>
  );
}
