import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import { storage } from '../utils/storage';
import ApiService from '../services/api';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      // Check if user is authenticated via cookies
      const response = await ApiService.getCurrentUser();
      if (response && response.user) {
        setUser(response.user);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      // User is not authenticated, stay logged out
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    try {
      const response = await ApiService.login(email, password);
      // After successful login, get current user data
      const userData = await ApiService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      throw error;
    }
  };

  const register = async (email: string, password: string, name: string) => {
    try {
      const userData = await ApiService.register({ 
        email, 
        password, 
        password_confirm: password, 
        name 
      });
      // Registration successful, now login to get authentication token
      await ApiService.login(email, password);
      // Set user data from registration response
      setUser(userData);
    } catch (error) {
      throw error;
    }
  };

  const logout = async () => {
    await ApiService.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};