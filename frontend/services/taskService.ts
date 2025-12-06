/**
 * Task API service
 */

import { httpClient } from './httpClient';
import { Task, TaskStatus, TaskPriority } from '../types';

export interface TaskCreateData {
  title: string;
  description: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  assigned_drone_ids?: number[];
}

export interface TaskUpdateData {
  title?: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  assigned_drone_ids?: number[];
}

class TaskService {
  async getTasks(): Promise<Task[]> {
    return httpClient.get<Task[]>('/api/tasks');
  }

  async getTask(id: number): Promise<Task> {
    return httpClient.get<Task>(`/api/tasks/${id}`);
  }

  async createTask(data: TaskCreateData): Promise<Task> {
    return httpClient.post<Task>('/api/tasks', data);
  }

  async updateTask(id: number, data: TaskUpdateData): Promise<Task> {
    return httpClient.put<Task>(`/api/tasks/${id}`, data);
  }

  async deleteTask(id: number): Promise<void> {
    return httpClient.delete(`/api/tasks/${id}`);
  }
}

export const taskService = new TaskService();

