
import React from 'react';
import { Drone, DroneStatus } from '../types';
import { Activity, Share2, Wifi, Zap, Server, ExternalLink } from 'lucide-react';
import { cn } from '../lib/utils';

const MetricBar = ({ label, value, icon: Icon, color }: any) => (
  <div className="flex flex-col gap-1">
    <div className="flex justify-between items-end">
      <div className="flex items-center gap-1.5 text-zinc-400 text-[10px] font-bold uppercase tracking-wide">
        <Icon size={12} />
        {label}
      </div>
      <span className="text-white font-bold text-xs font-mono">{value}%</span>
    </div>
    <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
      <div className={cn("h-full rounded-full transition-all duration-500", color)} style={{ width: `${value}%` }} />
    </div>
  </div>
);

export const ClusterDiagnostics: React.FC<{ drones: Drone[], onClick?: () => void }> = ({ drones, onClick }) => {
  const onlineCount = drones.filter(d => d.status !== DroneStatus.OFFLINE).length;
  const integrity = drones.length > 0 ? Math.round((onlineCount / drones.length) * 100) : 0;
  const cohesion = drones.length > 1 ? 85 : 100;
  
  return (
    <div 
        onClick={onClick}
        className="bg-surface rounded-xl border border-zinc-800/50 p-5 flex flex-col gap-5 shadow-lg group hover:border-zinc-700 cursor-pointer transition-all relative"
    >
      <div className="absolute top-4 right-4 text-zinc-600 group-hover:text-primary transition-colors">
          <ExternalLink size={14} />
      </div>

      <div className="flex justify-between items-center pr-6">
         <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Share2 className="text-primary w-4 h-4" />
            Swarm Health
         </h3>
         <div className="flex items-center gap-2">
           <div className={cn("w-2 h-2 rounded-full", integrity > 80 ? "bg-success" : "bg-danger")}></div>
           <span className="text-xs font-bold text-zinc-400">{integrity}% Integrity</span>
         </div>
      </div>

      <div className="space-y-4">
         <MetricBar label="Mesh Cohesion" value={cohesion} icon={Activity} color="bg-primary" />
         <MetricBar label="Signal Strength" value={92} icon={Wifi} color="bg-success" />
         <MetricBar label="Processing Load" value={34} icon={Server} color="bg-warning" />
      </div>

      <div className="bg-surface_highlight rounded-lg p-3 flex justify-between items-center mt-auto group-hover:bg-zinc-800 transition-colors">
         <div className="flex flex-col">
            <span className="text-[10px] text-zinc-500 font-bold uppercase">Total Power Draw</span>
            <span className="text-sm font-bold text-white font-mono flex items-center gap-1">
              <Zap size={12} className="fill-current text-warning" /> 
              {(drones.length * 0.4).toFixed(1)} kW
            </span>
         </div>
         <div className="text-right">
             <span className="text-[10px] text-zinc-500 font-bold uppercase">Active Nodes</span>
             <p className="text-sm font-bold text-white font-mono">{onlineCount} <span className="text-zinc-600">/</span> {drones.length}</p>
         </div>
      </div>
    </div>
  );
};
