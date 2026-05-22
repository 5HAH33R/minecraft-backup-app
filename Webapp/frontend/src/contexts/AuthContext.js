import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('authToken');
    if (token) {
      try {
        const response = await api.get('/api/auth/me');
        setUser(response.data);
      } catch (error) {
        localStorage.removeItem('authToken');
      }
    }
    setLoading(false);
  };

  const login = async () => {
    const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    const response = await fetch(`${API_URL}/api/auth/google/login`);
    const data = await response.json();
    window.location.href = data.auth_url;
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    setUser(null);
    window.location.href = '/';
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};