
import React, { useState } from 'react';

interface ControlPanelProps {
  onExecute: (prompt: string) => void;
  isProcessing: boolean;
}

const ControlPanel: React.FC<ControlPanelProps> = ({ onExecute, isProcessing }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isProcessing) {
      onExecute(input);
      setInput('');
    }
  };

  return (
    <div className="p-6 bg-[#080808] flex flex-col gap-8 flex-1">
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="w-1 h-4 bg-purple-500 rounded-full"></div>
          <h2 className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.3em]">Command Center</h2>
        </div>
        
        <form onSubmit={handleSubmit} className="relative group">
          <div className="relative material-card rounded-2xl overflow-hidden focus-within:border-purple-500/50 transition-all duration-500">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Define mission objective..."
              className="w-full h-40 bg-white/[0.02] p-5 text-sm text-zinc-200 focus:outline-none resize-none placeholder:text-zinc-600 font-medium leading-relaxed"
              disabled={isProcessing}
            />
            <div className="absolute bottom-4 right-4 flex items-center gap-3">
               <span className="text-[9px] text-zinc-600 mono uppercase">{input.length} chars</span>
            </div>
          </div>
          
          <button
            type="submit"
            disabled={isProcessing || !input.trim()}
            className={`mt-4 w-full py-4 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] transition-all duration-500 flex items-center justify-center gap-3 relative overflow-hidden group/btn ${
              isProcessing 
                ? 'bg-zinc-900 text-zinc-600 cursor-not-allowed border border-white/5' 
                : 'bg-white text-black hover:bg-zinc-200 shadow-[0_10px_20px_rgba(0,0,0,0.3)] hover:shadow-white/5'
            }`}
          >
            {isProcessing ? (
              <>
                <div className="w-3 h-3 border-2 border-zinc-700 border-t-zinc-400 rounded-full animate-spin"></div>
                Orchestrating Workflow
              </>
            ) : (
              <>
                Initialize Deployment
                <svg className="w-3 h-3 transition-transform group-hover/btn:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </>
            )}
            <div className="absolute inset-0 bg-gradient-to-r from-purple-500/0 via-purple-500/10 to-purple-500/0 -translate-x-full group-hover/btn:translate-x-full transition-transform duration-1000"></div>
          </button>
        </form>
      </div>

      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="w-1 h-4 bg-zinc-700 rounded-full"></div>
          <h2 className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.3em]">Protocol Configuration</h2>
        </div>
        <div className="grid grid-cols-1 gap-2">
          {[
            { label: 'Compute Engine', value: 'Gemini 3 Pro' },
            { label: 'Agent Density', value: 'Scalable' },
            { label: 'Security Level', value: 'Encrypted' },
          ].map((item, idx) => (
            <div key={idx} className="material-card flex items-center justify-between p-3 rounded-xl border border-white/5 hover:border-white/10 transition-colors">
              <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">{item.label}</span>
              <span className="text-[10px] text-zinc-300 mono font-bold">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
      
      <div className="mt-auto p-4 rounded-2xl bg-gradient-to-br from-purple-500/10 to-indigo-500/10 border border-purple-500/20">
         <div className="flex items-center gap-3 mb-2">
            <div className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></div>
            <span className="text-[9px] font-black text-purple-400 uppercase tracking-widest">Active System Status</span>
         </div>
         <p className="text-[10px] text-zinc-400 leading-relaxed font-medium">
           Framework operating at peak performance. All agent clusters synchronized.
         </p>
      </div>
    </div>
  );
};

export default ControlPanel;
