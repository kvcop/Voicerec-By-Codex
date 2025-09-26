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
    expect(screen.getByRole('heading').textContent).toBe('Войсерек');
    const button = screen.getByTestId('switch');
    await userEvent.click(button);
    await waitFor(() => expect(localStorage.getItem('lang')).toBe('en'));
  });

  it('falls back to English when stored locale is unsupported', async () => {
    localStorage.setItem('lang', 'de');
    render(<Root />);
    expect(screen.getByRole('heading').textContent).toBe('Voicerec');
    await waitFor(() => expect(localStorage.getItem('lang')).toBe('en'));
  });
});
