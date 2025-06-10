import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
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
    expect(localStorage.getItem('lang')).toBe('en');
  });
});
