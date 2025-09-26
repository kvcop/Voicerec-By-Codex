import { describe, it, expect, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { Root } from './main';

describe('App snapshot', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('matches the initial render snapshot', () => {
    const { container } = render(<Root />);
    expect(container).toMatchSnapshot();
  });
});
