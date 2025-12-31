import React from 'react';
import { AlertCircle, Play, Code, MoreVertical } from 'lucide-react';
import StatusBadge from './StatusBadge';

const ProjectCard = ({ project }) => {
  return (
    <div className="border border-white/10 bg-white/5 rounded p-4 hover:bg-white/10 transition cursor-pointer group">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="text-lg font-medium mb-1">{project.name}</div>
          <div className="text-white/60 text-sm">
            {project.agents} agents • {project.iterations} iterations • Last run {project.lastRun}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={project.status} blocked={project.blocked} />
          <button className="p-1 hover:bg-white/10 rounded opacity-0 group-hover:opacity-100 transition">
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {project.blocked && (
        <div className="text-xs text-white/60 bg-white/5 border border-white/10 rounded p-2 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>PSMP Conflict: Dependency mismatch detected in artifact declarations. Review required.</span>
        </div>
      )}
      
      <div className="flex gap-2 mt-3">
        <button className="flex-1 border border-white/20 bg-white/5 py-2 rounded text-sm font-medium hover:bg-white/10 transition flex items-center justify-center gap-2">
          <Play className="w-4 h-4" />
          EXECUTE
        </button>
        <button className="flex-1 border border-white/20 bg-white/5 py-2 rounded text-sm font-medium hover:bg-white/10 transition flex items-center justify-center gap-2">
          <Code className="w-4 h-4" />
          WORKFLOW
        </button>
      </div>
    </div>
  );
};

export default ProjectCard;