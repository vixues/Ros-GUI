
import React, { useEffect, useState, useMemo } from 'react';
import { SwarmVisualizer } from '../components/SwarmVisualizer';
import { MapView } from '../components/MapView';
import { ClusterDiagnostics } from '../components/ClusterDiagnostics';
import { SwarmControlPanel } from '../components/SwarmControlPanel';
import { WaypointEditor } from '../components/WaypointEditor';
import { useStore } from '../store/useStore';
import { DroneStatus, Drone } from '../types';
import { Activity, Box, Map as MapIcon, Search } from 'lucide-react';
import { cn } from '../lib/utils';

// Compact Row for High Density Lists
const CompactDroneRow = ({ drone, isSelected, onClick }: { drone: Drone, isSelected: boolean, onClick: () => void }) => {
    const statusColors = {
        [DroneStatus.FLYING]: 'text-blue-500',
        [DroneStatus.IDLE]: 'text-amber-500',
        [DroneStatus.ERROR]: 'text-red-500',
        [DroneStatus.OFFLINE]: 'text-zinc-600',
        [DroneStatus.RETURNING]: 'text-purple-500',
        [DroneStatus.LANDED]: 'text-emerald-500',
        [DroneStatus.ARMED]: 'text-white'
    };

    return (
        <div 
            onClick={onClick}
            className={cn(
                "flex items-center gap-3 p-2.5 border-b border-zinc-800/50 cursor-pointer transition-colors hover:bg-white/5 last:border-0 text-xs group",
                isSelected ? "bg-white/10" : "bg-transparent"
            )}
        >
            <div className={cn("w-2 h-2 rounded-full", statusColors[drone.status].replace('text-', 'bg-'))}></div>
            <div className="flex-1 font-mono font-bold text-zinc-300 truncate group-hover:text-white transition-colors">
                {drone.name}
            </div>
            <div className="w-12 text-right font-mono text-zinc-500 group-hover:text-zinc-300">
                {drone.battery_level}%
            </div>
            <div className="w-8 text-right font-bold text-zinc-600 group-hover:text-zinc-400">
                {drone.id}
            </div>
        </div>
    );
};

export const Dashboard: React.FC = () => {
  const { drones, fetchDrones, isLoadingDrones, selectedDroneId, setSelectedDroneId } = useStore();
  const [viewMode, setViewMode] = useState<'3d' | '2d'>('3d');
  const [searchTerm, setSearchTerm] = useState('');
  const [isSwarmPanelOpen, setIsSwarmPanelOpen] = useState(false);
  
  // Waypoint Editor State
  const [waypointEditorDroneId, setWaypointEditorDroneId] = useState<number | null>(null);

  useEffect(() => {
    fetchDrones();
    const interval = setInterval(fetchDrones, 2000); 
    return () => clearInterval(interval);
  }, [fetchDrones]);

  const filteredDrones = useMemo(() => {
      if(!searchTerm) return drones;
      return drones.filter(d => d.name?.toLowerCase().includes(searchTerm.toLowerCase()) || d.serial_number.toLowerCase().includes(searchTerm.toLowerCase()));
  }, [drones, searchTerm]);

  const handleOpenWaypointEditor = (droneId: number) => {
      setWaypointEditorDroneId(droneId);
  };

  const editingDrone = useMemo(() => drones.find(d => d.id === waypointEditorDroneId), [drones, waypointEditorDroneId]);

  return (
    <div className="h-full flex flex-col gap-6">
      {/* Main Content Split - Full Height now that Header Stats are moved */}
      <div className="flex-1 flex gap-6 min-h-0 overflow-hidden">
        
        {/* Left: Main Viewport (2D/3D) */}
        <div className="flex-1 flex flex-col gap-4 min-w-0 bg-surface rounded-xl border border-zinc-800/50 p-1 relative shadow-xl overflow-hidden">
            {/* View Toggle */}
            <div className="absolute top-4 right-4 z-[401] flex bg-surface_highlight p-1 rounded-lg border border-zinc-800 shadow-lg">
               <button 
                  onClick={() => setViewMode('3d')}
                  className={cn(
                    "flex items-center gap-2 px-3 py-1.5 text-xs font-bold rounded-md transition-all",
                    viewMode === '3d' ? 'bg-white text-black shadow-sm' : 'text-zinc-500 hover:text-white'
                  )}
               >
                  <Box size={14} />
                  3D
               </button>
               <button 
                  onClick={() => setViewMode('2d')}
                  className={cn(
                    "flex items-center gap-2 px-3 py-1.5 text-xs font-bold rounded-md transition-all",
                    viewMode === '2d' ? 'bg-white text-black shadow-sm' : 'text-zinc-500 hover:text-white'
                  )}
               >
                  <MapIcon size={14} />
                  MAP
               </button>
            </div>

            {/* Overlay Info */}
            <div className="absolute top-4 left-4 z-[401] pointer-events-none flex flex-col gap-1">
              <h2 className="text-sm font-bold text-white tracking-wide uppercase bg-black/80 px-2 py-1 rounded backdrop-blur-sm w-fit border border-white/10 shadow-lg">
                 {viewMode === '3d' ? 'Isometric Projection' : 'Tactical Map'}
              </h2>
              <div className="flex items-center gap-2 px-2 py-1 bg-black/80 rounded backdrop-blur-sm w-fit border border-white/10 shadow-lg">
                 <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                 </span>
                 <span className="text-[10px] font-mono text-zinc-300">LIVE FEED</span>
              </div>
            </div>

            <div className="flex-1 rounded-lg overflow-hidden relative bg-black">
              {viewMode === '3d' ? (
                <SwarmVisualizer 
                  drones={drones} 
                  selectedDroneId={selectedDroneId}
                  onSelectDrone={setSelectedDroneId}
                />
              ) : (
                <MapView 
                  drones={drones}
                  selectedDroneId={selectedDroneId}
                  onSelectDrone={setSelectedDroneId}
                  onOpenWaypointEditor={handleOpenWaypointEditor}
                />
              )}
            </div>
        </div>

        {/* Right: Status Panel (Optimized for 50-100 items) */}
        <div className="w-80 flex flex-col gap-4">
          <ClusterDiagnostics 
            drones={drones} 
            onClick={() => setIsSwarmPanelOpen(true)}
          />

          <div className="flex-1 flex flex-col bg-surface rounded-xl border border-zinc-800/50 min-h-0 shadow-lg">
            <div className="p-3 border-b border-zinc-800/50 bg-zinc-900/50">
               <div className="flex items-center justify-between mb-2">
                   <h3 className="font-bold text-sm text-white uppercase tracking-wider">Active Units</h3>
                   <span className="text-[10px] font-mono text-zinc-500">{filteredDrones.length} ONLINE</span>
               </div>
               
               <div className="relative">
                 <Search className="absolute left-2.5 top-2 text-zinc-600 w-3.5 h-3.5" />
                 <input 
                    className="w-full bg-black/30 border border-zinc-800 rounded px-8 py-1.5 text-xs text-white focus:border-white/20 focus:outline-none placeholder:text-zinc-600 font-medium transition-colors focus:bg-black/50" 
                    placeholder="Search ID..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                 />
               </div>
            </div>
            
            {/* Headers */}
            <div className="flex px-3 py-1.5 bg-black/40 text-[9px] font-bold text-zinc-500 uppercase tracking-wider border-b border-zinc-800/50">
               <span className="w-2"></span>
               <span className="flex-1 ml-3">Unit Name</span>
               <span className="w-12 text-right">Bat</span>
               <span className="w-8 text-right">ID</span>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar bg-black/20">
              {isLoadingDrones && drones.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-40 text-zinc-500 gap-3">
                   <Activity className="animate-spin text-primary w-6 h-6" />
                   <span className="text-xs font-semibold">Establishing Uplink...</span>
                </div>
              ) : (
                filteredDrones.map(drone => (
                  <CompactDroneRow 
                    key={drone.id} 
                    drone={drone} 
                    isSelected={drone.id === selectedDroneId}
                    onClick={() => setSelectedDroneId(drone.id)}
                  />
                ))
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Modals */}
      {isSwarmPanelOpen && (
          <SwarmControlPanel onClose={() => setIsSwarmPanelOpen(false)} />
      )}
      
      {editingDrone && (
          <WaypointEditor 
            drone={editingDrone} 
            onClose={() => setWaypointEditorDroneId(null)} 
          />
      )}
    </div>
  );
};
