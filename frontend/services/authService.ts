/**
 * Authentication API service
 */

import { httpClient } from './httpClient';
import { AuthResponse, User } from '../types';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

class AuthService {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    // OAuth2 requires form data
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await fetch(`${httpClient['baseURL']}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || error.detail || 'Login failed');
    }

    const data = await response.json();
    const authData = data.data || data;
    
    // Set token in http client
    httpClient.setToken(authData.access_token);
    
    return {
      access_token: authData.access_token,
      token_type: authData.token_type || 'bearer',
      user: authData.user,
    };
  }

  async register(data: RegisterData): Promise<User> {
    return httpClient.post<User>('/api/auth/register', data);
  }

  async getMe(): Promise<User> {
    return httpClient.get<User>('/api/auth/me');
  }

  logout() {
    httpClient.setToken(null);
  }
}

export const authService = new AuthService();

