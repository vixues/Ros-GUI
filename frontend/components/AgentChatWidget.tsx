
import React, { useState, useRef, useEffect } from 'react';
import { api } from '../services/api';
import { useStore } from '../store/useStore';
import { Send, Sparkles } from 'lucide-react';
import { AgentMessage } from '../types';
import { cn } from '../lib/utils';
import { ImageAnalysisCard, DroneTelemetryCard, MissionProgressCard } from './AgentRichCards';

export const AgentChatWidget: React.FC = () => {
  const { messages, addMessage } = useStore();
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const sessionId = useRef(`session-${Date.now()}`);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg: AgentMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
      type: 'text'
    };

    addMessage(userMsg);
    setInput('');
    setIsTyping(true);

    try {
      const response = await api.sendAgentMessage(sessionId.current, userMsg.content);
      
      const botMsg: AgentMessage = {
        role: 'assistant',
        content: response.response,
        type: response.type as any || 'text',
        data: response.data,
        timestamp: new Date().toISOString()
      };
      
      addMessage(botMsg);
      
      if(response.actions && response.actions.length > 0) {
         addMessage({
             role: 'system',
             content: `CMD EXECUTED: ${response.actions.map(a => a.action_type).join(', ')}`,
             timestamp: new Date().toISOString(),
             type: 'text'
         });
      }

    } catch (error) {
      addMessage({
        role: 'system',
        content: 'ERR: Uplink Failed',
        timestamp: new Date().toISOString(),
        type: 'text'
      });
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-zinc-900/50">
        {/* Chat Header */}
        <div className="p-3 border-b border-zinc-800 bg-zinc-900 flex items-center gap-2">
            <div className="p-1.5 bg-primary/10 rounded">
                <Sparkles size={14} className="text-primary" />
            </div>
            <div>
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">AI Commander</h3>
                <div className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span className="text-[9px] text-zinc-500 font-mono">ONLINE</span>
                </div>
            </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-3 space-y-4 custom-scrollbar" ref={scrollRef}>
            {messages.map((msg, idx) => (
                <div key={idx} className={cn("flex flex-col gap-1", msg.role === 'user' ? "items-end" : "items-start")}>
                    <div className={cn(
                        "max-w-[95%] p-2.5 rounded-lg text-xs leading-relaxed shadow-sm",
                        msg.role === 'user' 
                        ? 'bg-zinc-800 text-white rounded-tr-none' 
                        : msg.role === 'system'
                        ? 'bg-red-500/10 border border-red-500/20 text-red-400 font-mono'
                        : 'bg-black/40 border border-zinc-800 text-zinc-300 rounded-tl-none'
                    )}>
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                        
                        {/* Rich Content (Compact for Sidebar) */}
                         {msg.type === 'image' && msg.data && (
                             <ImageAnalysisCard data={msg.data} />
                         )}
                         {msg.type === 'drone_telemetry' && msg.data && (
                             <DroneTelemetryCard drone={msg.data} />
                         )}
                         {msg.type === 'mission_status' && msg.data && (
                             <MissionProgressCard data={msg.data} />
                         )}
                    </div>
                    <span className="text-[9px] text-zinc-600 font-mono px-1">
                        {new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </span>
                </div>
            ))}
            
            {isTyping && (
                <div className="flex items-center gap-2 p-2">
                    <div className="w-1.5 h-1.5 bg-zinc-600 rounded-full animate-bounce"></div>
                    <div className="w-1.5 h-1.5 bg-zinc-600 rounded-full animate-bounce delay-75"></div>
                    <div className="w-1.5 h-1.5 bg-zinc-600 rounded-full animate-bounce delay-150"></div>
                </div>
            )}
        </div>

        {/* Input Area */}
        <div className="p-3 border-t border-zinc-800 bg-zinc-900">
            <div className="relative">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Enter command..."
                    className="w-full bg-black/50 border border-zinc-700 text-white pl-3 pr-10 py-2.5 rounded-md focus:border-primary focus:outline-none text-xs font-medium"
                />
                <button 
                    onClick={handleSend}
                    disabled={!input.trim() || isTyping}
                    className="absolute right-1 top-1 p-1.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded transition-colors disabled:opacity-50"
                >
                    <Send size={12} />
                </button>
            </div>
            
            {/* Quick Chips */}
            <div className="flex gap-2 mt-2 overflow-x-auto pb-1 no-scrollbar">
                {['Status', 'Scan', 'Mission'].map(cmd => (
                    <button 
                        key={cmd}
                        onClick={() => setInput(cmd)}
                        className="px-2 py-1 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded text-[9px] font-bold text-zinc-400 whitespace-nowrap"
                    >
                        {cmd}
                    </button>
                ))}
            </div>
        </div>
    </div>
  );
};
