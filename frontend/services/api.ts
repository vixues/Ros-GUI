
import { AuthResponse, Drone, DroneStatus, AgentMessage, Task, TaskStatus, TaskPriority, User, Waypoint, SystemLog } from '../types';

const API_URL = 'http://localhost:8000';
const USE_MOCK = true; // Toggle this to false when Backend is live

// Real-world center (Mojave Desert Test Site)
const HOME_BASE = {
    lat: 35.0542,
    lng: -118.1523
};

// --- MOCK DATA GENERATOR ---
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
        for(let w=0; w<3; w++) {
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

// --- MOCK STATE ---
const MOCK_USER: User = { id: 1, username: 'Commander', email: 'admin@skynet.com', is_active: true, role: 'ADMIN' };
let MOCK_DRONES: Drone[] = generateMockDrones(64); 
let MOCK_TASKS: Task[] = [
  { id: 101, title: 'Perimeter Scan Alpha', description: 'Routine surveillance of sector 7G. Maintain altitude 50m.', status: TaskStatus.IN_PROGRESS, priority: TaskPriority.MEDIUM, assigned_drone_ids: [1, 5, 12, 15], created_at: new Date().toISOString() },
  { id: 102, title: 'Emergency Response Test', description: 'Simulate rapid deployment for search and rescue scenario.', status: TaskStatus.PENDING, priority: TaskPriority.CRITICAL, assigned_drone_ids: [], created_at: new Date().toISOString() },
  { id: 103, title: 'Battery Calibration', description: 'Perform discharge cycles on Unit 4.', status: TaskStatus.COMPLETED, priority: TaskPriority.LOW, assigned_drone_ids: [4], created_at: new Date().toISOString() },
];
let MOCK_LOGS: SystemLog[] = [
    { id: 'log-1', timestamp: new Date(Date.now() - 10000).toISOString(), level: 'INFO', module: 'AUTH', message: 'User Commander logged in from 192.168.1.5' },
    { id: 'log-2', timestamp: new Date(Date.now() - 50000).toISOString(), level: 'WARNING', module: 'SWARM', message: 'Unit-005 intermittent signal loss detected' },
    { id: 'log-3', timestamp: new Date(Date.now() - 120000).toISOString(), level: 'SUCCESS', module: 'MISSION', message: 'Task 103 completed successfully' },
];

class ApiService {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem('access_token');
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('access_token', token);
  }

  logout() {
    this.token = null;
    localStorage.removeItem('access_token');
  }

  // Generic Request Wrapper
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(this.token ? { 'Authorization': `Bearer ${this.token}` } : {}),
      ...options.headers,
    };

    try {
      const res = await fetch(`${API_URL}${endpoint}`, { ...options, headers });
      if (res.status === 401) {
          // Handle unauthorized
          this.logout();
          window.location.hash = '/login';
          throw new Error('Unauthorized');
      }
      if (!res.ok) {
          const errorData = await res.json().catch(() => ({}));
          throw new Error(errorData.detail || `API Error: ${res.statusText}`);
      }
      return res.json();
    } catch (e: any) {
        if (!USE_MOCK) throw e;
        console.warn(`[MOCK FALLBACK] ${endpoint}`);
        return this.mockHandler<T>(endpoint, options);
    }
  }

  // --- Mock Handler Logic ---
  private mockHandler<T>(endpoint: string, options: RequestInit): Promise<T> {
      return new Promise((resolve, reject) => {
          setTimeout(() => {
              // AUTH
              if (endpoint.includes('/auth/token')) {
                  resolve({ access_token: "mock_jwt_token", token_type: "bearer", user: MOCK_USER } as any);
                  return;
              }
              if (endpoint.includes('/auth/me')) {
                  resolve(MOCK_USER as any);
                  return;
              }

              // DRONES
              if (endpoint === '/drones/') {
                  resolve(MOCK_DRONES as any);
                  return;
              }
              // Drone Actions
              if (endpoint.match(/\/drones\/\d+\/(connect|disconnect|land|reboot)/)) {
                  resolve({ status: "success" } as any);
                  return;
              }
              if (endpoint.match(/\/drones\/\d+\/waypoints/)) {
                 resolve({ success: true } as any);
                 return;
              }

              // TASKS
              if (endpoint === '/tasks/' && options.method === 'GET') {
                  resolve(MOCK_TASKS as any);
                  return;
              }
              if (endpoint === '/tasks/' && options.method === 'POST') {
                  const body = JSON.parse(options.body as string);
                  const newTask = { ...body, id: Date.now(), created_at: new Date().toISOString() };
                  MOCK_TASKS.push(newTask);
                  resolve(newTask as any);
                  return;
              }
              if (endpoint.match(/\/tasks\/\d+/) && options.method === 'PUT') {
                  const id = parseInt(endpoint.split('/')[2]);
                  const updates = JSON.parse(options.body as string);
                  MOCK_TASKS = MOCK_TASKS.map(t => t.id === id ? { ...t, ...updates } : t);
                  resolve(MOCK_TASKS.find(t => t.id === id) as any);
                  return;
              }

              // LOGS
              if (endpoint === '/logs/') {
                  resolve(MOCK_LOGS as any);
                  return;
              }

              // SWARM
              if (endpoint === '/swarm/broadcast') {
                  resolve({ success: true } as any);
                  return;
              }

              // AGENT
              if (endpoint === '/agent/chat') {
                  // Handled in specific method below for complex logic
              }

              reject(new Error("Mock endpoint not found"));
          }, 300); // Latency
      });
  }

  // --- Public Methods ---

  async login(username: string, password: string) {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      // We manually fetch here because of form-data/content-type specifics
      if (USE_MOCK) return this.mockHandler<AuthResponse>('/auth/token', {});
      const res = await fetch(`${API_URL}/auth/token`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: formData
      });
      if(!res.ok) throw new Error('Login failed');
      const data = await res.json();
      this.setToken(data.access_token);
      return data;
  }

  async getMe() { return this.request<User>('/auth/me'); }

  // Drones
  async getDrones() { return this.request<Drone[]>('/drones/'); }
  async connectDrone(id: number) { return this.request(`/drones/${id}/connect`, { method: 'POST' }); }
  async disconnectDrone(id: number) { return this.request(`/drones/${id}/disconnect`, { method: 'POST' }); }
  async landDrone(id: number) { return this.request(`/drones/${id}/land`, { method: 'POST' }); }
  async rebootDrone(id: number) { return this.request(`/drones/${id}/reboot`, { method: 'POST' }); }
  async updateWaypoints(id: number, waypoints: Waypoint[]) {
      return this.request(`/drones/${id}/waypoints`, { 
          method: 'PUT', 
          body: JSON.stringify(waypoints) 
      });
  }

  // Swarm
  async broadcastCommand(command: string, params: any = {}) {
      return this.request('/swarm/broadcast', {
          method: 'POST',
          body: JSON.stringify({ command, params })
      });
  }

  // Tasks
  async getTasks() { return this.request<Task[]>('/tasks/'); }
  async createTask(task: Partial<Task>) { return this.request<Task>('/tasks/', { method: 'POST', body: JSON.stringify(task) }); }
  async updateTask(id: number, updates: Partial<Task>) { return this.request<Task>(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(updates) }); }
  async deleteTask(id: number) { return this.request(`/tasks/${id}`, { method: 'DELETE' }); }

  // Logs
  async getSystemLogs() { return this.request<SystemLog[]>('/logs/'); }

  // Agent (Complex Mock with Enhanced NLU)
  async sendAgentMessage(sessionId: string, message: string): Promise<{ response: string, actions: any[], type?: string, data?: any }> {
    if (!USE_MOCK) {
        return this.request('/agent/chat', { method: 'POST', body: JSON.stringify({ session_id: sessionId, message }) });
    }

    // Mock Logic
    await new Promise(r => setTimeout(r, 1200));
    const msg = message.toLowerCase();

    // 1. Image/Scan Intent
    if (msg.includes('scan') || msg.includes('image') || msg.includes('photo')) {
        return {
            response: "Initiating optical sweep. Target identified at Sector 7.",
            actions: [{ action_type: 'CAPTURE_IMAGE', status: 'EXECUTED', timestamp: new Date().toISOString() }],
            type: 'image',
            data: {
                url: 'https://images.unsplash.com/photo-1506947411487-a56738267384?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
                objects: ['Vehicle', 'Person'],
                confidence: 0.89,
                location: '35.054, -118.152'
            }
        };
    }

    // 2. Specific Unit Control: Altitude
    // Matches: "Set unit 5 altitude to 40", "Unit 5 alt 40m", etc.
    const altMatch = msg.match(/(?:unit|drone)\s?(\d+).*(?:altitude|alt)\s?(?:to)?\s?(\d+)/i);
    if (altMatch) {
        const [_, id, alt] = altMatch;
        return {
            response: `Command confirmed. Adjusting Unit-${id.padStart(3,'0')} flight ceiling to ${alt} meters.`,
            actions: [{ 
                action_type: 'SET_ALTITUDE', 
                parameters: { drone_id: parseInt(id), altitude: parseInt(alt) },
                status: 'EXECUTED', 
                timestamp: new Date().toISOString() 
            }],
            type: 'text'
        };
    }

    // 3. Specific Unit Control: Speed
    const speedMatch = msg.match(/(?:unit|drone)\s?(\d+).*(?:speed|velocity)\s?(?:to)?\s?(\d+)/i);
    if (speedMatch) {
        const [_, id, speed] = speedMatch;
        return {
            response: `Speed adjustment acknowledged. Unit-${id.padStart(3,'0')} accelerating to ${speed} m/s.`,
            actions: [{ 
                action_type: 'SET_SPEED', 
                parameters: { drone_id: parseInt(id), speed: parseInt(speed) },
                status: 'EXECUTED', 
                timestamp: new Date().toISOString() 
            }],
            type: 'text'
        };
    }

    // 4. Return to Launch (RTL)
    const rtlMatch = msg.match(/(?:return|rtl|home).*(?:unit|drone)\s?(\d+)/i);
    if (rtlMatch) {
        const [_, id] = rtlMatch;
        return {
            response: `RTL protocol engaged for Unit-${id.padStart(3,'0')}. Returning to base immediately.`,
            actions: [{ 
                action_type: 'RTL', 
                parameters: { drone_id: parseInt(id) },
                status: 'EXECUTED', 
                timestamp: new Date().toISOString() 
            }],
            type: 'text'
        };
    }

    // 5. General Telemetry
    if (msg.includes('status') || msg.includes('telemetry') || msg.includes('report')) {
        return {
            response: "Telemetry uplink established. Swarm operational status is NOMINAL.",
            actions: [],
            type: 'drone_telemetry',
            data: MOCK_DRONES[0] // Just show first drone as example
        };
    }

    // 6. Mission Info
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

    // Default Fallback
    return {
        response: `[DEMO] Command processed: "${message}". I am listening for swarm directives. Try asking me to "Scan sector", "Set Unit 1 altitude to 50", or "Return Unit 5".`,
        actions: [],
        type: 'text'
    };
  }
}

export const api = new ApiService();
