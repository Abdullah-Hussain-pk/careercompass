import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react';
import { auth as authApi, getToken, setToken, clearToken } from '../api/client';
import type { UserOut } from '../types';

interface AuthContextValue {
  user: UserOut | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (email: string, password: string, full_name: string) => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(() => {
    const cached = localStorage.getItem('cc_user');
    return cached ? (JSON.parse(cached) as UserOut) : null;
  });
  const [token, setTokenState] = useState<string | null>(getToken);
  const [loading, setLoading] = useState<boolean>(!!getToken());

  const refreshUser = useCallback(async () => {
    try {
      const me = await authApi.me();
      setUser(me);
      localStorage.setItem('cc_user', JSON.stringify(me));
    } catch {
      clearToken();
      setUser(null);
      setTokenState(null);
    }
  }, []);

  // On mount, verify token is still valid
  useEffect(() => {
    if (getToken()) {
      refreshUser().finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [refreshUser]);

  const login = useCallback(async (email: string, password: string) => {
    const res = await authApi.login(email, password);
    setToken(res.access_token);
    setTokenState(res.access_token);
    const me = await authApi.me();
    setUser(me);
    localStorage.setItem('cc_user', JSON.stringify(me));
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    setTokenState(null);
    window.location.href = '/login';
  }, []);

  const register = useCallback(
    async (email: string, password: string, full_name: string) => {
      await authApi.register({ email, password, full_name });
      // Auto-login after register
      await login(email, password);
    },
    [login],
  );

  return (
    <AuthContext.Provider
      value={{ user, token, loading, login, logout, register, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
