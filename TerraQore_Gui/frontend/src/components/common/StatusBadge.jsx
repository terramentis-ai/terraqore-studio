import React from 'react';
import { Activity, CheckCircle, FolderOpen, AlertCircle } from 'lucide-react';

const StatusBadge = ({ status, blocked }) => {
  if (blocked) {
    return (
      <span className="px-2 py-1 text-xs rounded border border-white/20 bg-white/5 flex items-center gap-1">
        <AlertCircle className="w-3 h-3 text-white" />
        BLOCKED
      </span>
    );
  }
  
  const configs = {
    in_progress: { icon: Activity, label: 'IN PROGRESS', color: 'text-white' },
    completed: { icon: CheckCircle, label: 'COMPLETED', color: 'text-white' },
    draft: { icon: FolderOpen, label: 'DRAFT', color: 'text-white/60' },
  };
  
  const config = configs[status] || configs.draft;
  const Icon = config.icon;
  
  return (
    <span className={`px-2 py-1 text-xs rounded border border-white/20 bg-white/5 flex items-center gap-1 ${config.color}`}>
      <Icon className="w-3 h-3" />
      {config.label}
    </span>
  );
};

export default StatusBadge;