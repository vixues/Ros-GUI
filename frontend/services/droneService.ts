/**
 * Drone API service
 */

import { httpClient } from './httpClient';
import { Drone, Waypoint } from '../types';

export interface DroneFilters {
  skip?: number;
  limit?: number;
  status?: string;
}

export interface DroneCreateData {
  name: string;
  drone_id: string;
  device_id?: number;
  connection_url?: string;
  use_mock?: boolean;
  mock_config?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface DroneUpdateData {
  name?: string;
  device_id?: number;
  connection_url?: string;
  use_mock?: boolean;
  status?: string;
  metadata?: Record<string, any>;
}

export interface ConnectionRequest {
  connection_url: string;
  use_mock?: boolean;
  mock_config?: Record<string, any>;
}

class DroneService {
  async getDrones(filters?: DroneFilters): Promise<Drone[]> {
    return httpClient.get<Drone[]>('/api/drones', filters);
  }

  async getDrone(id: number): Promise<Drone> {
    return httpClient.get<Drone>(`/api/drones/${id}`);
  }

  async createDrone(data: DroneCreateData): Promise<Drone> {
    return httpClient.post<Drone>('/api/drones', data);
  }

  async updateDrone(id: number, data: DroneUpdateData): Promise<Drone> {
    return httpClient.put<Drone>(`/api/drones/${id}`, data);
  }

  async deleteDrone(id: number): Promise<void> {
    return httpClient.delete(`/api/drones/${id}`);
  }

  async connectDrone(id: number, connection: ConnectionRequest): Promise<{ status: string }> {
    return httpClient.post(`/api/drones/${id}/connect`, connection);
  }

  async disconnectDrone(id: number): Promise<{ status: string }> {
    return httpClient.post(`/api/drones/${id}/disconnect`);
  }

  async getDroneStatus(id: number): Promise<any> {
    return httpClient.get(`/api/drones/${id}/status`);
  }

  async updateWaypoints(id: number, waypoints: Waypoint[]): Promise<{ success: boolean }> {
    return httpClient.put(`/api/drones/${id}/waypoints`, waypoints);
  }

  async landDrone(id: number): Promise<{ status: string }> {
    return httpClient.post(`/api/drones/${id}/land`);
  }

  async rebootDrone(id: number): Promise<{ status: string }> {
    return httpClient.post(`/api/drones/${id}/reboot`);
  }

  async publishMessage(
    id: number,
    topic: string,
    topic_type: string,
    message: any
  ): Promise<{ topic: string; operation_id: number }> {
    return httpClient.post(`/api/drones/${id}/publish`, {
      topic,
      topic_type,
      message,
    });
  }
}

export const droneService = new DroneService();

