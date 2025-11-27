
import { create } from 'zustand';
import { api } from '../services/api';
import { User, Drone, Task, AgentMessage, SystemLog, Notification } from '../types';

interface AppState {
  // Auth
  user: User | null;
  isAuthenticated: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
  
  // Drones
  drones: Drone[];
  selectedDroneId: number | null;
  isLoadingDrones: boolean;
  fetchDrones: () => Promise<void>;
  setSelectedDroneId: (id: number | null) => void;
  updateDrone: (id: number, updates: Partial<Drone>) => void;
  
  // Tasks
  tasks: Task[];
  fetchTasks: () => Promise<void>;
  updateTaskLocally: (task: Task) => void;
  addTaskLocally: (task: Task) => void;
  
  // Agent
  messages: AgentMessage[];
  addMessage: (msg: AgentMessage) => void;
  
  // Logs
  logs: SystemLog[];
  fetchLogs: () => Promise<void>;
  
  // Notifications
  notifications: Notification[];
  addNotification: (type: 'success' | 'error' | 'info' | 'warning', message: string) => void;
  removeNotification: (id: string) => void;

  // System UI
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useStore = create<AppState>((set, get) => ({
  // Auth
  user: null,
  isAuthenticated: false,
  login: (user, token) => {
    localStorage.setItem('access_token', token);
    set({ user, isAuthenticated: true });
    get().addNotification('success', `Welcome back, ${user.username}`);
  },
  logout: () => {
    api.logout();
    set({ user: null, isAuthenticated: false, drones: [], tasks: [], messages: [] });
  },

  // Drones
  drones: [],
  selectedDroneId: null,
  isLoadingDrones: false,
  fetchDrones: async () => {
    set({ isLoadingDrones: true });
    try {
      const data = await api.getDrones();
      set({ drones: Array.isArray(data) ? data : [] });
    } catch (error) {
      console.error(error);
      get().addNotification('error', 'Failed to update swarm telemetry');
    } finally {
      set({ isLoadingDrones: false });
    }
  },
  setSelectedDroneId: (id) => set({ selectedDroneId: id }),
  updateDrone: (id, updates) => set((state) => ({
    drones: state.drones.map(d => d.id === id ? { ...d, ...updates } : d)
  })),

  // Tasks
  tasks: [],
  fetchTasks: async () => {
    try {
      const data = await api.getTasks();
      if (Array.isArray(data)) {
        set({ tasks: data });
      } else {
        console.warn("fetchTasks received invalid data format:", data);
        set({ tasks: [] });
      }
    } catch (error) {
      console.error(error);
    }
  },
  updateTaskLocally: (updatedTask) => 
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === updatedTask.id ? updatedTask : t)),
    })),
  addTaskLocally: (newTask) =>
    set((state) => ({ tasks: [...state.tasks, newTask] })),

  // Agent
  messages: [{ role: 'system', content: 'Agent Link Established. Ready for swarm commands.', timestamp: new Date().toISOString() }],
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),

  // Logs
  logs: [],
  fetchLogs: async () => {
      try {
          const logs = await api.getSystemLogs();
          set({ logs: Array.isArray(logs) ? logs : [] });
      } catch (e) {
          console.error(e);
      }
  },

  // Notifications
  notifications: [],
  addNotification: (type, message) => {
      const id = Date.now().toString();
      set(state => ({ notifications: [...state.notifications, { id, type, message }] }));
      setTimeout(() => get().removeNotification(id), 5000);
  },
  removeNotification: (id) => set(state => ({ notifications: state.notifications.filter(n => n.id !== id) })),

  // System UI
  isSidebarOpen: true,
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
}));
