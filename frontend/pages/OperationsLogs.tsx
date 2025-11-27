
import React, { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';
import { Activity, AlertTriangle, CheckCircle, Info, Search, Filter } from 'lucide-react';
import { cn } from '../lib/utils';

export const OperationsLogs: React.FC = () => {
    const { logs, fetchLogs } = useStore();
    const [filterLevel, setFilterLevel] = useState<string>('ALL');
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchLogs();
        const interval = setInterval(fetchLogs, 10000); // Poll logs
        return () => clearInterval(interval);
    }, [fetchLogs]);

    const filteredLogs = logs.filter(log => {
        if (filterLevel !== 'ALL' && log.level !== filterLevel) return false;
        if (searchTerm && !log.message.toLowerCase().includes(searchTerm.toLowerCase()) && !log.module.toLowerCase().includes(searchTerm.toLowerCase())) return false;
        return true;
    }).sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    const getIcon = (level: string) => {
        switch(level) {
            case 'ERROR': return <AlertTriangle size={14} className="text-red-500" />;
            case 'WARNING': return <AlertTriangle size={14} className="text-amber-500" />;
            case 'SUCCESS': return <CheckCircle size={14} className="text-emerald-500" />;
            default: return <Info size={14} className="text-blue-500" />;
        }
    };

    return (
        <div className="h-full flex flex-col gap-6">
             <div className="flex flex-col gap-2">
                 <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
                     <Activity className="text-zinc-500"/> System Logs
                 </h1>
                 <p className="text-sm text-zinc-500 font-medium">Audit trail of system events, errors, and operational milestones.</p>
             </div>

             <div className="bg-surface border border-zinc-800 rounded-xl flex-1 flex flex-col overflow-hidden shadow-lg">
                 {/* Toolbar */}
                 <div className="p-4 border-b border-zinc-800 bg-zinc-900/50 flex justify-between items-center gap-4">
                     <div className="relative flex-1 max-w-md">
                         <Search className="absolute left-3 top-2.5 text-zinc-500 w-4 h-4" />
                         <input 
                            className="w-full bg-black/30 border border-zinc-700 rounded-lg pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-primary placeholder:text-zinc-600"
                            placeholder="Search logs..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                         />
                     </div>
                     <div className="flex gap-2">
                         {['ALL', 'INFO', 'WARNING', 'ERROR', 'SUCCESS'].map(lvl => (
                             <button
                                key={lvl}
                                onClick={() => setFilterLevel(lvl)}
                                className={cn(
                                    "px-3 py-1.5 rounded-md text-xs font-bold uppercase border transition-colors",
                                    filterLevel === lvl 
                                    ? "bg-white text-black border-white" 
                                    : "bg-zinc-900 text-zinc-500 border-zinc-800 hover:border-zinc-600 hover:text-white"
                                )}
                             >
                                 {lvl}
                             </button>
                         ))}
                     </div>
                 </div>

                 {/* Log Table */}
                 <div className="flex-1 overflow-y-auto custom-scrollbar">
                     <table className="w-full text-left border-collapse">
                         <thead className="bg-zinc-900 text-[10px] text-zinc-500 font-bold uppercase tracking-wider sticky top-0">
                             <tr>
                                 <th className="px-6 py-3 border-b border-zinc-800">Timestamp</th>
                                 <th className="px-6 py-3 border-b border-zinc-800">Level</th>
                                 <th className="px-6 py-3 border-b border-zinc-800">Module</th>
                                 <th className="px-6 py-3 border-b border-zinc-800 w-full">Message</th>
                             </tr>
                         </thead>
                         <tbody className="divide-y divide-zinc-800/50">
                             {filteredLogs.map(log => (
                                 <tr key={log.id} className="hover:bg-white/5 transition-colors group">
                                     <td className="px-6 py-3 text-xs font-mono text-zinc-500 whitespace-nowrap">
                                         {new Date(log.timestamp).toLocaleString()}
                                     </td>
                                     <td className="px-6 py-3">
                                         <div className="flex items-center gap-2">
                                            {getIcon(log.level)}
                                            <span className={cn(
                                                "text-xs font-bold",
                                                log.level === 'ERROR' ? "text-red-400" : 
                                                log.level === 'WARNING' ? "text-amber-400" :
                                                log.level === 'SUCCESS' ? "text-emerald-400" : "text-blue-400"
                                            )}>
                                                {log.level}
                                            </span>
                                         </div>
                                     </td>
                                     <td className="px-6 py-3">
                                         <span className="px-2 py-1 rounded bg-zinc-800 border border-zinc-700 text-[10px] font-mono text-zinc-300">
                                             {log.module}
                                         </span>
                                     </td>
                                     <td className="px-6 py-3 text-sm text-zinc-300 font-medium truncate max-w-xl" title={log.message}>
                                         {log.message}
                                     </td>
                                 </tr>
                             ))}
                             {filteredLogs.length === 0 && (
                                 <tr>
                                     <td colSpan={4} className="px-6 py-12 text-center text-zinc-500 text-sm italic">
                                         No logs found matching criteria
                                     </td>
                                 </tr>
                             )}
                         </tbody>
                     </table>
                 </div>
             </div>
        </div>
    );
};
