import React from 'react';
import { MoreVertical } from 'lucide-react';
import AgentTypeBadge from './AgentTypeBadge';

const AgentCard = ({ agent }) => {
  return (
    <div className="border border-white/10 bg-white/5 rounded p-4 hover:bg-white/10 transition cursor-pointer group">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="text-lg font-medium mb-1">{agent.name}</div>
          <div className="text-white/60 text-sm mb-2">{agent.description}</div>
          <div className="text-white/60 text-xs">
            {agent.executions} executions • {agent.avgQuality.toFixed(1)}/10 avg quality
          </div>
        </div>
        <div className="flex items-center gap-2">
          <AgentTypeBadge type={agent.type} />
          <button className="p-1 hover:bg-white/10 rounded opacity-0 group-hover:opacity-100 transition">
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      <div className="mt-3">
        <div className="flex justify-between text-xs text-white/60 mb-1">
          <span>QUALITY SCORE</span>
          <span>{agent.avgQuality.toFixed(1)}/10</span>
        </div>
        <div className="h-1 bg-white/10 rounded overflow-hidden">
          <div 
            className="h-full bg-white"
            style={{ width: `${(agent.avgQuality / 10) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
};

export default AgentCard;