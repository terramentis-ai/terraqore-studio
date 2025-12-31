import React from 'react';
import { Plus, Search, Cpu } from 'lucide-react';
import AgentCard from '../common/AgentCard';
import { agents } from '../../data/mockData';

const AgentsHubPanel = () => {
  return (
    <div className="space-y-6">
      <div className="flex gap-3">
        <button className="flex-1 bg-white text-black py-3 px-4 rounded font-medium hover:bg-white/90 transition flex items-center justify-center gap-2">
          <Plus className="w-5 h-5" />
          CREATE AGENT
        </button>
        <button className="border border-white/20 bg-white/5 py-3 px-4 rounded font-medium hover:bg-white/10 transition flex items-center gap-2">
          <Search className="w-5 h-5" />
        </button>
      </div>

      <div className="space-y-3">
        <div className="text-white/60 text-sm font-medium">REGISTERED AGENTS</div>
        {agents.map(agent => (
          <AgentCard key={agent.name} agent={agent} />
        ))}
      </div>

      <div className="border border-white/20 bg-white/5 rounded p-6 mt-6">
        <div className="text-center text-white/60 mb-4">
          <Cpu className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <div className="text-sm">Create custom agents with specialized capabilities</div>
        </div>
        <button className="w-full border border-white/20 bg-white/5 py-2 rounded text-sm font-medium hover:bg-white/10 transition">
          AGENT BUILDER →
        </button>
      </div>
    </div>
  );
};

export default AgentsHubPanel;