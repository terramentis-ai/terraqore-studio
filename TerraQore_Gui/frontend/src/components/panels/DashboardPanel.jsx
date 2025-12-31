import React from 'react';
import { Plus, Search, Filter } from 'lucide-react';
import ProjectCard from '../common/ProjectCard';
import { projects, agents } from '../../data/mockData';

const DashboardPanel = () => {
  return (
    <div className="space-y-6">
      <StatsOverview projects={projects} agents={agents} />
      
      <div className="flex gap-3">
        <button className="flex-1 bg-white text-black py-3 px-4 rounded font-medium hover:bg-white/90 transition flex items-center justify-center gap-2">
          <Plus className="w-5 h-5" />
          NEW PROJECT
        </button>
        <button className="border border-white/20 bg-white/5 py-3 px-4 rounded font-medium hover:bg-white/10 transition flex items-center gap-2">
          <Search className="w-5 h-5" />
        </button>
        <button className="border border-white/20 bg-white/5 py-3 px-4 rounded font-medium hover:bg-white/10 transition flex items-center gap-2">
          <Filter className="w-5 h-5" />
        </button>
      </div>

      <div className="space-y-3">
        <div className="text-white/60 text-sm font-medium">PROJECTS</div>
        {projects.map(project => (
          <ProjectCard key={project.id} project={project} />
        ))}
      </div>
    </div>
  );
};

const StatsOverview = ({ projects, agents }) => (
  <div className="grid grid-cols-4 gap-4">
    <div className="border border-white/10 bg-white/5 rounded p-4">
      <div className="text-white/60 text-xs mb-1">ACTIVE PROJECTS</div>
      <div className="text-3xl font-bold">{projects.filter(p => p.status === 'in_progress').length}</div>
    </div>
    <div className="border border-white/10 bg-white/5 rounded p-4">
      <div className="text-white/60 text-xs mb-1">TOTAL AGENTS</div>
      <div className="text-3xl font-bold">{agents.length}</div>
    </div>
    <div className="border border-white/10 bg-white/5 rounded p-4">
      <div className="text-white/60 text-xs mb-1">AVG ITERATIONS</div>
      <div className="text-3xl font-bold">
        {(projects.reduce((acc, p) => acc + p.iterations, 0) / projects.length).toFixed(1)}
      </div>
    </div>
    <div className="border border-white/10 bg-white/5 rounded p-4">
      <div className="text-white/60 text-xs mb-1">BLOCKED</div>
      <div className="text-3xl font-bold text-white">
        {projects.filter(p => p.blocked).length}
      </div>
    </div>
  </div>
);

export default DashboardPanel;