/**
 * Application configuration with comprehensive settings
 */

export const config = {
  // API Configuration
  api: {
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    timeout: 30000,
    retryAttempts: 3,
    retryDelay: 1000,
  },
  
  // Feature Flags
  features: {
    useMockData: import.meta.env.VITE_USE_MOCK === 'true' || true,
    enableLLM: import.meta.env.VITE_ENABLE_LLM === 'true' || false,
    enableRealtime: import.meta.env.VITE_ENABLE_REALTIME === 'true' || false,
  },
  
  // UI Configuration
  ui: {
    notificationDuration: 5000,
    autoRefreshInterval: 10000,
    mapDefaultCenter: {
      lat: 35.0542,
      lng: -118.1523,
    },
  },
  
  // App Metadata
  app: {
    name: 'SKYNET Swarm Command',
    version: '2.0.0',
  },
} as const;

export type AppConfig = typeof config;
