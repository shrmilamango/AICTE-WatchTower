import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api/client';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('watchtower_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const verifyUser = async () => {
      const token = localStorage.getItem('watchtower_token');
      if (token) {
        try {
          const userData = await api.get('/auth/me');
          setUser(userData);
          localStorage.setItem('watchtower_user', JSON.stringify(userData));
        } catch (err) {
          console.error('Session expired or invalid', err);
          logout();
        }
      }
      setLoading(false);
    };
    verifyUser();
  }, []);

  const login = async (email, password) => {
    const data = await api.post('/auth/login', { email, password });
    localStorage.setItem('watchtower_token', data.access_token);
    localStorage.setItem('watchtower_user', JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  };

  const logout = () => {
    localStorage.removeItem('watchtower_token');
    localStorage.removeItem('watchtower_user');
    setUser(null);
    api.post('/auth/logout').catch(() => {});
  };

  const hasRole = (roles) => {
    if (!user) return false;
    if (typeof roles === 'string') return user.role === roles;
    return roles.includes(user.role);
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      logout,
      hasRole,
      isAuthenticated: !!user,
      isInstitution: user?.role === 'INSTITUTION',
      isAdmin: user?.role === 'ADMIN',
      isOfficial: ['AUTHORISED_OFFICIAL', 'SCRUTINY_OFFICER', 'EVC_COORDINATOR', 'COMMITTEE_MEMBER'].includes(user?.role)
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
