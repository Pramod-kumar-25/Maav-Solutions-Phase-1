import React, { createContext, useContext, useState, useEffect } from 'react';
import { loginAPI, request } from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(false);

  const login = async (username, password) => {
    const data = await loginAPI(username, password);
    setToken(data.access_token);
    localStorage.setItem('token', data.access_token);
  };

  const register = async (userData) => {
    await request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  };

  const logout = () => {
    setToken(null);
    localStorage.removeItem('token');
  };

  return (
    <AuthContext.Provider value={{ token, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
