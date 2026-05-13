import {
    createContext,
    useCallback,
    useContext,
    useMemo,
    useState,
    type ReactNode,
  } from "react";
  import { clearToken, getToken, setToken as persistToken } from "./tokenStorage";
  
  type AuthContextValue = {
    token: string | null;
    setToken: (token: string | null) => void;
    logout: () => void;
  };
  
  const AuthContext = createContext<AuthContextValue | null>(null);
  
  export function AuthProvider({ children }: { children: ReactNode }) {
    const [token, setTokenState] = useState<string | null>(() => getToken());
  
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
    }, []);
  
    const value = useMemo(
      () => ({ token, setToken, logout }),
      [token, setToken, logout],
    );
  
    return (
      <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
    );
  }
  
  export function useAuth(): AuthContextValue {
    const ctx = useContext(AuthContext);
    if (ctx === null) {
      throw new Error("useAuth must be used within AuthProvider");
    }
    return ctx;
  }