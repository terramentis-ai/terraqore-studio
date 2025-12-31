import React from 'react';
import { Activity, Cpu, Settings } from 'lucide-react';

const Sidebar = ({ activePanel, setActivePanel }) => {
  return (
    <div className="col-span-3 space-y-2">
      <button
        onClick={() => setActivePanel('dashboard')}
        className={`w-full text-left px-4 py-3 rounded transition flex items-center gap-3 ${
          activePanel === 'dashboard'
            ? 'bg-white text-black'
            : 'bg-white/5 hover:bg-white/10 border border-white/10'
        }`}
      >
        <Activity className="w-5 h-5" />
        <span className="font-medium">DASHBOARD</span>
      </button>
      
      <button
        onClick={() => setActivePanel('agents')}
        className={`w-full text-left px-4 py-3 rounded transition flex items-center gap-3 ${
          activePanel === 'agents'
            ? 'bg-white text-black'
            : 'bg-white/5 hover:bg-white/10 border border-white/10'
        }`}
      >
        <Cpu className="w-5 h-5" />
        <span className="font-medium">AGENTS HUB</span>
      </button>
      
      <button
        onClick={() => setActivePanel('settings')}
        className={`w-full text-left px-4 py-3 rounded transition flex items-center gap-3 ${
          activePanel === 'settings'
            ? 'bg-white text-black'
            : 'bg-white/5 hover:bg-white/10 border border-white/10'
        }`}
      >
        <Settings className="w-5 h-5" />
        <span className="font-medium">SETTINGS</span>
      </button>

      <SystemStatus />
    </div>
  );
};

const SystemStatus = () => (
  <div className="mt-8 pt-8 border-t border-white/10 space-y-3">
    <div className="text-xs text-white/60 font-medium">SYSTEM STATUS</div>
    <div className="text-xs space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-white/60">Orchestrator</span>
        <span className="text-green-400">ONLINE</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-white/60">LLM Client</span>
        <span className="text-green-400">CONNECTED</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-white/60">State Manager</span>
        <span className="text-green-400">ACTIVE</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-white/60">PSMP Bridge</span>
        <span className="text-green-400">MONITORING</span>
      </div>
    </div>
  </div>
);

export default Sidebar;