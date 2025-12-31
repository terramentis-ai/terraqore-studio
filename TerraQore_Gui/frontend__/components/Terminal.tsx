
import React, { useEffect, useRef, useState } from 'react';
import { ExecutionLog } from '../types';

interface TerminalProps {
  logs: ExecutionLog[];
}

const Terminal: React.FC<TerminalProps> = ({ logs }) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const handleCopyAll = () => {
    if (logs.length > 0) {
      const formattedLogs = logs.map(log => {
        const time = new Date(log.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        return `[${time}] [${log.agentName}] ${log.message}`;
      }).join('\n');
      
      navigator.clipboard.writeText(formattedLogs);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="flex flex-col h-full bg-black/40 border-t border-zinc-800 mono text-[11px]">
      <div className="flex items-center justify-between px-4 py-2 bg-zinc-900/50 border-b border-zinc-800">
        <span className="text-zinc-400 font-medium tracking-widest">SYSTEM LOGS</span>
        <div className="flex items-center gap-3">
          <button 
            onClick={handleCopyAll}
            className="text-[9px] font-black uppercase text-zinc-500 hover:text-white transition-colors"
          >
            {copied ? 'COPIED!' : 'COPY ALL LOGS'}
          </button>
          <div className="flex gap-1.5">
            <div className="w-2 h-2 rounded-full bg-zinc-700"></div>
            <div className="w-2 h-2 rounded-full bg-zinc-700"></div>
            <div className="w-2 h-2 rounded-full bg-zinc-700"></div>
          </div>
        </div>
      </div>
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-1"
      >
        {logs.map((log) => (
          <div key={log.id} className="flex gap-3 leading-relaxed">
            <span className="text-zinc-600 shrink-0">
              {new Date(log.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
            <span className={`shrink-0 font-bold ${
              log.type === 'error' ? 'text-red-400' : 
              log.type === 'warning' ? 'text-amber-400' : 
              log.type === 'success' ? 'text-emerald-400' : 'text-blue-400'
            }`}>
              [{log.agentName}]
            </span>
            <span className="text-zinc-300">{log.message}</span>
          </div>
        ))}
        {logs.length === 0 && (
          <div className="text-zinc-600 italic">Waiting for system initialization...</div>
        )}
      </div>
    </div>
  );
};

export default Terminal;
