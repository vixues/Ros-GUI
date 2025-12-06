
import React, { useEffect, useState } from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { AgentConsole } from './pages/AgentConsole';
import { TaskManagement } from './pages/TaskManagement';
import { FleetManagement } from './pages/FleetManagement';
import { OperationsLogs } from './pages/OperationsLogs';
import { ToastNotifications } from './components/ToastNotifications';
import { useStore } from './store/useStore';
import { mockService } from './services/mockService';
import { authService } from './services/authService';
import { config } from './lib/config';

const App: React.FC = () => {
  const { isAuthenticated, login, logout, user } = useStore();
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      try {
        // Check if we have a token
        const token = localStorage.getItem('access_token');
        if (token) {
          // Try to get user info with existing token
          const userData = config.features.useMockData
            ? await mockService.getMe()
            : await authService.getMe();
          login(userData, token);
        } else if (config.features.useMockData) {
          // Auto-login in mock mode
          const bypassUser = { 
            id: 1, 
            username: 'Commander', 
            email: 'admin@skynet.com', 
            is_active: true,
            role: 'ADMIN'
          };
          const mockToken = 'mock_token';
          login(bypassUser, mockToken);
        }
      } catch (error) {
        console.error('Auth initialization failed:', error);
        // Clear invalid token
        localStorage.removeItem('access_token');
      } finally {
        setIsInitializing(false);
      }
    };
    initAuth();
  }, [login]);

  if (isInitializing) {
    return (
      <div className="h-screen w-full bg-black flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <div className="text-blue-500 font-mono text-sm tracking-widest animate-pulse">INITIALIZING SKYNET...</div>
        </div>
      </div>
    );
  }

  return (
    <HashRouter>
      <ToastNotifications />
      <Routes>
        <Route 
          path="/login" 
          element={!isAuthenticated ? <Login /> : <Navigate to="/" />} 
        />
        
        <Route 
          path="/" 
          element={isAuthenticated ? (
            <Layout user={user} onLogout={logout}>
              <Dashboard />
            </Layout>
          ) : <Navigate to="/login" />} 
        />
        
        <Route 
          path="/agent" 
          element={isAuthenticated ? (
            <Layout user={user} onLogout={logout}>
              <AgentConsole />
            </Layout>
          ) : <Navigate to="/login" />} 
        />

        <Route 
          path="/tasks" 
          element={isAuthenticated ? (
            <Layout user={user} onLogout={logout}>
              <TaskManagement />
            </Layout>
          ) : <Navigate to="/login" />} 
        />

        <Route 
          path="/fleet" 
          element={isAuthenticated ? (
            <Layout user={user} onLogout={logout}>
              <FleetManagement />
            </Layout>
          ) : <Navigate to="/login" />} 
        />
         <Route 
          path="/operations" 
          element={isAuthenticated ? (
            <Layout user={user} onLogout={logout}>
               <OperationsLogs />
            </Layout>
          ) : <Navigate to="/login" />} 
        />

        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </HashRouter>
  );
};

export default App;
