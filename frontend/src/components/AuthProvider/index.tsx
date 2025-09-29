import React from 'react';
import { login as requestLogin, LoginCredentials } from '../../api/auth';
import { clearToken, loadToken, persistToken, TOKEN_STORAGE_KEY } from '../../auth/tokenStorage';

interface AuthContextValue {
  token: string | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
}

const AuthContext = React.createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = React.useState<string | null>(() => loadToken());

  const handleLogin = React.useCallback(async (credentials: LoginCredentials) => {
    const jwt = await requestLogin(credentials);
    persistToken(jwt);
    setToken(jwt);
  }, []);

  const handleLogout = React.useCallback(() => {
    clearToken();
    setToken(null);
  }, []);

  React.useEffect(() => {
    if (typeof window === 'undefined') {
      return undefined;
    }

    const handleStorage = (event: StorageEvent) => {
      if (event.key === TOKEN_STORAGE_KEY) {
        setToken(loadToken());
      }
    };

    window.addEventListener('storage', handleStorage);
    return () => {
      window.removeEventListener('storage', handleStorage);
    };
  }, []);

  const contextValue = React.useMemo<AuthContextValue>(
    () => ({
      token,
      isAuthenticated: Boolean(token),
      login: handleLogin,
      logout: handleLogout,
    }),
    [token, handleLogin, handleLogout]
  );

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
