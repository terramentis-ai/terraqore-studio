import React, { useState, useEffect } from 'react';
import { Project } from '../services/flyntAPIService';
import flyntAPI from '../services/flyntAPIService';
import { COLORS } from '../constants';

interface ProjectDashboardProps {
  onSelectProject: (project: Project) => void;
  onCreateProject: () => void;
}

const ProjectDashboard: React.FC<ProjectDashboardProps> = ({ onSelectProject, onCreateProject }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'active' | 'completed'>('all');
  const [newProjectName, setNewProjectName] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await flyntAPI.getProjects();
      setProjects(result.projects);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects');
      console.error('Error fetching projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;

    try {
      setCreating(true);
      const newProject = await flyntAPI.createProject(newProjectName);
      setProjects([...projects, newProject]);
      setNewProjectName('');
      setShowCreateForm(false);
      onCreateProject();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project');
      console.error('Error creating project:', err);
    } finally {
      setCreating(false);
    }
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300';
      case 'in_progress':
        return 'bg-blue-500/20 border-blue-500/50 text-blue-300';
      case 'blocked':
        return 'bg-red-500/20 border-red-500/50 text-red-300';
      case 'planning':
        return 'bg-amber-500/20 border-amber-500/50 text-amber-300';
      default:
        return 'bg-zinc-800/50 border-zinc-700/50 text-zinc-300';
    }
  };

  const getStatusIcon = (status: string): string => {
    switch (status) {
      case 'completed':
        return '✓';
      case 'in_progress':
        return '⟳';
      case 'blocked':
        return '⊘';
      case 'planning':
        return '◐';
      default:
        return '◯';
    }
  };

  const filteredProjects = projects.filter(p => {
    if (filter === 'active') return p.status !== 'completed' && p.status !== 'archived';
    if (filter === 'completed') return p.status === 'completed';
    return true;
  });

  return (
    <div className="w-full max-w-7xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-zinc-100 mb-2">Projects</h1>
        <p className="text-zinc-400">Design, execute, and monitor your AI agent workflows</p>
      </div>

      {/* Create Project Form */}
      {showCreateForm && (
        <div className="mb-8 p-6 bg-zinc-800/50 border border-zinc-700/50 rounded-lg">
          <form onSubmit={handleCreateProject}>
            <div className="flex gap-4 items-end">
              <div className="flex-1">
                <label className="block text-sm font-medium text-zinc-300 mb-2">
                  Project Name
                </label>
                <input
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="Enter project name..."
                  className="w-full px-4 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-blue-500/50 transition-colors"
                  disabled={creating}
                />
              </div>
              <button
                type="submit"
                disabled={creating || !newProjectName.trim()}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-700 text-white font-medium rounded-lg transition-colors"
              >
                {creating ? 'Creating...' : 'Create'}
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-6 py-2 bg-zinc-700 hover:bg-zinc-600 text-white font-medium rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {!showCreateForm && (
        <div className="mb-8 flex gap-4 items-center">
          <button
            onClick={() => setShowCreateForm(true)}
            className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg transition-colors"
          >
            + New Project
          </button>

          <div className="flex gap-2 ml-auto">
            {(['all', 'active', 'completed'] as const).map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors capitalize ${
                  filter === f
                    ? 'bg-blue-600 text-white'
                    : 'bg-zinc-800/50 text-zinc-300 hover:bg-zinc-700/50'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mb-8 p-4 bg-red-500/20 border border-red-500/50 text-red-300 rounded-lg">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin text-2xl">⟳</div>
          <span className="ml-4 text-zinc-400">Loading projects...</span>
        </div>
      )}

      {/* Projects Grid */}
      {!loading && (
        <div>
          {filteredProjects.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-zinc-500 mb-4">No projects found</p>
              {filter !== 'all' && (
                <button
                  onClick={() => setFilter('all')}
                  className="text-blue-400 hover:text-blue-300 underline"
                >
                  View all projects
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredProjects.map(project => (
                <div
                  key={project.id}
                  onClick={() => onSelectProject(project)}
                  className="p-6 bg-zinc-800/50 border border-zinc-700/50 hover:border-blue-500/50 rounded-lg cursor-pointer transition-all hover:shadow-lg hover:shadow-blue-500/10"
                >
                  <div className="flex items-start justify-between mb-4">
                    <h3 className="text-xl font-semibold text-zinc-100 flex-1">{project.name}</h3>
                    <div className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(project.status)} ml-2 whitespace-nowrap`}>
                      {getStatusIcon(project.status)} {project.status.replace('_', ' ')}
                    </div>
                  </div>

                  {project.description && (
                    <p className="text-zinc-400 text-sm mb-4 line-clamp-2">{project.description}</p>
                  )}

                  <div className="space-y-3">
                    {/* Progress Bar */}
                    <div>
                      <div className="flex justify-between text-xs text-zinc-400 mb-1">
                        <span>Progress</span>
                        <span>{Math.round(project.completion_percentage)}%</span>
                      </div>
                      <div className="h-2 bg-zinc-900 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-blue-600 to-emerald-600 transition-all"
                          style={{ width: `${project.completion_percentage}%` }}
                        />
                      </div>
                    </div>

                    {/* Stats */}
                    <div className="flex gap-4 text-sm text-zinc-400">
                      <span>📋 {project.task_count} tasks</span>
                      <span>📅 {new Date(project.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t border-zinc-700/50">
                    <button
                      onClick={() => onSelectProject(project)}
                      className="w-full py-2 text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors"
                    >
                      View Details →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ProjectDashboard;
