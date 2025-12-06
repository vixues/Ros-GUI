/**
 * Agent/LLM API service
 */

import { httpClient } from './httpClient';
import { AgentMessage, AgentAction } from '../types';

export interface AgentSessionCreateData {
  title?: string;
  metadata?: Record<string, any>;
}

export interface AgentSessionResponse {
  id: number;
  user_id: number;
  title: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

export interface AgentMessageData {
  content: string;
  role?: 'user' | 'assistant' | 'system';
  type?: string;
  data?: any;
}

export interface AgentChatResponse {
  response: string;
  actions: AgentAction[];
  type?: string;
  data?: any;
}

class AgentService {
  async createSession(data?: AgentSessionCreateData): Promise<AgentSessionResponse> {
    return httpClient.post<AgentSessionResponse>('/api/agent/sessions', data || {});
  }

  async getSessions(activeOnly: boolean = true): Promise<AgentSessionResponse[]> {
    return httpClient.get<AgentSessionResponse[]>('/api/agent/sessions', { active_only: activeOnly });
  }

  async getSession(sessionId: number): Promise<AgentSessionResponse> {
    return httpClient.get<AgentSessionResponse>(`/api/agent/sessions/${sessionId}`);
  }

  async sendMessage(sessionId: number, message: AgentMessageData): Promise<AgentChatResponse> {
    return httpClient.post<AgentChatResponse>(`/api/agent/sessions/${sessionId}/message`, message);
  }

  async endSession(sessionId: number): Promise<AgentSessionResponse> {
    return httpClient.post<AgentSessionResponse>(`/api/agent/sessions/${sessionId}/end`);
  }
}

export const agentService = new AgentService();

