
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Cpu, 
  LayoutDashboard, 
  MessageSquareCode, 
  Plane, 
  Activity, 
  LogOut,
  Settings,
  ClipboardList,
  Target,
  Zap,
  Share2,
  ChevronRight,
  Bell
} from 'lucide-react';
import { cn } from '../lib/utils';
import { useStore } from '../store/useStore';
import { DroneStatus } from '../types';
import { AgentChatWidget } from './AgentChatWidget';

interface LayoutProps {
  children: React.ReactNode;
  user: any;
  onLogout: () => void;
}

// Compact Nav Icon
const NavIcon = ({ to, icon: Icon, label, active, alert }: any) => (
  <Link
    to={to}
    className={cn(
      "w-10 h-10 flex items-center justify-center rounded-lg transition-all duration-200 group relative",
      active 
        ? 'bg-primary text-white shadow-lg shadow-primary/20' 
        : 'text-zinc-500 hover:bg-zinc-800 hover:text-zinc-200'
    )}
    title={label}
  >
    <Icon className="w-5 h-5" />
    {alert && <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-red-500 border border-black animate-pulse"></span>}
    
    {/* Tooltip */}
    <div className="absolute left-14 bg-zinc-800 text-white text-[10px] font-bold px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap border border-zinc-700 z-50">
        {label}
    </div>
  </Link>
);

// Top Bar Stat Item
const StatusMetric = ({ label, value, icon: Icon, color }: any) => (
    <div className="flex items-center gap-3 px-4 border-r border-zinc-800/50 last:border-0 h-10">
        <div className={cn("p-1.5 rounded bg-opacity-10", color.replace('text-', 'bg-'))}>
            <Icon size={14} className={color} />
        </div>
        <div className="flex flex-col justify-center">
            <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-wider leading-none mb-0.5">{label}</span>
            <span className="text-xs font-bold text-white font-mono leading-none">{value}</span>
        </div>
    </div>
);

export const Layout: React.FC<LayoutProps> = ({ children, user, onLogout }) => {
  const location = useLocation();
  const { drones } = useStore();

  // Derived Stats for Header
  const onlineCount = drones.filter(d => d.status !== DroneStatus.OFFLINE).length;
  const avgBattery = drones.length > 0 ? Math.round(drones.reduce((acc, d) => acc + d.battery_level, 0) / drones.length) : 0;
  const healthIndex = drones.length > 0 ? Math.round((onlineCount / drones.length) * 100) : 100;
  const activePhase = "LOITER"; // Static for now

  return (
    <div className="flex h-screen w-full bg-black overflow-hidden text-zinc-200 font-sans selection:bg-primary/30">
      
      {/* 1. Left Sidebar Container (Nav Rail + Agent Panel) */}
      <aside className="flex h-full border-r border-zinc-800 bg-black flex-shrink-0">
        
        {/* A. Navigation Rail (Slim) */}
        <div className="w-16 flex flex-col items-center py-4 gap-2 border-r border-zinc-800 bg-zinc-950 z-20">
            <div className="mb-4">
                <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-lg shadow-white/5">
                    <Cpu className="w-6 h-6 text-black" />
                </div>
            </div>

            <NavIcon to="/" icon={LayoutDashboard} label="Dashboard" active={location.pathname === '/'} />
            <NavIcon to="/fleet" icon={Plane} label="Fleet Control" active={location.pathname === '/fleet'} />
            <NavIcon to="/tasks" icon={ClipboardList} label="Task Manager" active={location.pathname === '/tasks'} />
            <NavIcon to="/operations" icon={Activity} label="System Logs" active={location.pathname === '/operations'} />
            
            <div className="mt-auto flex flex-col gap-2">
                 <button onClick={onLogout} className="w-10 h-10 flex items-center justify-center text-zinc-500 hover:text-red-400 hover:bg-zinc-800 rounded-lg transition-colors">
                    <LogOut size={18} />
                 </button>
                 <div className="w-10 h-10 flex items-center justify-center rounded-lg bg-zinc-900 border border-zinc-800 text-xs font-bold text-zinc-400">
                    {user?.username.slice(0, 2).toUpperCase()}
                 </div>
            </div>
        </div>

        {/* B. Agent Console Panel (Persistent) */}
        <div className="w-[320px] bg-zinc-950 flex flex-col border-r border-zinc-800 relative z-10 transition-all duration-300">
            <AgentChatWidget />
        </div>
      </aside>

      {/* 2. Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-background">
        
        {/* Top Status Bar (Redesigned Header) */}
        <header className="h-14 bg-zinc-950 border-b border-zinc-800 flex items-center justify-between px-4 shrink-0 shadow-md z-30">
            {/* System Status Indicator */}
            <div className="flex items-center gap-4 pr-6 border-r border-zinc-800 h-full">
                <div className="flex flex-col">
                    <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-wider">System Status</span>
                    <div className="flex items-center gap-2">
                        <span className="relative flex h-2.5 w-2.5">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                        </span>
                        <span className="text-sm font-bold text-white tracking-tight">OPERATIONAL</span>
                    </div>
                </div>
            </div>

            {/* KPI Metrics Row (Moved from Dashboard) */}
            <div className="flex items-center mr-auto pl-2">
                <StatusMetric label="Swarm Nodes" value={`${onlineCount}/${drones.length}`} icon={Share2} color="text-blue-500" />
                <StatusMetric label="Power Reserves" value={`${avgBattery}%`} icon={Zap} color="text-amber-500" />
                <StatusMetric label="Mission Phase" value={activePhase} icon={Target} color="text-purple-500" />
                <StatusMetric label="Health Index" value={`${healthIndex}%`} icon={Activity} color="text-emerald-500" />
            </div>

            {/* Right Controls */}
            <div className="flex items-center gap-3">
                 <div className="flex items-center gap-2 px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded text-xs font-mono text-zinc-400">
                    <Target size={12} />
                    <span>SECTOR_7G</span>
                 </div>
                 <button className="p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-full transition-colors relative">
                    <Bell size={16} />
                    <span className="absolute top-2 right-2 w-1.5 h-1.5 bg-red-500 rounded-full border border-black"></span>
                 </button>
            </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto bg-[#0c0c0e] p-6 relative">
             {children}
        </main>
      </div>
    </div>
  );
};
