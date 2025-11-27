
import React, { useState, useEffect, useRef } from 'react';
import { Drone, DroneStatus } from '../types';
import { api } from '../services/api';
import { 
  Battery, 
  Wifi, 
  ArrowUp, 
  MapPin,
  Power,
  ArrowDown,
  RefreshCw,
  Loader2
} from 'lucide-react';
import { cn } from '../lib/utils';

interface DroneStatusCardProps {
  drone: Drone;
  isSelected?: boolean;
  onClick?: () => void;
}

export const DroneStatusCard: React.FC<DroneStatusCardProps> = ({ drone, isSelected, onClick }) => {
  const [activeAction, setActiveAction] = useState<string | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isSelected && cardRef.current) {
      cardRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [isSelected]);

  // Status Theme Configuration
  const getStatusTheme = (status: DroneStatus) => {
    switch (status) {
      case DroneStatus.FLYING: return { bg: 'bg-primary', text: 'text-primary', label: 'In Flight' };
      case DroneStatus.IDLE: return { bg: 'bg-warning', text: 'text-warning', label: 'Idle' };
      case DroneStatus.RETURNING: return { bg: 'bg-purple-500', text: 'text-purple-500', label: 'Returning' };
      case DroneStatus.LANDED: return { bg: 'bg-success', text: 'text-success', label: 'Landed' };
      case DroneStatus.ERROR: return { bg: 'bg-danger', text: 'text-danger', label: 'Error' };
      case DroneStatus.OFFLINE: return { bg: 'bg-zinc-500', text: 'text-zinc-500', label: 'Offline' };
      default: return { bg: 'bg-zinc-500', text: 'text-zinc-500', label: status };
    }
  };

  const theme = getStatusTheme(drone.status);
  const isOnline = drone.status !== DroneStatus.OFFLINE;

  // Actions
  const handleConnectToggle = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (activeAction) return;
    const action = isOnline ? 'disconnect' : 'connect';
    setActiveAction(action);
    try { 
      if (isOnline) await api.disconnectDrone(drone.id);
      else await api.connectDrone(drone.id);
    } catch (err) { console.error(err); }
    setActiveAction(null);
  };

  const handleLand = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (activeAction || !isOnline) return;
    setActiveAction('land');
    try { await api.landDrone(drone.id); } catch(err) { console.error(err); }
    setActiveAction(null);
  };

  const handleReboot = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (activeAction) return;
    setActiveAction('reboot');
    try { await api.rebootDrone(drone.id); } catch(err) { console.error(err); }
    setActiveAction(null);
  };

  return (
    <div 
      ref={cardRef}
      onClick={onClick}
      className={cn(
        "group relative rounded-lg overflow-hidden transition-all duration-200 cursor-pointer border-l-4",
        isSelected 
          ? 'bg-zinc-800 shadow-md ring-1 ring-white/10' 
          : 'bg-zinc-900/50 hover:bg-zinc-800 border-transparent',
        theme.bg.replace('bg-', 'border-')
      )}
    >
      <div className="p-3 flex flex-col gap-3">
        {/* Header: ID & Status */}
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-2 mb-0.5">
               <h4 className="text-sm font-bold text-white tracking-tight">
                  {drone.name || `UNIT ${drone.id}`}
               </h4>
               <span className="text-[10px] font-mono text-zinc-500">#{drone.serial_number?.slice(-4)}</span>
            </div>
            <p className="text-[10px] text-zinc-400 font-medium">{drone.model_type || 'Generic Quad'}</p>
          </div>
          <div className={cn("px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-white/5", theme.text)}>
            {theme.label}
          </div>
        </div>

        {/* Core Metrics: Battery & Alt */}
        <div className="grid grid-cols-2 gap-2">
           {/* Battery Block */}
           <div className="bg-black/20 rounded p-2 flex flex-col gap-1">
              <div className="flex justify-between items-center text-[10px] text-zinc-400 font-medium">
                 <span>PWR</span>
                 <Battery size={10} />
              </div>
              <div className="flex items-baseline gap-1">
                 <span className={cn("text-lg font-bold font-mono leading-none", drone.battery_level < 20 ? "text-danger" : "text-white")}>
                   {drone.battery_level}%
                 </span>
              </div>
              <div className="w-full bg-zinc-800 h-1 rounded-full overflow-hidden">
                 <div 
                   className={cn("h-full rounded-full", drone.battery_level < 20 ? "bg-danger" : "bg-white")} 
                   style={{width: `${drone.battery_level}%`}}
                 />
              </div>
           </div>

           {/* Signal/Alt Block */}
           <div className="bg-black/20 rounded p-2 flex flex-col gap-1">
               <div className="flex justify-between items-center text-[10px] text-zinc-400 font-medium">
                 <span>ALT</span>
                 <ArrowUp size={10} />
              </div>
              <div className="flex items-baseline gap-1">
                 <span className="text-lg font-bold font-mono text-white leading-none">
                    {drone.altitude?.toFixed(0) || '0'}
                 </span>
                 <span className="text-[10px] text-zinc-500 font-bold">m</span>
              </div>
               <div className="flex items-center gap-1 mt-auto">
                 <Wifi size={10} className="text-success" />
                 <span className="text-[9px] font-bold text-zinc-500">GOOD</span>
               </div>
           </div>
        </div>
      </div>
      
      {/* Action Drawer - Appears on Hover/Selected */}
      <div className={cn(
        "bg-zinc-950/50 border-t border-white/5 px-2 py-2 flex items-center justify-between gap-2 transition-all duration-300",
        isSelected || activeAction ? "h-auto opacity-100" : "h-0 opacity-0 overflow-hidden p-0 border-0"
      )}>
         <button 
           onClick={handleConnectToggle}
           className={cn(
             "flex-1 py-1.5 rounded text-[10px] font-bold uppercase flex items-center justify-center gap-1.5 transition-colors",
             isOnline ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700 hover:text-white" : "bg-primary text-white hover:bg-blue-600"
           )}
         >
            {activeAction?.includes('connect') ? <Loader2 size={10} className="animate-spin" /> : <Power size={10} />}
            {isOnline ? 'Disconnect' : 'Connect'}
         </button>
         
         {isOnline && (
           <>
            <button onClick={handleLand} className="flex-1 py-1.5 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 hover:text-white rounded text-[10px] font-bold uppercase flex items-center justify-center gap-1.5">
                {activeAction === 'land' ? <Loader2 size={10} className="animate-spin" /> : <ArrowDown size={10} />}
                Land
            </button>
            <button onClick={handleReboot} className="p-1.5 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 hover:text-white rounded">
               {activeAction === 'reboot' ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
            </button>
           </>
         )}
      </div>
    </div>
  );
};
