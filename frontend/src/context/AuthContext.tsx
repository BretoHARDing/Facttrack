import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import { authApi } from '../api/client';
import type { User } from '../types';

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string, totpCode?: string) => Promise<{ mfaRequired: boolean }>;
  logout: () => Promise<void>;
  setUser: (u: User | null) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem('user');
    return stored ? JSON.parse(stored) : null;
  });

  const login = useCallback(async (email: string, password: string, totpCode?: string) => {
    const { data } = await authApi.login(email, password, totpCode);
    if (data.mfa_required) {
      return { mfaRequired: true };
    }
    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token);
    }
    // Minimal user placeholder — a real implementation would decode the JWT
    const u: User = { id: '', email, platform_role: 'case_investigator' };
    setUser(u);
    localStorage.setItem('user', JSON.stringify(u));
    return { mfaRequired: false };
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
