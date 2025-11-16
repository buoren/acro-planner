import axios, { AxiosInstance, AxiosError } from 'axios';
import * as SecureStore from 'expo-secure-store';
import { ENV } from '../config/env';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: ENV.API_BASE_URL,
      timeout: ENV.API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    this.api.interceptors.request.use(
      async (config) => {
        const token = await SecureStore.getItemAsync('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    this.api.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          await SecureStore.deleteItemAsync('authToken');
        }
        return Promise.reject(error);
      }
    );
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.api.get('/health');
      return response.data.status === 'healthy';
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }

  async login(email: string, password: string): Promise<any> {
    try {
      const response = await this.api.post('/users/login', { email, password });
      if (response.data.token) {
        await SecureStore.setItemAsync('authToken', response.data.token);
      }
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async register(userData: {
    email: string;
    password: string;
    name: string;
    role?: string;
  }): Promise<any> {
    try {
      const response = await this.api.post('/users/register', userData);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async logout(): Promise<void> {
    await SecureStore.deleteItemAsync('authToken');
  }

  async getCurrentUser(): Promise<any> {
    try {
      const response = await this.api.get('/auth/me');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getConventions(): Promise<any> {
    try {
      const response = await this.api.get('/conventions');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getWorkshops(conventionId?: string): Promise<any> {
    try {
      const params = conventionId ? { convention_id: conventionId } : {};
      const response = await this.api.get('/workshops', { params });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getEventSlots(conventionId?: string): Promise<any> {
    try {
      const params = conventionId ? { convention_id: conventionId } : {};
      const response = await this.api.get('/event_slots', { params });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  private handleError(error: any): Error {
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      return new Error(message);
    }
    return error;
  }
}

export default new ApiService();