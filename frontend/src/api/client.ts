import { loadToken } from '../auth/tokenStorage';

export async function authorizedFetch(input: RequestInfo | URL, init: RequestInit = {}) {
  const token = loadToken();
  if (!token) {
    return fetch(input, init);
  }

  const headers = new Headers(init.headers ?? {});
  if (!headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  return fetch(input, { ...init, headers });
}
