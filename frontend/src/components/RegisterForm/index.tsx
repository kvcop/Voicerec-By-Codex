import React from 'react';
import { useTranslations } from '../../i18n';
import { RegisterError, register, LoginError } from '../../api/auth';
import { useAuth } from '../AuthProvider';
import styles from './styles.module.css';

interface RegisterFormProps {
  className?: string;
  onRequestLogin?: () => void;
}

export default function RegisterForm({ className, onRequestLogin }: RegisterFormProps) {
  const t = useTranslations();
  const { login } = useAuth();
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [confirmPassword, setConfirmPassword] = React.useState('');
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (password.length < 8) {
      setError(t('auth.register.error.passwordLength'));
      return;
    }

    if (password !== confirmPassword) {
      setError(t('auth.register.error.passwordMismatch'));
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await register({ email, password });
      await login({ email, password });
    } catch (submissionError) {
      if (submissionError instanceof RegisterError) {
        const key =
          submissionError.reason === 'validation'
            ? 'auth.register.error.validation'
            : 'auth.register.error.generic';
        setError(t(key));
      } else if (submissionError instanceof LoginError) {
        setError(t('auth.register.error.generic'));
      } else {
        setError(t('auth.register.error.generic'));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const containerClassName = [styles.container, className].filter(Boolean).join(' ');

  return (
    <section className={containerClassName}>
      <h2 className={styles.title}>{t('auth.register.title')}</h2>
      <p className={styles.description}>{t('auth.register.description')}</p>
      <form className={styles.form} onSubmit={handleSubmit}>
        <label className={styles.label} htmlFor="register-email">
          {t('auth.register.emailLabel')}
        </label>
        <input
          id="register-email"
          name="email"
          type="email"
          autoComplete="email"
          className={styles.input}
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          disabled={isSubmitting}
          required
        />
        <label className={styles.label} htmlFor="register-password">
          {t('auth.register.passwordLabel')}
        </label>
        <input
          id="register-password"
          name="password"
          type="password"
          autoComplete="new-password"
          className={styles.input}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          disabled={isSubmitting}
          required
        />
        <label className={styles.label} htmlFor="register-confirm-password">
          {t('auth.register.confirmPasswordLabel')}
        </label>
        <input
          id="register-confirm-password"
          name="confirmPassword"
          type="password"
          autoComplete="new-password"
          className={styles.input}
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          disabled={isSubmitting}
          required
        />
        <button type="submit" className={styles.submit} disabled={isSubmitting}>
          {isSubmitting ? t('auth.register.submitting') : t('auth.register.submit')}
        </button>
      </form>
      {error ? (
        <p className={styles.error} role="alert">
          {error}
        </p>
      ) : null}
      {onRequestLogin ? (
        <p className={styles.helper}>
          {t('auth.register.haveAccount')}{' '}
          <button type="button" className={styles.linkButton} onClick={onRequestLogin}>
            {t('auth.register.switchToLogin')}
          </button>
        </p>
      ) : null}
    </section>
  );
}
