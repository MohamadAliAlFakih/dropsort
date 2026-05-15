import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { apiFetch } from "../api/client";
import { routes } from "../api/routes";
import type { UserOut } from "../api/types";
import { clearToken, getToken, setToken as persistToken } from "./tokenStorage";

type AuthContextValue = {
  token: string | null;
  me: UserOut | null;
  meLoading: boolean;
  setToken: (token: string | null) => void;
  logout: () => void;
  refreshMe: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() => getToken());
  const [me, setMe] = useState<UserOut | null>(null);
  const [meLoading, setMeLoading] = useState(false);

  const setToken = useCallback((next: string | null) => {
    if (next === null) {
      clearToken();
    } else {
      persistToken(next);
    }
    setTokenState(getToken());
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setTokenState(null);
    setMe(null);
  }, []);

  const refreshMe = useCallback(async () => {
    const t = getToken();
    if (!t) {
      setMe(null);
      return;
    }
    setMeLoading(true);
    try {
      const res = await apiFetch(routes.me);
      if (res.status === 401) {
        logout();
        return;
      }
      if (!res.ok) {
        setMe(null);
        return;
      }
      const data = (await res.json()) as UserOut;
      setMe(data);
    } catch {
      setMe(null);
    } finally {
      setMeLoading(false);
    }
  }, [logout]);

  useEffect(() => {
    if (!token) {
      setMe(null);
      setMeLoading(false);
      return;
    }
    let cancelled = false;
    setMeLoading(true);
    void (async () => {
      try {
        const res = await apiFetch(routes.me);
        if (cancelled) {
          return;
        }
        if (res.status === 401) {
          logout();
          return;
        }
        if (!res.ok) {
          setMe(null);
          return;
        }
        const data = (await res.json()) as UserOut;
        if (!cancelled) {
          setMe(data);
        }
      } catch {
        if (!cancelled) {
          setMe(null);
        }
      } finally {
        if (!cancelled) {
          setMeLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, logout]);

  const value = useMemo(
    () => ({
      token,
      me,
      meLoading,
      setToken,
      logout,
      refreshMe,
    }),
    [token, me, meLoading, setToken, logout, refreshMe],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (ctx === null) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
