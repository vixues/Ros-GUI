
import React, { useState, useRef, useEffect } from 'react';
import { api } from '../services/api';
import { useStore } from '../store/useStore';
import { Send, Bot, User, Code2, Terminal, Sparkles } from 'lucide-react';
import { AgentMessage } from '../types';
import { cn } from '../lib/utils';
import { ImageAnalysisCard, DroneTelemetryCard, MissionProgressCard } from '../components/AgentRichCards';

export const AgentConsole: React.FC = () => {
  const { messages, addMessage } = useStore();
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const sessionId = useRef(`session-${Date.now()}`);

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
             content: `EXECUTED: ${response.actions.map(a => a.action_type).join(', ')}`,
             timestamp: new Date().toISOString(),
             type: 'text'
         });
      }

    } catch (error) {
      addMessage({
        role: 'system',
        content: 'ERROR: Uplink to Agent failed.',
        timestamp: new Date().toISOString(),
        type: 'text'
      });
    } finally {
      setIsTyping(false);
    }
  };

  const renderMessageContent = (msg: AgentMessage) => {
      return (
          <div className="flex flex-col gap-2">
              <p className="whitespace-pre-wrap">{msg.content}</p>
              
              {/* Rich Content Rendering */}
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
      );
  };

  return (
    <div className="h-full flex gap-6">
      {/* Chat Area */}
      <div className="flex-1 bg-surface rounded-xl border border-zinc-800/50 flex flex-col overflow-hidden shadow-xl">
        <div className="p-4 border-b border-zinc-800/50 bg-surface_highlight/50 flex items-center justify-between">
          <div className="flex items-center gap-3">
             <div className="p-2 bg-primary/10 rounded-md">
                <Sparkles className="text-primary w-4 h-4" />
             </div>
             <div>
                <h2 className="font-bold text-sm text-white">Swarm Intelligence AI</h2>
                <div className="flex items-center gap-1.5">
                   <span className="w-1.5 h-1.5 rounded-full bg-success"></span>
                   <span className="text-[10px] text-zinc-400 font-medium">Online & Ready</span>
                </div>
             </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6" ref={scrollRef}>
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={cn(
                "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm",
                msg.role === 'user' ? 'bg-white text-black' : 
                msg.role === 'system' ? 'bg-danger/10 text-danger' : 
                'bg-primary/10 text-primary'
              )}>
                {msg.role === 'user' ? <User size={14} /> : msg.role === 'system' ? <Terminal size={14} /> : <Bot size={14} />}
              </div>
              
              <div className={cn(
                "max-w-[85%] md:max-w-[70%] p-4 rounded-xl text-sm leading-relaxed shadow-md transition-all",
                msg.role === 'user' 
                  ? 'bg-zinc-800 text-white rounded-tr-none' 
                  : msg.role === 'system'
                  ? 'bg-danger/5 border border-danger/20 text-danger font-mono text-xs'
                  : 'bg-zinc-900 border border-zinc-800 text-zinc-200 rounded-tl-none'
              )}>
                {renderMessageContent(msg)}
                <span className="text-[9px] text-zinc-500 mt-2 block font-medium opacity-60">
                   {new Date(msg.timestamp).toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))}
          
          {isTyping && (
             <div className="flex gap-4">
                <div className="w-8 h-8 bg-primary/10 text-primary rounded-lg flex items-center justify-center">
                  <Bot size={14} />
                </div>
                <div className="bg-zinc-900 border border-zinc-800 p-4 rounded-xl rounded-tl-none flex items-center gap-1.5">
                   <div className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                   <div className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                   <div className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                </div>
             </div>
          )}
        </div>

        <div className="p-4 bg-surface_highlight/30 border-t border-zinc-800/50">
          <div className="flex gap-2 relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Input natural language command..."
              className="flex-1 bg-black/50 border border-zinc-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary font-medium text-sm placeholder:text-zinc-600 transition-all"
            />
            <button 
              onClick={handleSend}
              disabled={!input.trim() || isTyping}
              className="bg-white text-black px-6 rounded-lg hover:bg-zinc-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed font-bold"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* Suggested Commands Panel */}
      <div className="w-72 flex flex-col gap-4">
        <div className="bg-surface rounded-xl border border-zinc-800/50 p-5 shadow-lg">
           <div className="flex items-center gap-2 mb-4">
              <Code2 size={16} className="text-zinc-400" />
              <h3 className="font-bold text-sm text-white">Quick Actions</h3>
           </div>
           <div className="space-y-2">
             {[
               'Status Report', 
               'Scan Sector Alpha', 
               'Return Unit 1 to Base', 
               'Set Unit 2 Altitude to 100m', 
               'Generate Mission Plan'
             ].map(cmd => (
               <button 
                key={cmd}
                onClick={() => setInput(cmd)}
                className="w-full text-left px-3 py-2.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-600 rounded-lg text-xs font-medium text-zinc-300 transition-all truncate"
                title={cmd}
               >
                 {cmd}
               </button>
             ))}
           </div>
        </div>
        
        <div className="flex-1 bg-surface rounded-xl border border-zinc-800/50 p-5 flex flex-col shadow-lg min-h-0">
          <div className="flex items-center gap-2 mb-4">
             <Terminal size={16} className="text-zinc-400" />
             <h3 className="font-bold text-sm text-white">System Logs</h3>
          </div>
          <div className="flex-1 overflow-y-auto font-mono text-[10px] space-y-3 custom-scrollbar">
             <div className="flex gap-2 text-zinc-500">
               <span className="opacity-50 min-w-[50px]">10:42:01</span> 
               <span className="text-zinc-400">System Initialized</span>
             </div>
             <div className="flex gap-2 text-zinc-500">
               <span className="opacity-50 min-w-[50px]">10:42:05</span> 
               <span className="text-success font-bold">Agent Connection Established</span>
             </div>
             <div className="flex gap-2 text-zinc-500">
               <span className="opacity-50 min-w-[50px]">10:42:12</span> 
               <span className="text-zinc-400">Telemetry Stream Active</span>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
};
