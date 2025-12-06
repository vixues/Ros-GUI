/**
 * Unified API service exports
 */

export * from './httpClient';
export * from './authService';
export * from './droneService';
export * from './taskService';
export * from './agentService';
export * from './logService';
export * from './operationService';

// Import mock service for development
import { mockService } from './mockService';
import { config } from '../lib/config';

// Export the appropriate service based on feature flag
export const api = config.features.useMockData ? mockService : {
  // Real API will be used when feature flag is false
};

