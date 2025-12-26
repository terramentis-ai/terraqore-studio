import React, { useState, useEffect } from 'react';
import { Project, Task } from '../services/flyntAPIService';
import flyntAPI from '../services/flyntAPIService';

interface ProjectDetailProps {
  project: Project;
  onBack: () => void;
  onExecuteWorkflow: (projectId: number, workflowType: string) => void;
}

const ProjectDetail: React.FC<ProjectDetailProps> = ({ project, onBack, onExecuteWorkflow }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [conflicts, setConflicts] = useState<any>(null);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'tasks' | 'conflicts'>('overview');
  const [showNewTaskForm, setShowNewTaskForm] = useState(false);
  const [newTask, setNewTask] = useState({ title: '', priority: 'medium', milestone: '' });

  useEffect(() => {
    fetchProjectDetails();
  }, [project.id]);

  const fetchProjectDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      const [tasksData, conflictsData] = await Promise.all([
        flyntAPI.getProjectTasks(project.id),
        flyntAPI.getProjectConflicts(project.id),
      ]);
      setTasks(tasksData.tasks);
      setConflicts(conflictsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load project details');
      console.error('Error fetching project details:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTask.title.trim()) return;

    try {
      const createdTask = await flyntAPI.createTask(
        project.id,
        newTask.title,
        '',
        newTask.milestone || undefined,
        newTask.priority
      );
      setTasks([...tasks, createdTask]);
      setNewTask({ title: '', priority: 'medium', milestone: '' });
      setShowNewTaskForm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create task');
    }
  };

  const handleResolveConflict = async (library: string, version: string) => {
    try {
      const result = await flyntAPI.resolveConflict(project.id, library, version);
      if (result.success) {
        // Refresh conflicts
        const updatedConflicts = await flyntAPI.getProjectConflicts(project.id);
        setConflicts(updatedConflicts);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resolve conflict');
    }
  };

  const getPriorityColor = (priority: string): string => {
    switch (priority) {
      case 'critical': return 'text-red-400';
      case 'high': return 'text-orange-400';
      case 'medium': return 'text-yellow-400';
      case 'low': return 'text-blue-400';
      default: return 'text-zinc-400';
    }
  };

  const getTaskStatusColor = (status: string): string => {
    switch (status) {
      case 'completed': return 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300';
      case 'in_progress': return 'bg-blue-500/20 border-blue-500/50 text-blue-300';
      case 'blocked': return 'bg-red-500/20 border-red-500/50 text-red-300';
      default: return 'bg-zinc-800/50 border-zinc-700/50 text-zinc-300';
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <button
            onClick={onBack}
            className="text-blue-400 hover:text-blue-300 mb-4 flex items-center gap-2"
          >
            ← Back to Projects
          </button>
          <h1 className="text-4xl font-bold text-zinc-100">{project.name}</h1>
          {project.description && (
            <p className="text-zinc-400 mt-2">{project.description}</p>
          )}
        </div>
        <div className="text-right">
          <div className={`text-2xl mb-2 ${project.completion_percentage >= 100 ? 'text-emerald-400' : 'text-blue-400'}`}>
            {Math.round(project.completion_percentage)}%
          </div>
          <div className="text-sm text-zinc-400">{project.task_count} tasks</div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mb-8 flex gap-4">
        <button
          onClick={() => onExecuteWorkflow(project.id, 'ideate')}
          className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg transition-colors"
        >
          💡 Ideate
        </button>
        <button
          onClick={() => onExecuteWorkflow(project.id, 'plan')}
          className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
        >
          📋 Plan
        </button>
        <button
          onClick={() => onExecuteWorkflow(project.id, 'execute')}
          className="px-6 py-2 bg-orange-600 hover:bg-orange-700 text-white font-medium rounded-lg transition-colors"
        >
          ⚙️ Execute
        </button>
        <button
          onClick={() => onExecuteWorkflow(project.id, 'review')}
          className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
        >
          ✓ Review
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-8 p-4 bg-red-500/20 border border-red-500/50 text-red-300 rounded-lg">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-4 border-b border-zinc-700/50 mb-8">
        {(['overview', 'tasks', 'conflicts'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setSelectedTab(tab)}
            className={`px-4 py-2 font-medium border-b-2 transition-colors capitalize ${
              selectedTab === tab
                ? 'text-blue-400 border-blue-400'
                : 'text-zinc-400 border-transparent hover:text-zinc-300'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin text-2xl">⟳</div>
          <span className="ml-4 text-zinc-400">Loading project details...</span>
        </div>
      ) : (
        <>
          {/* Overview Tab */}
          {selectedTab === 'overview' && (
            <div className="grid grid-cols-3 gap-6">
              <div className="p-6 bg-zinc-800/50 border border-zinc-700/50 rounded-lg">
                <div className="text-sm text-zinc-400 mb-2">Total Tasks</div>
                <div className="text-3xl font-bold text-zinc-100">{project.task_count}</div>
              </div>
              <div className="p-6 bg-zinc-800/50 border border-zinc-700/50 rounded-lg">
                <div className="text-sm text-zinc-400 mb-2">Completion</div>
                <div className="text-3xl font-bold text-emerald-400">{Math.round(project.completion_percentage)}%</div>
              </div>
              <div className="p-6 bg-zinc-800/50 border border-zinc-700/50 rounded-lg">
                <div className="text-sm text-zinc-400 mb-2">Status</div>
                <div className="text-lg font-bold text-blue-400 capitalize">{project.status.replace('_', ' ')}</div>
              </div>
            </div>
          )}

          {/* Tasks Tab */}
          {selectedTab === 'tasks' && (
            <div>
              {!showNewTaskForm && (
                <button
                  onClick={() => setShowNewTaskForm(true)}
                  className="mb-6 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
                >
                  + New Task
                </button>
              )}

              {showNewTaskForm && (
                <div className="mb-6 p-6 bg-zinc-800/50 border border-zinc-700/50 rounded-lg">
                  <form onSubmit={handleCreateTask}>
                    <div className="grid grid-cols-4 gap-4 mb-4">
                      <input
                        type="text"
                        value={newTask.title}
                        onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                        placeholder="Task title..."
                        className="col-span-2 px-4 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-blue-500/50"
                      />
                      <select
                        value={newTask.priority}
                        onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
                        className="px-4 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:border-blue-500/50"
                      >
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                        <option value="critical">Critical</option>
                      </select>
                      <input
                        type="text"
                        value={newTask.milestone}
                        onChange={(e) => setNewTask({ ...newTask, milestone: e.target.value })}
                        placeholder="Milestone..."
                        className="px-4 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-blue-500/50"
                      />
                    </div>
                    <div className="flex gap-2">
                      <button
                        type="submit"
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg transition-colors"
                      >
                        Create
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowNewTaskForm(false)}
                        className="px-4 py-2 bg-zinc-700 hover:bg-zinc-600 text-white font-medium rounded-lg transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              )}

              <div className="space-y-4">
                {tasks.length === 0 ? (
                  <div className="text-center py-12 text-zinc-400">
                    No tasks yet. Create one to get started.
                  </div>
                ) : (
                  tasks.map(task => (
                    <div key={task.id} className="p-4 bg-zinc-800/50 border border-zinc-700/50 rounded-lg hover:border-blue-500/30 transition-colors">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-semibold text-zinc-100 mb-1">{task.title}</h4>
                          <div className="flex gap-4 text-sm text-zinc-400">
                            <span className={`font-medium ${getPriorityColor(task.priority)}`}>
                              {task.priority.toUpperCase()}
                            </span>
                            {task.milestone && <span>🎯 {task.milestone}</span>}
                            <span>⏱️ {task.estimated_hours || 0}h</span>
                          </div>
                        </div>
                        <div className={`px-3 py-1 rounded-full text-sm font-medium border ${getTaskStatusColor(task.status)}`}>
                          {task.status.replace('_', ' ')}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Conflicts Tab */}
          {selectedTab === 'conflicts' && (
            <div>
              {conflicts?.blocking_blocks && conflicts.blocking_blocks.length > 0 ? (
                <div className="space-y-4">
                  {conflicts.blocking_blocks.map((block: any, idx: number) => (
                    <div key={idx} className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-semibold text-red-300 mb-1">{block.library_name}</h4>
                          <div className="text-sm text-red-400">
                            Required: {block.required_range} → Available: {block.current_version}
                          </div>
                        </div>
                        <span className="text-red-400 font-medium">BLOCKING</span>
                      </div>
                      <button
                        onClick={() => handleResolveConflict(block.library_name, block.suggested_version)}
                        className="px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-300 font-medium rounded-lg transition-colors"
                      >
                        Suggest Resolution
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-zinc-400">
                  ✓ No dependency conflicts detected
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default ProjectDetail;
