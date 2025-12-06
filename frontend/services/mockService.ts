/**
 * Mock API service for development
 */

import { 
  Drone, 
  DroneStatus, 
  Task, 
  TaskStatus, 
  TaskPriority, 
  SystemLog, 
  User,
  Waypoint,
  AgentMessage,
} from '../types';
import { authService } from './authService';
import { droneService } from './droneService';
import { taskService } from './taskService';
import { agentService } from './agentService';
import { logService } from './logService';
import { operationService } from './operationService';
import { config } from '../lib/config';

// Mock data
const HOME_BASE = config.ui.mapDefaultCenter;

const generateMockDrones = (count: number): Drone[] => {
  const drones: Drone[] = [];
  const models = ['Scout MK-I', 'Scout MK-II', 'Heavy Lift X8', 'Interceptor'];
  
  for (let i = 1; i <= count; i++) {
    let status = DroneStatus.IDLE;
    const rand = Math.random();
    if (rand > 0.9) status = DroneStatus.ERROR;
    else if (rand > 0.8) status = DroneStatus.OFFLINE;
    else if (rand > 0.6) status = DroneStatus.RETURNING;
    else if (rand > 0.3) status = DroneStatus.FLYING;

    const latOffset = (Math.random() - 0.5) * 0.025;
    const lngOffset = (Math.random() - 0.5) * 0.030;
    
    const altitude = status === DroneStatus.FLYING || status === DroneStatus.RETURNING 
      ? 20 + Math.random() * 100 
      : 0;
    
    const waypoints: Waypoint[] = [];
    if (status === DroneStatus.FLYING) {
      for (let w = 0; w < 3; w++) {
        waypoints.push({
          id: `wp-${i}-${w}`,
          lat: HOME_BASE.lat + latOffset + (Math.random() - 0.5) * 0.01,
          lng: HOME_BASE.lng + lngOffset + (Math.random() - 0.5) * 0.01,
          alt: 50,
          type: 'FLY_THROUGH',
          speed: 15
        });
      }
    }

    drones.push({
      id: i,
      serial_number: `SN-${1000 + i}`,
      name: `Unit-${i.toString().padStart(3, '0')}`,
      model_type: models[Math.floor(Math.random() * models.length)],
      status: status,
      battery_level: Math.floor(Math.random() * 100),
      altitude: altitude,
      latitude: HOME_BASE.lat + latOffset,
      longitude: HOME_BASE.lng + lngOffset,
      heading: Math.floor(Math.random() * 360),
      last_seen: new Date().toISOString(),
      waypoints: waypoints
    });
  }
  return drones;
};

let MOCK_DRONES: Drone[] = generateMockDrones(64);
let MOCK_TASKS: Task[] = [
  {
    id: 101,
    title: 'Perimeter Scan Alpha',
    description: 'Routine surveillance of sector 7G. Maintain altitude 50m.',
    status: TaskStatus.IN_PROGRESS,
    priority: TaskPriority.MEDIUM,
    assigned_drone_ids: [1, 5, 12, 15],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 102,
    title: 'Emergency Response Test',
    description: 'Simulate rapid deployment for search and rescue scenario.',
    status: TaskStatus.PENDING,
    priority: TaskPriority.CRITICAL,
    assigned_drone_ids: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 103,
    title: 'Battery Calibration',
    description: 'Perform discharge cycles on Unit 4.',
    status: TaskStatus.COMPLETED,
    priority: TaskPriority.LOW,
    assigned_drone_ids: [4],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
];

let MOCK_LOGS: SystemLog[] = [
  {
    id: 'log-1',
    timestamp: new Date(Date.now() - 10000).toISOString(),
    level: 'INFO',
    module: 'AUTH',
    message: 'User Commander logged in from 192.168.1.5'
  },
  {
    id: 'log-2',
    timestamp: new Date(Date.now() - 50000).toISOString(),
    level: 'WARNING',
    module: 'SWARM',
    message: 'Unit-005 intermittent signal loss detected'
  },
  {
    id: 'log-3',
    timestamp: new Date(Date.now() - 120000).toISOString(),
    level: 'SUCCESS',
    module: 'MISSION',
    message: 'Task 103 completed successfully'
  },
];

const MOCK_USER: User = {
  id: 1,
  username: 'Commander',
  email: 'admin@skynet.com',
  is_active: true,
  role: 'ADMIN'
};

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Mock service that wraps real services with mock data
 */
class MockService {
  // Auth
  async login(username: string, password: string) {
    await sleep(500);
    return {
      access_token: 'mock_jwt_token',
      token_type: 'bearer' as const,
      user: MOCK_USER
    };
  }

  async getMe() {
    await sleep(200);
    return MOCK_USER;
  }

  logout() {
    authService.logout();
  }

  // Drones
  async getDrones() {
    await sleep(300);
    return MOCK_DRONES;
  }

  async getDrone(id: number) {
    await sleep(200);
    const drone = MOCK_DRONES.find(d => d.id === id);
    if (!drone) throw new Error('Drone not found');
    return drone;
  }

  async connectDrone(id: number) {
    await sleep(500);
    return { status: 'connected' };
  }

  async disconnectDrone(id: number) {
    await sleep(300);
    return { status: 'disconnected' };
  }

  async landDrone(id: number) {
    await sleep(400);
    return { status: 'landing' };
  }

  async rebootDrone(id: number) {
    await sleep(600);
    return { status: 'rebooting' };
  }

  async updateWaypoints(id: number, waypoints: Waypoint[]) {
    await sleep(300);
    const droneIndex = MOCK_DRONES.findIndex(d => d.id === id);
    if (droneIndex !== -1) {
      MOCK_DRONES[droneIndex].waypoints = waypoints;
    }
    return { success: true };
  }

  // Tasks
  async getTasks() {
    await sleep(300);
    return MOCK_TASKS;
  }

  async createTask(task: Partial<Task>) {
    await sleep(400);
    const newTask: Task = {
      id: Date.now(),
      title: task.title || '',
      description: task.description || '',
      status: task.status || TaskStatus.PENDING,
      priority: task.priority || TaskPriority.MEDIUM,
      assigned_drone_ids: task.assigned_drone_ids || [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    MOCK_TASKS.push(newTask);
    return newTask;
  }

  async updateTask(id: number, updates: Partial<Task>) {
    await sleep(300);
    const index = MOCK_TASKS.findIndex(t => t.id === id);
    if (index !== -1) {
      MOCK_TASKS[index] = { ...MOCK_TASKS[index], ...updates, updated_at: new Date().toISOString() };
      return MOCK_TASKS[index];
    }
    throw new Error('Task not found');
  }

  async deleteTask(id: number) {
    await sleep(300);
    MOCK_TASKS = MOCK_TASKS.filter(t => t.id !== id);
  }

  // Logs
  async getSystemLogs() {
    await sleep(300);
    return MOCK_LOGS;
  }

  // Agent
  async sendAgentMessage(sessionId: string, message: string) {
    await sleep(1200);
    const msg = message.toLowerCase();

    // Image/Scan Intent
    if (msg.includes('scan') || msg.includes('image') || msg.includes('photo')) {
      return {
        response: "Initiating optical sweep. Target identified at Sector 7.",
        actions: [{
          id: Date.now(),
          action_type: 'CAPTURE_IMAGE',
          parameters: {},
          status: 'EXECUTED' as const,
          timestamp: new Date().toISOString()
        }],
        type: 'image',
        data: {
          url: 'https://images.unsplash.com/photo-1506947411487-a56738267384?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
          objects: ['Vehicle', 'Person'],
          confidence: 0.89,
          location: '35.054, -118.152'
        }
      };
    }

    // Altitude control
    const altMatch = msg.match(/(?:unit|drone)\s?(\d+).*(?:altitude|alt)\s?(?:to)?\s?(\d+)/i);
    if (altMatch) {
      const [_, id, alt] = altMatch;
      return {
        response: `Command confirmed. Adjusting Unit-${id.padStart(3, '0')} flight ceiling to ${alt} meters.`,
        actions: [{
          id: Date.now(),
          action_type: 'SET_ALTITUDE',
          parameters: { drone_id: parseInt(id), altitude: parseInt(alt) },
          status: 'EXECUTED' as const,
          timestamp: new Date().toISOString()
        }],
        type: 'text'
      };
    }

    // Speed control
    const speedMatch = msg.match(/(?:unit|drone)\s?(\d+).*(?:speed|velocity)\s?(?:to)?\s?(\d+)/i);
    if (speedMatch) {
      const [_, id, speed] = speedMatch;
      return {
        response: `Speed adjustment acknowledged. Unit-${id.padStart(3, '0')} accelerating to ${speed} m/s.`,
        actions: [{
          id: Date.now(),
          action_type: 'SET_SPEED',
          parameters: { drone_id: parseInt(id), speed: parseInt(speed) },
          status: 'EXECUTED' as const,
          timestamp: new Date().toISOString()
        }],
        type: 'text'
      };
    }

    // RTL
    const rtlMatch = msg.match(/(?:return|rtl|home).*(?:unit|drone)\s?(\d+)/i);
    if (rtlMatch) {
      const [_, id] = rtlMatch;
      return {
        response: `RTL protocol engaged for Unit-${id.padStart(3, '0')}. Returning to base immediately.`,
        actions: [{
          id: Date.now(),
          action_type: 'RTL',
          parameters: { drone_id: parseInt(id) },
          status: 'EXECUTED' as const,
          timestamp: new Date().toISOString()
        }],
        type: 'text'
      };
    }

    // Telemetry
    if (msg.includes('status') || msg.includes('telemetry') || msg.includes('report')) {
      return {
        response: "Telemetry uplink established. Swarm operational status is NOMINAL.",
        actions: [],
        type: 'drone_telemetry',
        data: MOCK_DRONES[0]
      };
    }

    // Mission
    if (msg.includes('mission') || msg.includes('plan')) {
      return {
        response: "Retrieving active mission profile...",
        actions: [],
        type: 'mission_status',
        data: {
          title: 'Operation Beta',
          status: 'IN PROGRESS',
          progress: 65,
          steps: ['Deploy', 'Scan', 'RTL']
        }
      };
    }

    // Default
    return {
      response: `[DEMO] Command processed: "${message}". I am listening for swarm directives. Try asking me to "Scan sector", "Set Unit 1 altitude to 50", or "Return Unit 5".`,
      actions: [],
      type: 'text'
    };
  }
}

export const mockService = new MockService();

