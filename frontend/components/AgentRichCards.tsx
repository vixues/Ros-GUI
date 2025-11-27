
import React from 'react';
import { Drone, DroneStatus, TaskStatus } from '../types';
import { Battery, Wifi, ArrowUp, MapPin, Target, AlertTriangle, CheckCircle2, Clock, Scan, Video, ShieldAlert } from 'lucide-react';
import { cn } from '../lib/utils';

// --- IMAGE ANALYSIS CARD ---
export const ImageAnalysisCard = ({ data }: { data: { url: string, objects: string[], confidence: number, location: string } }) => (
  <div className="bg-black border border-zinc-800 rounded-lg overflow-hidden w-full max-w-sm mt-2 font-sans shadow-lg">
    <div className="relative group">
      {/* Scanline Overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-10 bg-[length:100%_2px,3px_100%] pointer-events-none opacity-50"></div>
      
      <img src={data.url} alt="Analysis" className="w-full h-48 object-cover opacity-80" />
      
      {/* HUD Overlays */}
      <div className="absolute top-2 left-2 bg-black/70 backdrop-blur px-2 py-0.5 rounded border border-red-500/50 flex items-center gap-1.5">
         <div className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse"></div>
         <span className="text-[9px] font-mono text-red-500 font-bold">REC</span>
      </div>
      
      {/* Bounding Box Sim */}
      <div className="absolute top-1/4 left-1/4 w-24 h-24 border border-primary/70 rounded-sm">
         <div className="absolute -top-3 left-0 bg-primary/20 px-1 text-[8px] text-primary font-mono">{data.objects[0]} {(data.confidence * 100).toFixed(0)}%</div>
      </div>
    </div>
    
    <div className="p-3 bg-zinc-900 border-t border-zinc-800">
      <div className="flex justify-between items-start mb-2">
         <h4 className="text-xs font-bold text-white flex items-center gap-2">
            <Scan size={14} className="text-primary" />
            Object Detection
         </h4>
         <span className="text-[10px] font-mono text-zinc-500">{data.location}</span>
      </div>
      <div className="flex gap-2 flex-wrap">
         {data.objects.map((obj, i) => (
            <span key={i} className="px-1.5 py-0.5 bg-zinc-800 border border-zinc-700 rounded text-[9px] text-zinc-300 uppercase font-medium">
               {obj}
            </span>
         ))}
      </div>
    </div>
  </div>
);

// --- DRONE TELEMETRY CARD (Chat Version) ---
export const DroneTelemetryCard = ({ drone }: { drone: Drone }) => {
    const isOnline = drone.status !== DroneStatus.OFFLINE;
    
    return (
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-3 w-full max-w-xs mt-2 shadow-md">
            <div className="flex justify-between items-center mb-3 pb-2 border-b border-zinc-800/50">
                <div className="flex items-center gap-2">
                    <div className={cn("w-2 h-2 rounded-full", isOnline ? "bg-emerald-500" : "bg-red-500")}></div>
                    <span className="font-bold text-white text-xs">{drone.name}</span>
                </div>
                <span className="text-[9px] px-1.5 py-0.5 bg-zinc-800 rounded border border-zinc-700 text-zinc-400 font-mono">
                    {drone.serial_number}
                </span>
            </div>
            
            <div className="grid grid-cols-2 gap-2 mb-3">
                <div className="bg-black/40 p-2 rounded border border-zinc-800">
                    <div className="flex justify-between text-[9px] text-zinc-500 font-bold uppercase mb-1">
                        <span>Power</span>
                        <Battery size={10} />
                    </div>
                    <div className={cn("text-sm font-mono font-bold", drone.battery_level < 20 ? "text-red-500" : "text-white")}>
                        {drone.battery_level}%
                    </div>
                </div>
                 <div className="bg-black/40 p-2 rounded border border-zinc-800">
                    <div className="flex justify-between text-[9px] text-zinc-500 font-bold uppercase mb-1">
                        <span>Altitude</span>
                        <ArrowUp size={10} />
                    </div>
                    <div className="text-sm font-mono font-bold text-white">
                        {drone.altitude?.toFixed(0)}m
                    </div>
                </div>
            </div>
            
            <div className="flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 p-2 rounded">
                 <Target size={12} className="text-blue-400" />
                 <span className="text-[10px] text-blue-200 font-medium">
                    Current Task: Sector Surveillance
                 </span>
            </div>
        </div>
    );
};

// --- MISSION VISUALIZATION CARD ---
export const MissionProgressCard = ({ data }: { data: { title: string, status: string, progress: number, steps: string[] } }) => (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg w-full max-w-sm mt-2 overflow-hidden">
        <div className="p-3 bg-zinc-950 border-b border-zinc-800 flex justify-between items-center">
            <div className="flex items-center gap-2">
                <ShieldAlert size={14} className="text-amber-500" />
                <span className="text-xs font-bold text-white uppercase tracking-wide">{data.title}</span>
            </div>
            <span className="text-[9px] font-mono text-amber-500 animate-pulse">{data.status}</span>
        </div>
        
        <div className="p-4">
             {/* Progress Bar */}
             <div className="flex justify-between text-[9px] font-bold text-zinc-500 mb-1">
                 <span>COMPLETION</span>
                 <span>{data.progress}%</span>
             </div>
             <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden mb-4">
                 <div className="h-full bg-amber-500 transition-all duration-1000" style={{ width: `${data.progress}%` }}></div>
             </div>
             
             {/* Steps Visualization */}
             <div className="space-y-3 relative">
                 {/* Connecting Line */}
                 <div className="absolute left-1.5 top-2 bottom-2 w-px bg-zinc-800"></div>
                 
                 {data.steps.map((step, idx) => {
                     const isCompleted = idx / data.steps.length < data.progress / 100;
                     const isCurrent = !isCompleted && idx === Math.floor((data.progress / 100) * data.steps.length);
                     
                     return (
                         <div key={idx} className="flex items-start gap-3 relative z-10">
                             <div className={cn(
                                 "w-3 h-3 rounded-full border-2 flex-shrink-0 bg-zinc-900",
                                 isCompleted ? "border-emerald-500 bg-emerald-500" : isCurrent ? "border-amber-500 animate-pulse" : "border-zinc-700"
                             )}></div>
                             <div className="flex-1 -mt-1">
                                 <div className={cn("text-[10px] font-bold uppercase", isCompleted ? "text-zinc-400 line-through" : isCurrent ? "text-white" : "text-zinc-600")}>
                                     {step}
                                 </div>
                             </div>
                         </div>
                     )
                 })}
             </div>
        </div>
        
        {/* Visual Map Placeholder */}
        <div className="h-24 bg-black relative border-t border-zinc-800 overflow-hidden">
             <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'radial-gradient(#555 1px, transparent 1px)', backgroundSize: '10px 10px' }}></div>
             {/* Simulated Drone Path */}
             <svg className="absolute inset-0 w-full h-full p-4 overflow-visible">
                 <path d="M 20 50 Q 80 20 150 50 T 280 50" fill="none" stroke="#f59e0b" strokeWidth="2" strokeDasharray="4 2" />
                 <circle cx="150" cy="50" r="3" fill="white" className="animate-ping" />
             </svg>
             <div className="absolute bottom-1 right-2 text-[8px] font-mono text-zinc-500">TACTICAL MAP PREVIEW</div>
        </div>
    </div>
);
