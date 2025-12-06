import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { User, Drone, Task, AgentMessage, SystemLog, Notification } from '../types';
import { mockService } from '../services/mockService';
import { authService } from '../services/authService';
import { droneService } from '../services/droneService';
import { taskService } from '../services/taskService';
import { logService } from '../services/logService';
import { config } from '../lib/config';

const useMock = config.features.useMockData;

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
  lastDronesFetch: number | null;
  fetchDrones: (force?: boolean) => Promise<void>;
  setSelectedDroneId: (id: number | null) => void;
  updateDrone: (id: number, updates: Partial<Drone>) => void;
  
  // Tasks
  tasks: Task[];
  isLoadingTasks: boolean;
  lastTasksFetch: number | null;
  fetchTasks: (force?: boolean) => Promise<void>;
  updateTaskLocally: (task: Task) => void;
  addTaskLocally: (task: Task) => void;
  removeTaskLocally: (id: number) => void;
  
  // Agent
  messages: AgentMessage[];
  agentSessionId: number | null;
  addMessage: (msg: AgentMessage) => void;
  clearMessages: () => void;
  
  // Logs
  logs: SystemLog[];
  isLoadingLogs: boolean;
  fetchLogs: () => Promise<void>;
  addLog: (log: SystemLog) => void;
  
  // Notifications
  notifications: Notification[];
  addNotification: (type: 'success' | 'error' | 'info' | 'warning', message: string) => void;
  removeNotification: (id: string) => void;

  // System UI
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
  
  // System Stats
  systemStats: {
    totalDrones: number;
    activeDrones: number;
    onlineDrones: number;
    errorDrones: number;
    activeTasks: number;
  };
  updateSystemStats: () => void;
  
  // Cache control
  invalidateCache: () => void;
}

const CACHE_TTL = 30000; // 30 seconds cache

const isCacheValid = (lastFetch: number | null): boolean => {
  if (!lastFetch) return false;
  return Date.now() - lastFetch < CACHE_TTL;
};

export const useStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Auth
      user: null,
      isAuthenticated: false,
      login: (user, token) => {
        localStorage.setItem('access_token', token);
        set({ user, isAuthenticated: true });
        get().addNotification('success', `Welcome back, ${user.username}`);
      },
      logout: () => {
        if (useMock) {
          mockService.logout();
        } else {
          authService.logout();
        }
        set({ 
          user: null, 
          isAuthenticated: false, 
          drones: [], 
          tasks: [], 
          messages: [{ 
            role: 'system', 
            content: 'Agent Link Established. Ready for swarm commands.', 
            timestamp: new Date().toISOString() 
          }],
          logs: [],
          agentSessionId: null,
          lastDronesFetch: null,
          lastTasksFetch: null,
        });
      },

      // Drones
      drones: [],
      selectedDroneId: null,
      isLoadingDrones: false,
      lastDronesFetch: null,
      fetchDrones: async (force = false) => {
        // Cache check
        if (!force && isCacheValid(get().lastDronesFetch)) {
          return;
        }

        // Prevent concurrent fetches
        if (get().isLoadingDrones) return;

        set({ isLoadingDrones: true });
        try {
          const data = useMock 
            ? await mockService.getDrones()
            : await droneService.getDrones();
          set({ 
            drones: Array.isArray(data) ? data : [],
            lastDronesFetch: Date.now()
          });
          get().updateSystemStats();
        } catch (error: any) {
          console.error('Failed to fetch drones:', error);
          get().addNotification('error', 'Failed to update swarm telemetry');
        } finally {
          set({ isLoadingDrones: false });
        }
      },
      setSelectedDroneId: (id) => set({ selectedDroneId: id }),
      updateDrone: (id, updates) => {
        set((state) => ({
          drones: state.drones.map(d => d.id === id ? { ...d, ...updates } : d)
        }));
        get().updateSystemStats();
      },

      // Tasks
      tasks: [],
      isLoadingTasks: false,
      lastTasksFetch: null,
      fetchTasks: async (force = false) => {
        // Cache check
        if (!force && isCacheValid(get().lastTasksFetch)) {
          return;
        }

        // Prevent concurrent fetches
        if (get().isLoadingTasks) return;

        set({ isLoadingTasks: false });
        try {
          const data = useMock
            ? await mockService.getTasks()
            : await taskService.getTasks();
          set({ 
            tasks: Array.isArray(data) ? data : [],
            lastTasksFetch: Date.now()
          });
          get().updateSystemStats();
        } catch (error: any) {
          console.error('Failed to fetch tasks:', error);
          get().addNotification('error', 'Failed to load tasks');
        } finally {
          set({ isLoadingTasks: false });
        }
      },
      updateTaskLocally: (updatedTask) => {
        set((state) => ({
          tasks: state.tasks.map((t) => (t.id === updatedTask.id ? updatedTask : t)),
        }));
        get().updateSystemStats();
      },
      addTaskLocally: (newTask) => {
        set((state) => ({ tasks: [...state.tasks, newTask] }));
        get().updateSystemStats();
      },
      removeTaskLocally: (id) => {
        set((state) => ({ tasks: state.tasks.filter(t => t.id !== id) }));
        get().updateSystemStats();
      },

      // Agent
      messages: [
        { 
          role: 'system', 
          content: 'Agent Link Established. Ready for swarm commands.', 
          timestamp: new Date().toISOString() 
        }
      ],
      agentSessionId: null,
      addMessage: (msg) => set((state) => ({ 
        messages: [...state.messages, msg].slice(-100) // Keep last 100 messages
      })),
      clearMessages: () => set({ 
        messages: [
          { 
            role: 'system', 
            content: 'Agent Link Established. Ready for swarm commands.', 
            timestamp: new Date().toISOString() 
          }
        ] 
      }),

      // Logs
      logs: [],
      isLoadingLogs: false,
      fetchLogs: async () => {
        set({ isLoadingLogs: true });
        try {
          const logs = useMock
            ? await mockService.getSystemLogs()
            : await logService.getLogs();
          set({ logs: Array.isArray(logs) ? logs : [] });
        } catch (error: any) {
          console.error('Failed to fetch logs:', error);
        } finally {
          set({ isLoadingLogs: false });
        }
      },
      addLog: (log) => set((state) => ({ 
        logs: [log, ...state.logs].slice(0, 500) // Keep last 500 logs
      })),

      // Notifications
      notifications: [],
      addNotification: (type, message) => {
        const id = Date.now().toString();
        set(state => ({ 
          notifications: [...state.notifications, { id, type, message }] 
        }));
        setTimeout(() => get().removeNotification(id), config.ui.notificationDuration);
      },
      removeNotification: (id) => 
        set(state => ({ 
          notifications: state.notifications.filter(n => n.id !== id) 
        })),

      // System UI
      isSidebarOpen: true,
      toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
      
      // System Stats
      systemStats: {
        totalDrones: 0,
        activeDrones: 0,
        onlineDrones: 0,
        errorDrones: 0,
        activeTasks: 0,
      },
      updateSystemStats: () => {
        const { drones, tasks } = get();
        const stats = {
          totalDrones: drones.length,
          activeDrones: drones.filter(d => 
            d.status === 'FLYING' || d.status === 'ARMED'
          ).length,
          onlineDrones: drones.filter(d => 
            d.status !== 'OFFLINE' && d.status !== 'ERROR'
          ).length,
          errorDrones: drones.filter(d => d.status === 'ERROR').length,
          activeTasks: tasks.filter(t => 
            t.status === 'IN_PROGRESS' || t.status === 'PENDING'
          ).length,
        };
        set({ systemStats: stats });
      },

      // Cache control
      invalidateCache: () => {
        set({ lastDronesFetch: null, lastTasksFetch: null });
      },
    }),
    {
      name: 'app-store',
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        isSidebarOpen: state.isSidebarOpen,
        // Don't persist volatile data
      }),
    }
  )
);

// Cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    useStore.getState().invalidateCache();
  });

  // Listen for auth unauthorized event
  window.addEventListener('auth:unauthorized', () => {
    useStore.getState().logout();
  });
}
