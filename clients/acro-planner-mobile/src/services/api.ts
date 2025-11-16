import axios, { AxiosInstance, AxiosError } from 'axios';
import { storage } from '../utils/storage';
import { ENV } from '../config/env';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: ENV.API_BASE_URL,
      timeout: ENV.API_TIMEOUT,
      withCredentials: true, // Enable cookie support
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    this.api.interceptors.request.use(
      async (config) => {
        // Authentication is handled via HTTP-only cookies automatically
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    this.api.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        // 401 errors will be handled by the cookie expiration automatically
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
      const response = await this.api.post('/auth/login/password', { email, password });
      // Authentication is handled via HTTP-only cookies, no manual token storage needed
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async register(userData: {
    email: string;
    password: string;
    password_confirm: string;
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
    // Call logout endpoint to clear HTTP-only cookies
    try {
      await this.api.get('/auth/logout');
    } catch (error) {
      // Ignore logout errors, user is being logged out anyway
    }
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