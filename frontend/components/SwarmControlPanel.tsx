
import React, { useState } from 'react';
import { X, Hexagon, Triangle, Grid, ArrowDownCircle, Home, Zap, ShieldAlert, Activity } from 'lucide-react';
import { cn } from '../lib/utils';
import { useStore } from '../store/useStore';
import { api } from '../services/api';

interface SwarmControlPanelProps {
  onClose: () => void;
}

export const SwarmControlPanel: React.FC<SwarmControlPanelProps> = ({ onClose }) => {
  const { drones, addNotification } = useStore();
  const [activeTab, setActiveTab] = useState<'formation' | 'broadcast' | 'config'>('formation');
  const [processingAction, setProcessingAction] = useState<string | null>(null);

  const handleBroadcast = async (action: string) => {
      setProcessingAction(action);
      try {
          await api.broadcastCommand(action);
          addNotification('success', `Command "${action}" broadcasted to ${drones.length} nodes`);
      } catch (error: any) {
          addNotification('error', `Broadcast failed: ${error.message}`);
      } finally {
          setProcessingAction(null);
      }
  };

  return (
    <div className="fixed inset-0 z-[500] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
        <div className="bg-zinc-950 border border-zinc-800 w-full max-w-2xl rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            {/* Header */}
            <div className="p-4 border-b border-zinc-800 flex justify-between items-center bg-zinc-900/50">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/20 rounded-lg">
                        <Hexagon className="text-primary w-5 h-5" />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-white tracking-wide">SWARM COMMAND CENTER</h2>
                        <div className="flex items-center gap-2 text-xs font-mono text-zinc-400">
                            <span>NODES: {drones.length}</span>
                            <span className="text-zinc-600">|</span>
                            <span>SYNC: 100%</span>
                        </div>
                    </div>
                </div>
                <button onClick={onClose} className="p-2 hover:bg-zinc-800 rounded-lg text-zinc-500 hover:text-white transition-colors">
                    <X size={20} />
                </button>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-zinc-800">
                {['formation', 'broadcast', 'config'].map(tab => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab as any)}
                        className={cn(
                            "flex-1 py-3 text-xs font-bold uppercase tracking-wider transition-colors border-b-2",
                            activeTab === tab 
                            ? "border-primary text-white bg-white/5" 
                            : "border-transparent text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                        )}
                    >
                        {tab}
                    </button>
                ))}
            </div>

            {/* Content */}
            <div className="p-6 flex-1 overflow-y-auto">
                {activeTab === 'formation' && (
                    <div className="grid grid-cols-2 gap-4">
                        {[
                            { id: 'delta', name: 'Delta Wedge', icon: Triangle, desc: 'Aerodynamic efficiency for transit.' },
                            { id: 'grid', name: 'Search Grid', icon: Grid, desc: 'Maximum coverage for scanning.' },
                            { id: 'orbit', name: 'Circular Orbit', icon: Activity, desc: 'Perimeter surveillance mode.' },
                            { id: 'sphere', name: 'Defensive Sphere', icon: ShieldAlert, desc: 'Protect high-value asset.' },
                        ].map(f => (
                            <button 
                                key={f.id}
                                onClick={() => handleBroadcast(`formation_${f.id}`)}
                                disabled={!!processingAction}
                                className="flex flex-col gap-3 p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl hover:bg-zinc-800 hover:border-zinc-700 transition-all text-left group disabled:opacity-50"
                            >
                                <div className="flex justify-between items-start">
                                    <div className="p-2 bg-black rounded-lg border border-zinc-800 group-hover:border-zinc-600">
                                        <f.icon size={20} className="text-white" />
                                    </div>
                                    {processingAction === `formation_${f.id}` && <span className="text-[10px] text-primary animate-pulse">SYNCING...</span>}
                                </div>
                                <div>
                                    <h3 className="font-bold text-white text-sm">{f.name}</h3>
                                    <p className="text-xs text-zinc-500 mt-1">{f.desc}</p>
                                </div>
                            </button>
                        ))}
                    </div>
                )}

                {activeTab === 'broadcast' && (
                    <div className="space-y-6">
                        <div className="bg-red-950/20 border border-red-900/30 p-4 rounded-xl">
                            <h3 className="text-red-400 font-bold text-sm mb-3 flex items-center gap-2">
                                <ShieldAlert size={16} /> EMERGENCY OVERRIDES
                            </h3>
                            <div className="grid grid-cols-2 gap-3">
                                <button onClick={() => handleBroadcast('emergency_land')} className="bg-red-900/20 border border-red-900/50 hover:bg-red-900/40 text-red-500 py-3 rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition-colors">
                                    <ArrowDownCircle size={16} />
                                    EMERGENCY LAND
                                </button>
                                <button onClick={() => handleBroadcast('return_home')} className="bg-red-900/20 border border-red-900/50 hover:bg-red-900/40 text-red-500 py-3 rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition-colors">
                                    <Home size={16} />
                                    RETURN TO BASE
                                </button>
                            </div>
                        </div>

                        <div>
                            <h3 className="text-white font-bold text-sm mb-3">Routine Broadcasts</h3>
                            <div className="grid grid-cols-2 gap-3">
                                <button onClick={() => handleBroadcast('sync_lights')} className="bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 py-3 rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition-colors">
                                    <Zap size={16} />
                                    Sync Lights
                                </button>
                                <button onClick={() => handleBroadcast('calibrate_sensors')} className="bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 py-3 rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition-colors">
                                    Calibrate Sensors
                                </button>
                            </div>
                        </div>
                    </div>
                )}
                
                {activeTab === 'config' && (
                    <div className="text-center py-10 text-zinc-500 text-xs font-mono">
                        GLOBAL CONFIGURATION PARAMETERS LOCKED BY ADMIN
                    </div>
                )}
            </div>
        </div>
    </div>
  );
};
