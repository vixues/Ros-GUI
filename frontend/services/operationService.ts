/**
 * Operations API service
 */

import { httpClient } from './httpClient';

export interface Operation {
  id: number;
  operation_type: string;
  drone_id?: number;
  user_id: number;
  status: string;
  topic?: string;
  payload?: any;
  response?: any;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface OperationFilters {
  drone_id?: number;
  operation_type?: string;
  status?: string;
  start_date?: string;
  end_date?: string;
  skip?: number;
  limit?: number;
}

class OperationService {
  async getOperations(filters?: OperationFilters): Promise<Operation[]> {
    return httpClient.get<Operation[]>('/api/operations', filters);
  }

  async getOperation(id: number): Promise<Operation> {
    return httpClient.get<Operation>(`/api/operations/${id}`);
  }
}

export const operationService = new OperationService();

