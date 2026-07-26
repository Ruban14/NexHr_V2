import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import { authApi } from '../api/auth';
import { extractErrorMessage } from '../api/client';
import type { LoginResponse, User } from '../types';
import { getUserFullName } from '../types';
import { tokenStorage } from './tokenStorage';

type AuthContextValue = {
  user: User | null;
  bootstrapping: boolean;
  loading: boolean;
  isAuthenticated: boolean;
  displayName: string;
  login: (email: string, password: string, rememberMe: boolean) => Promise<User>;
  register: (payload: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
  forgotPassword: (email: string) => Promise<void>;
  resetPassword: (token: string, password: string) => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<User>;
  verifyEmail: (token: string) => Promise<void>;
  resendVerification: (email: string) => Promise<void>;
  getAccessToken: () => string | null;
  establishSession: (response: LoginResponse, rememberMe?: boolean) => void;
  setUser: (user: User | null) => void;
  refreshUser: () => Promise<User | null>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [bootstrapping, setBootstrapping] = useState(true);
  const [loading, setLoading] = useState(false);

  const clearSession = useCallback(() => {
    setUser(null);
    tokenStorage.clear();
  }, []);

  const establishSession = useCallback((response: LoginResponse, rememberMe = true) => {
    tokenStorage.setTokens(response.tokens.access, response.tokens.refresh, rememberMe);
    setUser(response.user);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      const access = tokenStorage.getAccessToken();
      const refresh = tokenStorage.getRefreshToken();
      if (!access && !refresh) {
        if (!cancelled) setBootstrapping(false);
        return;
      }

      try {
        const me = await authApi.me(access ?? '');
        if (!cancelled) setUser(me);
      } catch {
        if (!cancelled) clearSession();
      } finally {
        if (!cancelled) setBootstrapping(false);
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, [clearSession]);

  const login = useCallback(
    async (email: string, password: string, rememberMe: boolean) => {
      setLoading(true);
      try {
        const response = await authApi.login({ email, password });
        establishSession(response, rememberMe);
        return response.user;
      } finally {
        setLoading(false);
      }
    },
    [establishSession],
  );

  const register = useCallback(
    async (payload: {
      email: string;
      password: string;
      first_name: string;
      last_name: string;
    }) => {
      setLoading(true);
      try {
        await authApi.register(payload);
        clearSession();
      } finally {
        setLoading(false);
      }
    },
    [clearSession],
  );

  const logout = useCallback(async () => {
    setLoading(true);
    try {
      const refresh = tokenStorage.getRefreshToken();
      const access = tokenStorage.getAccessToken();
      if (refresh && access) {
        try {
          await authApi.logout(refresh, access);
        } catch {
          // ignore logout API failures
        }
      }
      clearSession();
    } finally {
      setLoading(false);
    }
  }, [clearSession]);

  const forgotPassword = useCallback(async (email: string) => {
    setLoading(true);
    try {
      await authApi.forgotPassword(email);
    } finally {
      setLoading(false);
    }
  }, []);

  const resetPassword = useCallback(async (token: string, password: string) => {
    setLoading(true);
    try {
      await authApi.resetPassword({ token, password });
    } finally {
      setLoading(false);
    }
  }, []);

  const changePassword = useCallback(async (currentPassword: string, newPassword: string) => {
    const access = tokenStorage.getAccessToken();
    if (!access) {
      throw new Error('Not authenticated.');
    }
    setLoading(true);
    try {
      const updated = await authApi.changePassword(access, {
        current_password: currentPassword,
        password: newPassword,
      });
      setUser(updated);
      return updated;
    } finally {
      setLoading(false);
    }
  }, []);

  const verifyEmail = useCallback(async (token: string) => {
    setLoading(true);
    try {
      await authApi.verifyEmail(token);
    } finally {
      setLoading(false);
    }
  }, []);

  const resendVerification = useCallback(async (email: string) => {
    setLoading(true);
    try {
      await authApi.resendVerification(email);
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshUser = useCallback(async () => {
    const access = tokenStorage.getAccessToken();
    if (!access) {
      setUser(null);
      return null;
    }
    try {
      const me = await authApi.me(access);
      setUser(me);
      return me;
    } catch {
      return null;
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      bootstrapping,
      loading,
      isAuthenticated: !!user,
      displayName: user ? getUserFullName(user) : '',
      login,
      register,
      logout,
      forgotPassword,
      resetPassword,
      changePassword,
      verifyEmail,
      resendVerification,
      getAccessToken: () => tokenStorage.getAccessToken(),
      establishSession,
      setUser,
      refreshUser,
    }),
    [
      user,
      bootstrapping,
      loading,
      login,
      register,
      logout,
      forgotPassword,
      resetPassword,
      changePassword,
      verifyEmail,
      resendVerification,
      establishSession,
      refreshUser,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}

export { extractErrorMessage };
