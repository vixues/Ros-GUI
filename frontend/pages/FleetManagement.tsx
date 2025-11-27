
import React, { useState, useMemo } from 'react';
import { useStore } from '../store/useStore';
import { Drone, DroneStatus, TaskPriority, TaskStatus } from '../types';
import { api } from '../services/api';
import { cn } from '../lib/utils';
import { 
    Search, ArrowUp, ArrowDown, MoreHorizontal, 
    RefreshCw, ArrowDown as ArrowDownIcon,
    Check, Square, PlayCircle, Loader2, X, Target, Zap
} from 'lucide-react';
import { DroneDetailCard } from '../components/DroneDetailCard';

// --- Sub-Component: Quick Task Modal ---
const QuickTaskModal = ({ droneIds, onClose, onConfirm }: { droneIds: number[], onClose: () => void, onConfirm: (title: string, priority: TaskPriority) => Promise<void> }) => {
    const [title, setTitle] = useState('');
    const [priority, setPriority] = useState<TaskPriority>(TaskPriority.MEDIUM);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async () => {
        setIsSubmitting(true);
        await onConfirm(title, priority);
        setIsSubmitting(false);
        onClose();
    };

    return (
        <div className="fixed inset-0 z-[600] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="bg-surface border border-zinc-800 rounded-xl w-full max-w-md shadow-2xl animate-in fade-in zoom-in duration-200">
                <div className="p-4 border-b border-zinc-800 flex justify-between items-center bg-zinc-900/50">
                    <h3 className="font-bold text-white flex items-center gap-2">
                        <Target size={16} className="text-primary"/>
                        Assign Mission
                    </h3>
                    <button onClick={onClose}><X size={18} className="text-zinc-500 hover:text-white"/></button>
                </div>
                <div className="p-6 space-y-4">
                    <div className="text-xs text-zinc-400 font-mono">
                        TARGETING: <span className="text-white font-bold">{droneIds.length} UNIT(S)</span>
                    </div>
                    <div>
                        <label className="text-[10px] uppercase font-bold text-zinc-500 block mb-1">Mission Directive</label>
                        <input 
                            autoFocus
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="e.g. Sector 4 Surveillance"
                            className="w-full bg-black/50 border border-zinc-700 rounded p-2 text-sm text-white focus:border-primary focus:outline-none"
                        />
                    </div>
                    <div>
                        <label className="text-[10px] uppercase font-bold text-zinc-500 block mb-1">Priority</label>
                        <div className="flex gap-2">
                            {[TaskPriority.LOW, TaskPriority.MEDIUM, TaskPriority.HIGH, TaskPriority.CRITICAL].map(p => (
                                <button
                                    key={p}
                                    onClick={() => setPriority(p)}
                                    className={cn(
                                        "flex-1 py-2 text-[10px] font-bold uppercase rounded border transition-all",
                                        priority === p 
                                        ? "bg-white text-black border-white" 
                                        : "bg-zinc-900 text-zinc-500 border-zinc-800 hover:border-zinc-600"
                                    )}
                                >
                                    {p}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
                <div className="p-4 border-t border-zinc-800 flex justify-end gap-2 bg-zinc-900/50">
                    <button onClick={onClose} className="px-3 py-2 text-xs font-bold text-zinc-400 hover:text-white">Cancel</button>
                    <button 
                        onClick={handleSubmit}
                        disabled={!title || isSubmitting}
                        className="bg-primary text-white px-4 py-2 rounded text-xs font-bold flex items-center gap-2 hover:bg-blue-600 disabled:opacity-50"
                    >
                        {isSubmitting && <Loader2 size={12} className="animate-spin" />}
                        Confirm Assignment
                    </button>
                </div>
            </div>
        </div>
    );
};

export const FleetManagement: React.FC = () => {
    const { drones, updateDrone, addTaskLocally, addNotification } = useStore();
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState<DroneStatus | 'ALL'>('ALL');
    const [selectedIds, setSelectedIds] = useState<number[]>([]);
    const [sortConfig, setSortConfig] = useState<{ key: keyof Drone, direction: 'asc' | 'desc' } | null>(null);
    
    // Action States
    const [isBulkLoading, setIsBulkLoading] = useState<string | null>(null); // 'land' | 'reboot'
    const [quickTaskTarget, setQuickTaskTarget] = useState<number[] | null>(null); // IDs to assign task to
    const [detailDroneId, setDetailDroneId] = useState<number | null>(null); // ID for detail drawer

    // Filter & Sort Logic
    const filteredData = useMemo(() => {
        let data = [...drones];

        if (statusFilter !== 'ALL') {
            data = data.filter(d => d.status === statusFilter);
        }

        if (searchTerm) {
            data = data.filter(d => 
                d.name?.toLowerCase().includes(searchTerm.toLowerCase()) || 
                d.serial_number.toLowerCase().includes(searchTerm.toLowerCase())
            );
        }

        if (sortConfig) {
            data.sort((a, b) => {
                const aVal = a[sortConfig.key] ?? '';
                const bVal = b[sortConfig.key] ?? '';
                
                if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
                if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
                return 0;
            });
        }
        return data;
    }, [drones, statusFilter, searchTerm, sortConfig]);

    const handleSort = (key: keyof Drone) => {
        let direction: 'asc' | 'desc' = 'asc';
        if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };

    const toggleSelectAll = () => {
        if (selectedIds.length === filteredData.length) {
            setSelectedIds([]);
        } else {
            setSelectedIds(filteredData.map(d => d.id));
        }
    };

    const toggleSelectRow = (id: number) => {
        if (selectedIds.includes(id)) {
            setSelectedIds(selectedIds.filter(sid => sid !== id));
        } else {
            setSelectedIds([...selectedIds, id]);
        }
    };

    // --- Bulk Action Handlers ---

    const handleBulkLand = async () => {
        if (selectedIds.length === 0) return;
        setIsBulkLoading('land');
        
        // Optimistic Update
        selectedIds.forEach(id => updateDrone(id, { status: DroneStatus.LANDED }));

        try {
            await Promise.all(selectedIds.map(id => api.landDrone(id)));
            addNotification('success', `Landing initiated for ${selectedIds.length} units`);
        } catch (error) {
            console.error("Bulk Land Failed", error);
            addNotification('error', "Failed to execute bulk landing");
        } finally {
            setIsBulkLoading(null);
            setSelectedIds([]);
        }
    };

    const handleBulkReboot = async () => {
        if (selectedIds.length === 0) return;
        setIsBulkLoading('reboot');
        
        selectedIds.forEach(id => updateDrone(id, { status: DroneStatus.OFFLINE }));

        try {
            await Promise.all(selectedIds.map(id => api.rebootDrone(id)));
            addNotification('success', `Reboot signal sent to ${selectedIds.length} units`);
            // Simulate coming back online
            setTimeout(() => {
                selectedIds.forEach(id => updateDrone(id, { status: DroneStatus.IDLE }));
            }, 2000);
        } catch (error) {
            console.error("Bulk Reboot Failed", error);
            addNotification('error', "Failed to execute bulk reboot");
        } finally {
            setIsBulkLoading(null);
            setSelectedIds([]);
        }
    };

    const handleAssignTask = async (title: string, priority: TaskPriority) => {
        if (!quickTaskTarget) return;

        try {
            const newTask = await api.createTask({
                title,
                description: "Quick Assignment via Fleet Control",
                priority,
                status: TaskStatus.PENDING,
                assigned_drone_ids: quickTaskTarget
            });
            addTaskLocally(newTask);
            
            // Visual feedback update on drones if needed
            quickTaskTarget.forEach(id => {
                const d = drones.find(drone => drone.id === id);
                if (d && d.status === DroneStatus.IDLE) {
                    updateDrone(id, { status: DroneStatus.ARMED });
                }
            });
            addNotification('success', `Task "${title}" assigned to ${quickTaskTarget.length} units`);

        } catch (error) {
            console.error("Task Assignment Failed", error);
            addNotification('error', "Failed to assign task");
        }
    };

    const getStatusBadge = (status: DroneStatus) => {
        const styles = {
            [DroneStatus.FLYING]: 'bg-blue-500/20 text-blue-400 border-blue-500/20',
            [DroneStatus.IDLE]: 'bg-amber-500/20 text-amber-400 border-amber-500/20',
            [DroneStatus.ERROR]: 'bg-red-500/20 text-red-400 border-red-500/20',
            [DroneStatus.OFFLINE]: 'bg-zinc-800 text-zinc-500 border-zinc-700',
            [DroneStatus.RETURNING]: 'bg-purple-500/20 text-purple-400 border-purple-500/20',
            [DroneStatus.LANDED]: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/20',
            [DroneStatus.ARMED]: 'bg-white/10 text-white border-white/20'
        };
        return (
            <span className={cn("px-2 py-0.5 rounded text-[10px] font-bold uppercase border", styles[status])}>
                {status}
            </span>
        );
    };

    const detailDrone = drones.find(d => d.id === detailDroneId);

    return (
        <div className="h-full flex flex-col gap-4 relative">
            {/* Header / Controls */}
            <div className="flex flex-col gap-4 bg-surface rounded-xl p-4 border border-zinc-800/50 shadow-md">
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-xl font-bold text-white">Fleet Control</h1>
                        <p className="text-sm text-zinc-500">Manage swarm configurations and bulk directives</p>
                    </div>
                    <div className="flex gap-2">
                         <button 
                            disabled={selectedIds.length === 0 || !!isBulkLoading}
                            onClick={handleBulkLand}
                            className="bg-zinc-800 text-white px-3 py-2 rounded-lg text-xs font-bold flex items-center gap-2 hover:bg-zinc-700 disabled:opacity-50 transition-all"
                         >
                             {isBulkLoading === 'land' ? <Loader2 size={14} className="animate-spin" /> : <ArrowDownIcon size={14} />} 
                             Land Selected
                         </button>
                         <button 
                            disabled={selectedIds.length === 0 || !!isBulkLoading}
                            onClick={handleBulkReboot}
                            className="bg-zinc-800 text-white px-3 py-2 rounded-lg text-xs font-bold flex items-center gap-2 hover:bg-zinc-700 disabled:opacity-50 transition-all"
                         >
                             {isBulkLoading === 'reboot' ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />} 
                             Reboot Selected
                         </button>
                    </div>
                </div>

                <div className="flex gap-4 items-center">
                    <div className="relative flex-1 max-w-md">
                        <Search className="absolute left-3 top-2.5 text-zinc-500 w-4 h-4" />
                        <input 
                            className="w-full bg-black/30 border border-zinc-700 rounded-lg pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-primary placeholder:text-zinc-600 transition-colors focus:bg-black/50"
                            placeholder="Search by ID or Serial..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    
                    <div className="flex gap-2">
                        {['ALL', 'FLYING', 'IDLE', 'ERROR', 'OFFLINE'].map((s) => (
                             <button
                                key={s}
                                onClick={() => setStatusFilter(s as any)}
                                className={cn(
                                    "px-3 py-1.5 rounded-md text-xs font-bold uppercase transition-colors border",
                                    statusFilter === s 
                                    ? "bg-white text-black border-white" 
                                    : "bg-zinc-900 text-zinc-500 border-zinc-800 hover:border-zinc-600 hover:text-zinc-300"
                                )}
                             >
                                {s}
                             </button>
                        ))}
                    </div>
                    <div className="ml-auto text-xs font-mono text-zinc-500">
                        {filteredData.length} UNITS FOUND
                    </div>
                </div>
            </div>

            {/* Data Grid */}
            <div className="flex-1 bg-surface rounded-xl border border-zinc-800/50 flex flex-col min-h-0 overflow-hidden shadow-lg relative">
                {/* Table Header */}
                <div className="flex items-center px-4 py-3 bg-zinc-900/50 border-b border-zinc-800 text-xs font-bold text-zinc-400 uppercase tracking-wider">
                    <div className="w-10 flex justify-center cursor-pointer" onClick={toggleSelectAll}>
                        {selectedIds.length > 0 && selectedIds.length === filteredData.length 
                            ? <Check size={14} className="text-primary" /> 
                            : <Square size={14} />
                        }
                    </div>
                    <div className="flex-1 cursor-pointer hover:text-white flex items-center gap-1" onClick={() => handleSort('name')}>
                        Unit ID {sortConfig?.key === 'name' && (sortConfig.direction === 'asc' ? <ArrowUp size={10}/> : <ArrowDown size={10}/>)}
                    </div>
                    <div className="w-32 cursor-pointer hover:text-white" onClick={() => handleSort('status')}>Status</div>
                    <div className="w-24 text-right cursor-pointer hover:text-white" onClick={() => handleSort('battery_level')}>Battery</div>
                    <div className="w-24 text-right cursor-pointer hover:text-white" onClick={() => handleSort('altitude')}>Altitude</div>
                    <div className="w-40 text-center">Coordinates</div>
                    <div className="w-24 text-center">Actions</div>
                </div>

                {/* Table Body */}
                <div className="flex-1 overflow-y-auto custom-scrollbar">
                    {filteredData.map(drone => (
                        <div 
                            key={drone.id} 
                            className={cn(
                                "flex items-center px-4 py-3 border-b border-zinc-800/50 text-sm transition-colors hover:bg-white/5",
                                selectedIds.includes(drone.id) && "bg-primary/5"
                            )}
                        >
                            <div className="w-10 flex justify-center cursor-pointer" onClick={() => toggleSelectRow(drone.id)}>
                                {selectedIds.includes(drone.id) 
                                    ? <Check size={14} className="text-primary" /> 
                                    : <Square size={14} className="text-zinc-600" />
                                }
                            </div>
                            <div className="flex-1 font-mono font-medium text-white flex flex-col">
                                <span>{drone.name}</span>
                                <span className="text-[10px] text-zinc-600">{drone.serial_number}</span>
                            </div>
                            <div className="w-32">
                                {getStatusBadge(drone.status)}
                            </div>
                            <div className="w-24 text-right font-mono flex items-center justify-end gap-2">
                                <div className={cn("h-1.5 w-12 rounded-full bg-zinc-800 overflow-hidden")}>
                                    <div className={cn("h-full rounded-full", drone.battery_level < 20 ? "bg-red-500" : "bg-white")} style={{width: `${drone.battery_level}%`}} />
                                </div>
                                <span className={cn(drone.battery_level < 20 ? "text-red-500" : "text-zinc-300")}>{drone.battery_level}%</span>
                            </div>
                            <div className="w-24 text-right font-mono text-zinc-300">
                                {drone.altitude?.toFixed(1)}m
                            </div>
                            <div className="w-40 text-center font-mono text-[10px] text-zinc-500">
                                {drone.latitude?.toFixed(5)}, {drone.longitude?.toFixed(5)}
                            </div>
                            <div className="w-24 flex justify-center gap-2">
                                <button 
                                    title="Assign Task" 
                                    onClick={() => setQuickTaskTarget([drone.id])} 
                                    className="p-1.5 hover:bg-zinc-700 rounded text-zinc-400 hover:text-white transition-colors"
                                >
                                    <PlayCircle size={14} />
                                </button>
                                <button 
                                    title="Details" 
                                    onClick={() => setDetailDroneId(drone.id)}
                                    className={cn(
                                        "p-1.5 hover:bg-zinc-700 rounded transition-colors",
                                        detailDroneId === drone.id ? "text-primary bg-primary/10" : "text-zinc-400 hover:text-white"
                                    )}
                                >
                                    <MoreHorizontal size={14} />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Quick Task Modal */}
            {quickTaskTarget && (
                <QuickTaskModal 
                    droneIds={quickTaskTarget} 
                    onClose={() => setQuickTaskTarget(null)} 
                    onConfirm={handleAssignTask}
                />
            )}

            {/* Details Drawer */}
            <div className={cn(
                "absolute top-0 right-0 h-full w-[320px] bg-black/95 border-l border-zinc-800 shadow-2xl transition-transform duration-300 z-50 flex flex-col",
                detailDroneId ? "translate-x-0" : "translate-x-full"
            )}>
                <div className="p-4 border-b border-zinc-800 flex justify-between items-center">
                    <h3 className="font-bold text-white uppercase tracking-wider text-xs">Unit Details</h3>
                    <button onClick={() => setDetailDroneId(null)} className="text-zinc-500 hover:text-white">
                        <X size={16} />
                    </button>
                </div>
                <div className="flex-1 p-4 overflow-y-auto">
                    {detailDrone ? (
                        <div className="scale-100 origin-top">
                             <DroneDetailCard drone={detailDrone} />
                             
                             <div className="mt-4 p-4 bg-zinc-900/50 rounded-lg border border-zinc-800">
                                <h4 className="text-xs font-bold text-white mb-2 flex items-center gap-2">
                                    <Zap size={14} className="text-amber-500"/> System Diagnostics
                                </h4>
                                <div className="space-y-2 text-[10px] font-mono text-zinc-400">
                                    <div className="flex justify-between"><span>IMU SENSOR:</span> <span className="text-success">CALIBRATED</span></div>
                                    <div className="flex justify-between"><span>GPS FIX:</span> <span className="text-white">3D LOCK (12 SAT)</span></div>
                                    <div className="flex justify-between"><span>MOTOR TEMP:</span> <span className="text-white">42°C</span></div>
                                    <div className="flex justify-between"><span>LINK QUALITY:</span> <span className="text-success">98%</span></div>
                                    <div className="flex justify-between"><span>UPTIME:</span> <span className="text-zinc-500">14H 23M</span></div>
                                </div>
                             </div>
                        </div>
                    ) : (
                        <div className="text-center text-zinc-500 text-xs mt-10">Select a unit</div>
                    )}
                </div>
            </div>
        </div>
    );
};
