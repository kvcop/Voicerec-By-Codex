import React from 'react';
import ReactDOM from 'react-dom/client';
import { NextIntlClientProvider } from 'next-intl';
import en from './locales/en.json';
import ru from './locales/ru.json';
import { App } from './components/App';

const messages = { en, ru } as const;

const rootElement = typeof document === 'undefined' ? null : document.getElementById('root');
export function Root() {
  const [locale, setLocale] = React.useState(() => {
    if (typeof window === 'undefined') return 'en';
    return localStorage.getItem('lang') || navigator.language.split('-')[0];
  });

  React.useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('lang', locale);
    }
  }, [locale]);

  const switchLang = () => setLocale(locale === 'en' ? 'ru' : 'en');

  return (
    <NextIntlClientProvider locale={locale} messages={messages[locale]}>
      <button onClick={switchLang} data-testid="switch">
        {locale === 'en' ? 'RU' : 'EN'}
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
