/**
 * Enhanced HTTP Client with Request Interceptors and Retry Logic
 */

import { config } from '../lib/config';
import { retryWithBackoff } from '../lib/utils';

export interface ApiError {
  status: number;
  message: string;
  detail?: any;
  error_code?: string;
}

export interface ResponseWrapper<T = any> {
  status: number;
  message: string;
  data: T;
  error_code?: string;
  detail?: any;
}

type RequestInterceptor = (config: RequestInit) => RequestInit | Promise<RequestInit>;
type ResponseInterceptor = <T>(response: T) => T | Promise<T>;

class HttpClient {
  private baseURL: string;
  private token: string | null = null;
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];
  private abortControllers: Map<string, AbortController> = new Map();

  constructor(baseURL: string) {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('access_token');
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('access_token', token);
    } else {
      localStorage.removeItem('access_token');
    }
  }

  getToken(): string | null {
    return this.token;
  }

  // Interceptor management
  addRequestInterceptor(interceptor: RequestInterceptor) {
    this.requestInterceptors.push(interceptor);
  }

  addResponseInterceptor(interceptor: ResponseInterceptor) {
    this.responseInterceptors.push(interceptor);
  }

  // Cancel pending requests
  cancelRequest(key: string) {
    const controller = this.abortControllers.get(key);
    if (controller) {
      controller.abort();
      this.abortControllers.delete(key);
    }
  }

  cancelAllRequests() {
    this.abortControllers.forEach(controller => controller.abort());
    this.abortControllers.clear();
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryConfig?: { maxRetries?: number; baseDelay?: number }
  ): Promise<T> {
    const requestKey = `${options.method || 'GET'}_${endpoint}`;
    
    // Create abort controller for this request
    const controller = new AbortController();
    this.abortControllers.set(requestKey, controller);

    const makeRequest = async (): Promise<T> => {
      const url = `${this.baseURL}${endpoint}`;
      let requestOptions: RequestInit = {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
          ...options.headers,
        },
      };

      // Apply request interceptors
      for (const interceptor of this.requestInterceptors) {
        requestOptions = await interceptor(requestOptions);
      }

      try {
        const response = await fetch(url, requestOptions);

        // Handle 401 Unauthorized - Token expired
        if (response.status === 401) {
          this.setToken(null);
          // Emit custom event for auth failure
          window.dispatchEvent(new CustomEvent('auth:unauthorized'));
          window.location.hash = '/login';
          throw this.createError(401, 'Session expired. Please login again.');
        }

        // Handle 403 Forbidden
        if (response.status === 403) {
          throw this.createError(403, 'Access forbidden. Insufficient permissions.');
        }

        // Handle other HTTP errors
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw this.createError(
            response.status,
            errorData.message || errorData.detail || response.statusText,
            errorData.detail,
            errorData.error_code
          );
        }

        // Parse response
        let data = await response.json();
        
        // Handle wrapped responses
        if (data && typeof data === 'object' && 'data' in data) {
          data = data.data;
        }

        // Apply response interceptors
        for (const interceptor of this.responseInterceptors) {
          data = await interceptor(data);
        }

        return data as T;
      } catch (error: any) {
        // Handle abort
        if (error.name === 'AbortError') {
          throw this.createError(0, 'Request cancelled');
        }

        if (error.status) {
          throw error; // Already an ApiError
        }

        // Network or other errors
        throw this.createError(0, error.message || 'Network error');
      } finally {
        this.abortControllers.delete(requestKey);
      }
    };

    // Apply retry logic for certain requests
    if (retryConfig?.maxRetries) {
      return retryWithBackoff(
        makeRequest,
        retryConfig.maxRetries,
        retryConfig.baseDelay || config.api.retryDelay
      );
    }

    return makeRequest();
  }

  private createError(
    status: number,
    message: string,
    detail?: any,
    error_code?: string
  ): ApiError {
    return { status, message, detail, error_code };
  }

  async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const queryString = params
      ? '?' + new URLSearchParams(params).toString()
      : '';
    return this.request<T>(
      endpoint + queryString, 
      { method: 'GET' },
      { maxRetries: config.api.retryAttempts }
    );
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  async postFormData<T>(endpoint: string, formData: FormData): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const headers: HeadersInit = {
      ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
    };

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw this.createError(
        response.status,
        errorData.message || response.statusText
      );
    }

    const data = await response.json();
    return data && typeof data === 'object' && 'data' in data
      ? data.data
      : data;
  }
}

export const httpClient = new HttpClient(config.api.baseURL);

// Add default interceptors
httpClient.addRequestInterceptor((config) => {
  // Add request timestamp for debugging
  const headers = new Headers(config.headers);
  headers.set('X-Request-Time', new Date().toISOString());
  return { ...config, headers };
});
