import React from 'react';
import { IntlProvider, useIntl } from 'react-intl';
import en from '../locales/en.json';
import ru from '../locales/ru.json';

export const messages = { en, ru } as const;
export type Locale = keyof typeof messages;
type AppMessages = (typeof messages)[Locale];
type MessageKey = keyof AppMessages & string;
type LocaleChangeHandler = React.Dispatch<React.SetStateAction<Locale>>;

interface TranslationContextValue {
  locale: Locale;
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
      setLocale: onLocaleChange,
    }),
    [locale, onLocaleChange],
  );

  return (
    <TranslationContext.Provider value={contextValue}>
      <IntlProvider locale={locale} messages={messages[locale]} defaultLocale="en">
        {children}
      </IntlProvider>
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
  const intl = useIntl();
  return React.useCallback(
    <Key extends MessageKey>(key: Key): AppMessages[Key] =>
      intl.formatMessage({ id: key }) as AppMessages[Key],
    [intl],
  );
}

export function isSupportedLocale(locale: string | null): locale is Locale {
  return Boolean(
    locale && Object.prototype.hasOwnProperty.call(messages, locale),
  );
}
