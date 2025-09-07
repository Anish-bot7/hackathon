import React, { createContext, useState, useContext, useEffect } from 'react';
import api from './api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [userType, setUserType] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    const savedUserType = localStorage.getItem('userType');
    
    if (savedUser && savedUserType) {
      setUser(JSON.parse(savedUser));
      setUserType(savedUserType);
    }
    setLoading(false);
  }, []);

  const login = async (credentials, type) => {
    try {
      const endpoint = type === 'retailer' ? '/auth/retailer/login' : '/auth/warehouse/login';
      const response = await api.post(endpoint, credentials);
      const userData = response.data;
      
      setUser(userData);
      setUserType(type);
      localStorage.setItem('user', JSON.stringify(userData));
      localStorage.setItem('userType', type);
      
      return { success: true, data: userData };
    } catch (error) {
      return { success: false, message: error.response?.data?.detail || 'Login failed' };
    }
  };

  const register = async (userData, type) => {
    try {
      const endpoint = type === 'retailer' ? '/auth/retailer/register' : '/auth/warehouse/register';
      const response = await api.post(endpoint, userData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, message: error.response?.data?.detail || 'Registration failed' };
    }
  };

  const logout = () => {
    setUser(null);
    setUserType(null);
    localStorage.removeItem('user');
    localStorage.removeItem('userType');
  };

  return (
    <AuthContext.Provider value={{ user, userType, loading, login, register, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
};