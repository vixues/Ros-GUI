/**
 * System logs API service
 */

import { httpClient } from './httpClient';
import { SystemLog } from '../types';

export interface LogFilters {
  level?: string;
  module?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

class LogService {
  async getLogs(filters?: LogFilters): Promise<SystemLog[]> {
    return httpClient.get<SystemLog[]>('/api/logs', filters);
  }

  async getLog(id: string): Promise<SystemLog> {
    return httpClient.get<SystemLog>(`/api/logs/${id}`);
  }
}

export const logService = new LogService();

