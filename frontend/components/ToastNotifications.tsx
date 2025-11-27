
import React from 'react';
import { useStore } from '../store/useStore';
import { X, CheckCircle, AlertTriangle, Info, AlertCircle } from 'lucide-react';
import { cn } from '../lib/utils';

export const ToastNotifications: React.FC = () => {
  const { notifications, removeNotification } = useStore();

  const getIcon = (type: string) => {
      switch(type) {
          case 'success': return <CheckCircle size={16} className="text-emerald-500" />;
          case 'error': return <AlertCircle size={16} className="text-red-500" />;
          case 'warning': return <AlertTriangle size={16} className="text-amber-500" />;
          default: return <Info size={16} className="text-blue-500" />;
      }
  };

  const getBorderColor = (type: string) => {
      switch(type) {
          case 'success': return 'border-emerald-500/50 bg-emerald-950/20';
          case 'error': return 'border-red-500/50 bg-red-950/20';
          case 'warning': return 'border-amber-500/50 bg-amber-950/20';
          default: return 'border-blue-500/50 bg-blue-950/20';
      }
  };

  return (
    <div className="fixed top-6 right-6 z-[9999] flex flex-col gap-2 pointer-events-none">
      {notifications.map(n => (
          <div 
            key={n.id}
            className={cn(
                "pointer-events-auto min-w-[300px] p-3 rounded-lg border shadow-xl flex items-start gap-3 animate-in slide-in-from-right fade-in duration-300",
                getBorderColor(n.type),
                "backdrop-blur-md"
            )}
          >
             <div className="mt-0.5">{getIcon(n.type)}</div>
             <div className="flex-1">
                 <p className="text-sm font-medium text-white">{n.message}</p>
             </div>
             <button 
                onClick={() => removeNotification(n.id)}
                className="text-zinc-500 hover:text-white transition-colors"
             >
                 <X size={14} />
             </button>
          </div>
      ))}
    </div>
  );
};
