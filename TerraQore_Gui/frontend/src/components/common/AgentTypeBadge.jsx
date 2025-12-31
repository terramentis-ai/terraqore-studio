import React from 'react';
import { Sparkles, GitBranch, CheckCircle, Shield, Zap } from 'lucide-react';

const AgentTypeBadge = ({ type }) => {
  const configs = {
    generation: { icon: Sparkles, label: 'GENERATION' },
    planning: { icon: GitBranch, label: 'PLANNING' },
    validation: { icon: CheckCircle, label: 'VALIDATION' },
    security: { icon: Shield, label: 'SECURITY' },
    psmp: { icon: Zap, label: 'PSMP' },
  };
  
  const config = configs[type] || configs.generation;
  const Icon = config.icon;
  
  return (
    <span className="px-2 py-1 text-xs rounded border border-white/20 bg-white/5 flex items-center gap-1">
      <Icon className="w-3 h-3" />
      {config.label}
    </span>
  );
};

export default AgentTypeBadge;