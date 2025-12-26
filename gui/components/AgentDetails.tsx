
import React, { useState } from 'react';
import { AgentNode, AgentStatus } from '../types';
import { COLORS } from '../constants';

interface AgentDetailsProps {
  node: AgentNode | null;
  onClose: () => void;
}

const AgentDetails: React.FC<AgentDetailsProps> = ({ node, onClose }) => {
  const [copied, setCopied] = useState(false);

  if (!node) return null;

  const color = (COLORS as any)[node.type.split(' ')[0].toUpperCase()] || '#52525b';

  const handleCopy = () => {
    if (node.output) {
      navigator.clipboard.writeText(node.output);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="absolute right-0 top-0 bottom-0 w-80 bg-zinc-950/80 backdrop-blur-xl border-l border-zinc-800 z-30 flex flex-col shadow-2xl animate-in slide-in-from-right duration-300">
      <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div 
            className="w-2 h-2 rounded-full" 
            style={{ backgroundColor: color, boxShadow: `0 0 8px ${color}` }}
          ></div>
          <span className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Agent Insight</span>
        </div>
        <button 
          onClick={onClose}
          className="text-zinc-500 hover:text-zinc-200 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        <div>
          <h2 className="text-xl font-semibold text-white mb-1">{node.label}</h2>
          <p className="text-xs text-zinc-500 mono">{node.id}</p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 bg-zinc-900/50 rounded-lg border border-zinc-800">
            <p className="text-[10px] text-zinc-500 uppercase mb-1">Status</p>
            <p className={`text-xs font-bold ${
              node.status === AgentStatus.COMPLETED ? 'text-emerald-400' :
              node.status === AgentStatus.THINKING ? 'text-purple-400 animate-pulse' : 'text-zinc-300'
            }`}>
              {node.status.toUpperCase()}
            </p>
          </div>
          <div className="p-3 bg-zinc-900/50 rounded-lg border border-zinc-800">
            <p className="text-[10px] text-zinc-500 uppercase mb-1">Role</p>
            <p className="text-xs font-bold text-zinc-300">{node.type}</p>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Output & Context</h3>
            {node.output && (
              <button 
                onClick={handleCopy}
                className="text-[9px] font-black uppercase text-zinc-500 hover:text-white transition-colors flex items-center gap-1.5"
              >
                {copied ? 'Copied!' : (
                  <>
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    Copy Output
                  </>
                )}
              </button>
            )}
          </div>
          <div className="h-64 bg-zinc-900/80 rounded-lg border border-zinc-800 relative overflow-hidden group">
             {node.output ? (
               <div className="w-full h-full p-4 overflow-auto custom-scrollbar select-text">
                 <pre className="text-[11px] text-zinc-300 leading-relaxed font-mono whitespace-pre-wrap break-words">
                   {node.output}
                 </pre>
               </div>
             ) : (
               <div className="absolute inset-0 flex items-center justify-center">
                 <p className="text-xs text-zinc-600 italic">No output data available yet</p>
               </div>
             )}
             {node.status === AgentStatus.THINKING && (
               <div className="absolute bottom-0 left-0 h-1 bg-purple-500/50 animate-[loading_2s_infinite]"></div>
             )}
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Performance Metrics</h3>
          <div className="space-y-2">
            {[
              { label: 'Latency', value: '1.2s' },
              { label: 'Token Usage', value: '420' },
              { label: 'Confidence', value: '98%' },
            ].map((m, i) => (
              <div key={i} className="flex items-center justify-between text-[11px]">
                <span className="text-zinc-500">{m.label}</span>
                <div className="flex items-center gap-2">
                   <div className="w-24 h-1 bg-zinc-800 rounded-full overflow-hidden">
                     <div className="h-full bg-zinc-600" style={{ width: '70%' }}></div>
                   </div>
                   <span className="text-zinc-300 mono">{m.value}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-zinc-800 bg-zinc-900/20">
        <button className="w-full py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-[10px] font-bold uppercase rounded transition-colors tracking-widest">
          Debug Stack Trace
        </button>
      </div>

      <style>{`
        @keyframes loading {
          0% { width: 0%; left: 0%; }
          50% { width: 100%; left: 0%; }
          100% { width: 0%; left: 100%; }
        }
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #3f3f46;
          border-radius: 10px;
        }
      `}</style>
    </div>
  );
};

export default AgentDetails;
