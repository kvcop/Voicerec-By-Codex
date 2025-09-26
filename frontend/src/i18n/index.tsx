import React from 'react';
import en from '../locales/en.json';
import ru from '../locales/ru.json';

export const messages = { en, ru } as const;
export type Locale = keyof typeof messages;
type AppMessages = (typeof messages)[Locale];
type LocaleChangeHandler = React.Dispatch<Locale>;

interface TranslationContextValue {
  locale: Locale;
  messages: AppMessages;
  setLocale: LocaleChangeHandler;
}

const TranslationContext = React.createContext<TranslationContextValue | undefined>(
  undefined,
);

export interface TranslationProviderProps {
  locale: Locale;
  onLocaleChange: LocaleChangeHandler;
  children: React.ReactNode;
}

export function TranslationProvider({
  locale,
  onLocaleChange,
  children,
}: TranslationProviderProps) {
  const contextValue = React.useMemo(
    () => ({
      locale,
      messages: messages[locale],
      setLocale: onLocaleChange,
    }),
    [locale, onLocaleChange],
  );

  return (
    <TranslationContext.Provider value={contextValue}>
      {children}
    </TranslationContext.Provider>
  );
}

export function useLocale() {
  const context = React.useContext(TranslationContext);
  if (!context) {
    throw new Error('useLocale must be used within a TranslationProvider');
  }

  return { locale: context.locale, setLocale: context.setLocale };
}

export function useTranslations() {
  const context = React.useContext(TranslationContext);
  if (!context) {
    throw new Error('useTranslations must be used within a TranslationProvider');
  }

  return <Key extends keyof AppMessages>(key: Key): AppMessages[Key] =>
    context.messages[key];
}

export function isSupportedLocale(locale: string | null): locale is Locale {
  return Boolean(
    locale && Object.prototype.hasOwnProperty.call(messages, locale),
  );
}
