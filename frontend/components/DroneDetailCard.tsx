
import React from 'react';
import { Drone, DroneStatus, Task } from '../types';
import { useStore } from '../store/useStore';
import { 
  Battery, 
  Wifi, 
  Navigation, 
  Target, 
  Video, 
  PlayCircle,
  Power,
  ArrowDownCircle,
  AlertTriangle,
  CheckCircle2,
  Clock,
  MapPin,
  Edit
} from 'lucide-react';
import { cn } from '../lib/utils';
import { api } from '../services/api';

interface DroneDetailCardProps {
  drone: Drone;
  onOpenWaypointEditor?: (droneId: number) => void;
}

export const DroneDetailCard: React.FC<DroneDetailCardProps> = ({ drone, onOpenWaypointEditor }) => {
  const { tasks } = useStore();
  
  // Filter tasks for this drone
  const activeTasks = tasks.filter(t => t.assigned_drone_ids.includes(drone.id));
  
  const handleAction = async (action: 'land' | 'rtl') => {
      // Implementation placeholder
      console.log(`Command ${action} sent to Drone ${drone.id}`);
      if (action === 'land') await api.landDrone(drone.id);
  };

  const statusColor = {
      [DroneStatus.FLYING]: 'text-blue-400',
      [DroneStatus.IDLE]: 'text-amber-400',
      [DroneStatus.ERROR]: 'text-red-400',
      [DroneStatus.OFFLINE]: 'text-zinc-600',
      [DroneStatus.RETURNING]: 'text-purple-400',
      [DroneStatus.LANDED]: 'text-emerald-400',
      [DroneStatus.ARMED]: 'text-white'
  }[drone.status];

  return (
    <div className="w-[300px] bg-black/90 backdrop-blur-md border border-zinc-700 rounded-lg overflow-hidden flex flex-col shadow-2xl font-sans">
      {/* Header */}
      <div className="px-3 py-2 bg-zinc-900 border-b border-zinc-800 flex justify-between items-center">
        <div className="flex items-center gap-2">
            <div className={cn("w-2 h-2 rounded-full animate-pulse", statusColor.replace('text-', 'bg-'))}></div>
            <span className="font-bold text-white text-xs tracking-wider">{drone.name?.toUpperCase()}</span>
        </div>
        <span className="text-[10px] font-mono text-zinc-500">SN: {drone.serial_number}</span>
      </div>

      {/* Video Feed Placeholder */}
      <div className="relative h-40 bg-zinc-950 flex items-center justify-center border-b border-zinc-800 group">
          {/* Scanlines effect */}
          <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-10 bg-[length:100%_2px,3px_100%] pointer-events-none"></div>
          
          <Video className="text-zinc-700 mb-2" size={32} />
          <span className="absolute bottom-2 right-2 text-[9px] font-mono text-red-500 flex items-center gap-1 bg-black/50 px-1 rounded">
            <div className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse"></div>
            LIVE
          </span>
          <div className="absolute top-2 left-2 text-[9px] font-mono text-zinc-400 bg-black/50 px-1 rounded border border-zinc-800">
             CAM_01
          </div>
          
          {/* HUD Overlay */}
          <div className="absolute inset-4 border border-zinc-800/30 rounded-sm border-dashed"></div>
      </div>

      {/* Telemetry Grid */}
      <div className="grid grid-cols-3 gap-px bg-zinc-800 border-b border-zinc-800">
          <div className="bg-black/80 p-2 flex flex-col items-center justify-center">
              <span className="text-[9px] text-zinc-500 uppercase font-bold">Battery</span>
              <div className="flex items-center gap-1 text-white font-mono text-xs">
                  <Battery size={10} className={drone.battery_level < 20 ? "text-red-500" : "text-emerald-500"} />
                  {drone.battery_level}%
              </div>
          </div>
          <div className="bg-black/80 p-2 flex flex-col items-center justify-center">
              <span className="text-[9px] text-zinc-500 uppercase font-bold">Altitude</span>
              <div className="flex items-center gap-1 text-white font-mono text-xs">
                  <ArrowDownCircle size={10} className="text-blue-500 rotate-180" />
                  {drone.altitude?.toFixed(0)}m
              </div>
          </div>
           <div className="bg-black/80 p-2 flex flex-col items-center justify-center">
              <span className="text-[9px] text-zinc-500 uppercase font-bold">Heading</span>
              <div className="flex items-center gap-1 text-white font-mono text-xs">
                  <Navigation size={10} className="text-amber-500" style={{ transform: `rotate(${drone.heading || 0}deg)`}} />
                  {drone.heading || 0}°
              </div>
          </div>
      </div>

      {/* Waypoint/Mission Control Row */}
      <div className="p-2 border-b border-zinc-800 bg-zinc-900/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
              <MapPin size={12} className="text-blue-400" />
              <div className="flex flex-col">
                  <span className="text-[9px] font-bold text-zinc-400 uppercase">Flight Path</span>
                  <span className="text-[9px] font-mono text-white leading-none">
                      {drone.waypoints?.length || 0} Waypoints Set
                  </span>
              </div>
          </div>
          <button 
            onClick={() => onOpenWaypointEditor && onOpenWaypointEditor(drone.id)}
            className="flex items-center gap-1 px-2 py-1 bg-zinc-800 hover:bg-zinc-700 text-white rounded border border-zinc-700 text-[9px] font-bold transition-colors"
          >
              <Edit size={10} /> EDIT PATH
          </button>
      </div>

      {/* Task List */}
      <div className="p-3 bg-zinc-900/50 flex-1">
          <div className="flex items-center gap-1.5 mb-2">
              <Target size={12} className="text-zinc-400" />
              <span className="text-[10px] font-bold text-zinc-400 uppercase">Active Directives</span>
          </div>
          
          <div className="space-y-2 max-h-[80px] overflow-y-auto custom-scrollbar">
              {activeTasks.length > 0 ? (
                  activeTasks.map(task => (
                      <div key={task.id} className="flex items-start gap-2 bg-black/40 p-1.5 rounded border border-zinc-800">
                          {task.status === 'IN_PROGRESS' ? <PlayCircle size={10} className="text-blue-400 mt-0.5" /> : <Clock size={10} className="text-zinc-500 mt-0.5" />}
                          <div>
                              <div className="text-[10px] font-bold text-zinc-200 leading-none">{task.title}</div>
                              <div className="text-[9px] text-zinc-500 leading-none mt-1">{task.status}</div>
                          </div>
                      </div>
                  ))
              ) : (
                  <div className="text-[10px] text-zinc-600 italic py-2 text-center border border-dashed border-zinc-800 rounded">
                      No active tasks assigned
                  </div>
              )}
          </div>
      </div>

      {/* Footer Actions */}
      <div className="p-2 bg-zinc-950 border-t border-zinc-800 grid grid-cols-2 gap-2">
          <button 
            onClick={() => handleAction('rtl')}
            className="flex items-center justify-center gap-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-[10px] font-bold py-1.5 rounded transition-colors"
          >
              <Target size={12} />
              RTL
          </button>
          <button 
             onClick={() => handleAction('land')}
             className="flex items-center justify-center gap-1.5 bg-red-900/20 hover:bg-red-900/40 text-red-500 border border-red-900/30 text-[10px] font-bold py-1.5 rounded transition-colors"
          >
              <ArrowDownCircle size={12} />
              LAND
          </button>
      </div>
    </div>
  );
};
