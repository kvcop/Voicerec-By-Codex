export interface LoginCredentials {
  email: string;
  password: string;
}

type LoginErrorReason = 'network' | 'invalidCredentials' | 'invalidResponse';

export class LoginError extends Error {
  public readonly reason: LoginErrorReason;

  constructor(reason: LoginErrorReason, message?: string) {
    super(message ?? reason);
    this.reason = reason;
  }
}

interface LoginResponse {
  access_token?: unknown;
  token?: unknown;
  jwt?: unknown;
}

function extractToken(payload: LoginResponse): string | null {
  const candidate = payload.access_token ?? payload.token ?? payload.jwt;
  return typeof candidate === 'string' && candidate.trim() ? candidate : null;
}

export async function login(credentials: LoginCredentials): Promise<string> {
  const response = await fetch('/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(credentials),
  });

  if (response.status === 401) {
    throw new LoginError('invalidCredentials');
  }

  if (!response.ok) {
    throw new LoginError('network');
  }

  let payload: LoginResponse;
  try {
    payload = (await response.json()) as LoginResponse;
  } catch (error) {
    throw new LoginError('invalidResponse', (error as Error).message);
  }

  const token = extractToken(payload);
  if (!token) {
    throw new LoginError('invalidResponse');
  }

  return token;
}
