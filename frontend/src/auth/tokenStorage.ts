export const TOKEN_STORAGE_KEY = 'authToken';

function getBrowserStorage(): Storage | null {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    return window.localStorage;
  } catch (error) {
    console.warn('Unable to access localStorage:', error);
    return null;
  }
}

const memoryStorage: { token: string | null } = { token: null };

export function loadToken(): string | null {
  const storage = getBrowserStorage();
  if (storage) {
    const stored = storage.getItem(TOKEN_STORAGE_KEY);
    if (typeof stored === 'string' && stored.trim()) {
      memoryStorage.token = stored;
      return stored;
    }
    memoryStorage.token = null;
    return null;
  }

  return memoryStorage.token;
}

export function persistToken(token: string | null): void {
  const storage = getBrowserStorage();
  if (storage) {
    if (token && token.trim()) {
      storage.setItem(TOKEN_STORAGE_KEY, token);
    } else {
      storage.removeItem(TOKEN_STORAGE_KEY);
    }
  }

  memoryStorage.token = token && token.trim() ? token : null;
}

export function clearToken(): void {
  persistToken(null);
}
