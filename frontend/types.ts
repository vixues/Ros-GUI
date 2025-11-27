
// Matching backend Pydantic models

export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  role?: string;
}

export enum DroneStatus {
  IDLE = "IDLE",
  ARMED = "ARMED",
  FLYING = "FLYING",
  RETURNING = "RETURNING",
  LANDED = "LANDED",
  OFFLINE = "OFFLINE",
  ERROR = "ERROR"
}

export interface Waypoint {
  id: string;
  lat: number;
  lng: number;
  alt: number;
  type: 'FLY_THROUGH' | 'HOVER' | 'LAND' | 'ROI';
  speed?: number; // m/s
}

export interface Drone {
  id: number;
  serial_number: string;
  name?: string;
  model_type?: string;
  status: DroneStatus;
  battery_level: number;
  latitude?: number;
  longitude?: number;
  altitude?: number;
  heading?: number;
  last_seen?: string;
  waypoints?: Waypoint[];
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export type MessageType = 'text' | 'image' | 'drone_telemetry' | 'mission_status';

export interface AgentMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  type?: MessageType;
  data?: any;
  timestamp: string;
}

export interface AgentAction {
  id: number;
  action_type: string;
  parameters: Record<string, any>;
  status: 'PENDING' | 'EXECUTED' | 'FAILED';
  timestamp: string;
}

export interface SystemStats {
  total_drones: number;
  active_operations: number;
  system_health: number;
}

export enum TaskStatus {
  PENDING = "PENDING",
  IN_PROGRESS = "IN_PROGRESS",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED"
}

export enum TaskPriority {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  CRITICAL = "CRITICAL"
}

export interface Task {
  id: number;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  assigned_drone_ids: number[];
  created_at?: string;
  updated_at?: string;
}

export interface SystemLog {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL' | 'SUCCESS';
  module: string; // e.g., 'AUTH', 'SWARM', 'MISSION'
  message: string;
  metadata?: any;
}

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  duration?: number;
}
