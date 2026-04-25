import { useState, useEffect } from 'react';

interface User {
  id: number;
  email: string;
  name: string;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = localStorage.getItem('medlens_token');
    const storedUser = localStorage.getItem('medlens_user');
    
    if (storedToken && storedUser) {
      setToken(storedToken);
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        console.error("Failed to parse stored user", e);
      }
    }
  }, []);

  const login = (newToken: string, newUser: User) => {
    localStorage.setItem('medlens_token', newToken);
    localStorage.setItem('medlens_user', JSON.stringify(newUser));
    setToken(newToken);
    setUser(newUser);
  };

  const logout = () => {
    localStorage.removeItem('medlens_token');
    localStorage.removeItem('medlens_user');
    setToken(null);
    setUser(null);
    window.location.href = '/login';
  };

  return {
    user,
    token,
    isLoggedIn: !!token,
    login,
    logout
  };
}
