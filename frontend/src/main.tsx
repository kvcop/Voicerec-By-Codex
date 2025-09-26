import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './components/App';
import { TranslationProvider, isSupportedLocale, Locale } from './i18n';

function getInitialLocale(): Locale {
  if (typeof window === 'undefined') {
    return 'en';
  }

  const storedLocale = localStorage.getItem('lang');
  if (isSupportedLocale(storedLocale)) {
    return storedLocale;
  }

  if (typeof navigator !== 'undefined') {
    const browserLocale = navigator.language.split('-')[0];
    if (isSupportedLocale(browserLocale)) {
      return browserLocale;
    }
  }

  return 'en';
}

const rootElement = typeof document === 'undefined' ? null : document.getElementById('root');
export function Root() {
  const [locale, setLocale] = React.useState<Locale>(getInitialLocale);

  React.useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('lang', locale);
    }
  }, [locale]);

  const switchLang = React.useCallback(() => {
    setLocale((currentLocale) => (currentLocale === 'en' ? 'ru' : 'en'));
  }, []);

  return (
    <TranslationProvider locale={locale} onLocaleChange={setLocale}>
      <button onClick={switchLang} data-testid="switch">
        {locale === 'en' ? 'RU' : 'EN'}
      </button>
      <App />
    </TranslationProvider>
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
