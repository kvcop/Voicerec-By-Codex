import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Root } from './main';

beforeEach(() => {
  localStorage.clear();
});

describe('language switch', () => {
  it('persists language choice', async () => {
    localStorage.setItem('lang', 'ru');
    render(<Root />);
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Войсерек');
    const button = screen.getByTestId('switch');
    await userEvent.click(button);
    await waitFor(() => expect(localStorage.getItem('lang')).toBe('en'));
  });

  it('falls back to English when stored locale is unsupported', async () => {
    localStorage.setItem('lang', 'de');
    render(<Root />);
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Voicerec');
    await waitFor(() => expect(localStorage.getItem('lang')).toBe('en'));
  });

  it('updates close button text when language changes', async () => {
    render(<Root />);

    await userEvent.click(screen.getByRole('button', { name: 'Open Dialog' }));
    const closeButtonEn = await screen.findByRole('button', { name: 'Close' });
    expect(closeButtonEn.textContent).toBe('Close');

    await userEvent.click(closeButtonEn);

    await userEvent.click(screen.getByTestId('switch'));
    await waitFor(() =>
      expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Войсерек')
    );

    await userEvent.click(screen.getByRole('button', { name: 'Открыть диалог' }));
    const closeButtonRu = await screen.findByRole('button', { name: 'Закрыть' });
    expect(closeButtonRu.textContent).toBe('Закрыть');
  });
});
