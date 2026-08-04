import { createContext, useContext, useState, useEffect, ReactNode, FC } from 'react';
import { fetchMe } from '../api/authApi';

interface User {
  id: string;
  email: string;
  full_name?: string;
  active_planner_id?: string;
  [key: string]: any;
}

interface AuthContextType {
  token: string;
  user: User | null;
  loading: boolean;
  login: (newToken: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string>(localStorage.getItem('token') || '');
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Handle OAuth hash tokens on mount
  useEffect(() => {
    const hash = window.location.hash;
    if (hash) {
      const params = new URLSearchParams(hash.substring(1));
      const oauthToken = params.get('token');
      if (oauthToken) {
        localStorage.setItem('token', oauthToken);
        setToken(oauthToken);
      }
      window.history.replaceState(null, '', window.location.pathname);
    }
  }, []);

  // Fetch user when token changes
  useEffect(() => {
    const loadUser = async () => {
      if (!token) {
        setUser(null);
        setLoading(false);
        return;
      }
      
      try {
        setLoading(true);
        const me = await fetchMe();
        setUser(me);
      } catch (error) {
        console.error('Failed to fetch user:', error);
        localStorage.removeItem('token');
        setToken('');
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, [token]);

  const login = (newToken: string) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken('');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ token, user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  // During Vite HMR, the provider might unmount and context becomes null briefly
  return context || {
    token: '',
    user: null,
    loading: true,
    login: () => {},
    logout: () => {}
  };
};
