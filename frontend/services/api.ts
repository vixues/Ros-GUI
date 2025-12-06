/**
 * Unified API entry point
 * 统一的API入口，自动根据配置选择Mock或真实服务
 */

import { config } from '../lib/config';
import { mockService } from './mockService';
import { authService } from './authService';
import { droneService } from './droneService';
import { taskService } from './taskService';
import { agentService } from './agentService';
import { logService } from './logService';
import { operationService } from './operationService';

// 根据配置决定使用Mock还是真实API
const useMock = config.features.useMockData;

/**
 * 统一的API对象
 * 根据配置自动路由到Mock或真实服务
 */
export const api = {
  // ==================== Auth API ====================
  async login(username: string, password: string) {
    if (useMock) {
      return mockService.login(username, password);
    }
    return authService.login({ username, password });
  },

  async getMe() {
    if (useMock) {
      return mockService.getMe();
    }
    return authService.getMe();
  },

  logout() {
    if (useMock) {
      mockService.logout();
    } else {
      authService.logout();
    }
  },

  // ==================== Drone API ====================
  async getDrones() {
    if (useMock) {
      return mockService.getDrones();
    }
    return droneService.getDrones();
  },

  async getDrone(id: number) {
    if (useMock) {
      return mockService.getDrone(id);
    }
    return droneService.getDrone(id);
  },

  async connectDrone(id: number, connection?: any) {
    if (useMock) {
      return mockService.connectDrone(id);
    }
    return droneService.connectDrone(id, connection || {
      connection_url: 'ws://localhost:9090',
      use_mock: false
    });
  },

  async disconnectDrone(id: number) {
    if (useMock) {
      return mockService.disconnectDrone(id);
    }
    return droneService.disconnectDrone(id);
  },

  async landDrone(id: number) {
    if (useMock) {
      return mockService.landDrone(id);
    }
    return droneService.landDrone(id);
  },

  async rebootDrone(id: number) {
    if (useMock) {
      return mockService.rebootDrone(id);
    }
    return droneService.rebootDrone(id);
  },

  async updateWaypoints(id: number, waypoints: any[]) {
    if (useMock) {
      return mockService.updateWaypoints(id, waypoints);
    }
    return droneService.updateWaypoints(id, waypoints);
  },

  // ==================== Task API ====================
  async getTasks() {
    if (useMock) {
      return mockService.getTasks();
    }
    return taskService.getTasks();
  },

  async createTask(task: any) {
    if (useMock) {
      return mockService.createTask(task);
    }
    return taskService.createTask(task);
  },

  async updateTask(id: number, updates: any) {
    if (useMock) {
      return mockService.updateTask(id, updates);
    }
    return taskService.updateTask(id, updates);
  },

  async deleteTask(id: number) {
    if (useMock) {
      return mockService.deleteTask(id);
    }
    return taskService.deleteTask(id);
  },

  // ==================== System Logs API ====================
  async getSystemLogs(filters?: any) {
    if (useMock) {
      return mockService.getSystemLogs();
    }
    return logService.getLogs(filters);
  },

  // ==================== Agent API ====================
  async sendAgentMessage(sessionId: string, message: string) {
    if (useMock) {
      return mockService.sendAgentMessage(sessionId, message);
    }
    // 真实API需要先创建session，这里简化处理
    try {
      const sessionIdNum = parseInt(sessionId);
      return agentService.sendMessage(sessionIdNum, {
        content: message,
        role: 'user'
      });
    } catch (error) {
      console.error('Agent message error:', error);
      throw error;
    }
  },

  // ==================== Swarm Control API ====================
  async broadcastCommand(command: string, params: any = {}) {
    if (useMock) {
      // Mock实现
      await new Promise(resolve => setTimeout(resolve, 300));
      return { success: true };
    }
    // 真实实现（待后端实现）
    return { success: true };
  },
};

// 导出所有服务供高级用法使用
export {
  authService,
  droneService,
  taskService,
  agentService,
  logService,
  operationService,
  mockService,
};

// 导出配置
export { config };

