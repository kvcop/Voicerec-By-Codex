import React from 'react';
import ReactDOM from 'react-dom/client';
import { NextIntlClientProvider } from 'next-intl';
import en from './locales/en.json';
import ru from './locales/ru.json';
import { App } from './components/App';

const messages = { en, ru } as const;
type Locale = keyof typeof messages;

function isSupportedLocale(locale: string | null): locale is Locale {
  return !!locale && Object.prototype.hasOwnProperty.call(messages, locale);
}

function getInitialLocale(): string {
  if (typeof window === 'undefined') {
    return 'en';
  }

  const storedLocale = localStorage.getItem('lang');
  if (storedLocale) {
    return storedLocale;
  }

  if (typeof navigator !== 'undefined') {
    return navigator.language.split('-')[0];
  }

  return 'en';
}

const rootElement = typeof document === 'undefined' ? null : document.getElementById('root');
export function Root() {
  const [locale, setLocale] = React.useState<string>(getInitialLocale);

  const effectiveLocale = React.useMemo<Locale>(() => {
    if (isSupportedLocale(locale)) {
      return locale;
    }
    return 'en';
  }, [locale]);

  React.useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('lang', effectiveLocale);
    }
  }, [effectiveLocale]);

  const switchLang = React.useCallback(() => {
    setLocale(effectiveLocale === 'en' ? 'ru' : 'en');
  }, [effectiveLocale]);

  return (
    <NextIntlClientProvider locale={effectiveLocale} messages={messages[effectiveLocale]}>
      <button onClick={switchLang} data-testid="switch">
        {effectiveLocale === 'en' ? 'RU' : 'EN'}
      </button>
      <App />
    </NextIntlClientProvider>
  );
}

if (rootElement) {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <Root />
    </React.StrictMode>
  );
}

export default App;
