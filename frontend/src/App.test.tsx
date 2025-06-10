import { describe, it, expect } from 'vitest';
import { App } from './main';

describe('sample test', () => {
  it('renders', () => {
    expect(typeof App).toBe('function');
  });
});
