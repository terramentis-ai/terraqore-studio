import React, { useState, useEffect } from 'react';
import { Project } from '../services/terraqoreAPIService';
import terraqoreAPI from '../services/terraqoreAPIService';

interface Achievement {
  icon: string;
  badge_name: string;
  description: string;
  points: number;
  achieved_at: string;
  type: string;
}

interface ProjectGalleryItem {
  project: Project;
  achievements: Achievement[];
  totalPoints: number;
  artifact_count: number;
  quality_score: number;
}

const ProjectGallery: React.FC = () => {
  const [projects, setProjects] = useState<ProjectGalleryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<'completion' | 'points' | 'recent'>('completion');
  const [selectedProject, setSelectedProject] = useState<ProjectGalleryItem | null>(null);

  useEffect(() => {
    fetchProjectsGallery();
  }, []);

  const fetchProjectsGallery = async () => {
    try {
      setLoading(true);
      const result = await terraqoreAPI.getProjects();
      
      // Transform projects into gallery items with mock achievement data
      const galleryItems: ProjectGalleryItem[] = result.projects.map(project => ({
        project,
        achievements: generateAchievements(project),
        totalPoints: calculatePoints(project),
        artifact_count: Math.floor(Math.random() * 20) + 5,
        quality_score: Math.random() * 2 + 7 // 7-9 range
      }));
      
      setProjects(galleryItems);
    } catch (err) {
      console.error('Error fetching projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const generateAchievements = (project: Project): Achievement[] => {
    const achievements: Achievement[] = [];
    
    // Project Created
    achievements.push({
      icon: '🎯',
      badge_name: 'Project Founder',
      description: 'Created your first TERRAQORE Project',
      points: 10,
      achieved_at: new Date(project.created_at).toISOString(),
      type: 'project_created'
    });
    
    // Based on completion
    if (project.completion_percentage >= 50) {
      achievements.push({
        icon: '⚡',
        badge_name: 'Workflow Guru',
        description: 'Executed all 4 workflow types',
        points: 40,
        achieved_at: new Date(Date.now() - Math.random() * 86400000).toISOString(),
        type: 'all_workflows'
      });
    }
    
    if (project.completion_percentage === 100) {
      achievements.push({
        icon: '🏆',
        badge_name: 'Completion Master',
        description: 'Completed a project (100% of tasks)',
        points: 50,
        achieved_at: new Date(Date.now() - Math.random() * 43200000).toISOString(),
        type: 'project_completed'
      });
    }
    
    // Quality-based
    achievements.push({
      icon: '💎',
      badge_name: 'Quality Enthusiast',
      description: 'Achieved code quality score > 8.0',
      points: 35,
      achieved_at: new Date(Date.now() - Math.random() * 172800000).toISOString(),
      type: 'high_quality'
    });
    
    return achievements.slice(0, 3); // Show top 3
  };

  const calculatePoints = (project: Project): number => {
    let points = 10; // Base points
    points += Math.floor(project.completion_percentage / 10) * 5; // Up to 50 points
    points += project.task_count * 2; // 2 points per task
    return points;
  };

  const sortProjects = (items: ProjectGalleryItem[]) => {
    const sorted = [...items];
    
    if (sortBy === 'completion') {
      sorted.sort((a, b) => b.project.completion_percentage - a.project.completion_percentage);
    } else if (sortBy === 'points') {
      sorted.sort((a, b) => b.totalPoints - a.totalPoints);
    } else if (sortBy === 'recent') {
      sorted.sort((a, b) => new Date(b.project.created_at).getTime() - new Date(a.project.created_at).getTime());
    }
    
    return sorted;
  };

  const handleExport = async (project: ProjectGalleryItem) => {
    try {
      // Mock export functionality
      const exportData = {
        project: project.project,
        achievements: project.achievements,
        totalPoints: project.totalPoints,
        exportedAt: new Date().toISOString(),
        format: 'json'
      };
      
      const dataStr = JSON.stringify(exportData, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${project.project.name.replace(/\s+/g, '_')}_export.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const sortedProjects = sortProjects(projects);

  return (
    <div className="w-full max-w-7xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-zinc-100 mb-2">📚 Project Gallery</h1>
        <p className="text-zinc-400">Showcase your AI-powered projects and achievements</p>
      </div>

      {/* Sort Controls */}
      <div className="mb-8 flex gap-4">
        {(['completion', 'points', 'recent'] as const).map(option => (
          <button
            key={option}
            onClick={() => setSortBy(option)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors capitalize ${
              sortBy === option
                ? 'bg-blue-600 text-white'
                : 'bg-zinc-800/50 text-zinc-300 hover:bg-zinc-700/50'
            }`}
          >
            {option === 'completion' ? 'By Completion' : option === 'points' ? 'By Points' : 'By Recent'}
          </button>
        ))}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin text-2xl">⟳</div>
          <span className="ml-4 text-zinc-400">Loading projects...</span>
        </div>
      )}

      {/* Projects Gallery */}
      {!loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedProjects.length === 0 ? (
            <div className="col-span-full text-center py-12 text-zinc-500">
              No projects yet. Create your first project to get started!
            </div>
          ) : (
            sortedProjects.map(item => (
              <div
                key={item.project.id}
                className="bg-gradient-to-br from-zinc-800/50 to-zinc-900/50 border border-zinc-700/50 hover:border-blue-500/50 rounded-lg overflow-hidden transition-all hover:shadow-lg hover:shadow-blue-500/10"
              >
                {/* Header with Status */}
                <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border-b border-zinc-700/50 p-4">
                  <h3 className="text-lg font-bold text-zinc-100 mb-2">{item.project.name}</h3>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-zinc-400">{item.project.task_count} tasks</span>
                    <span className="text-sm font-semibold text-emerald-400">
                      {item.project.completion_percentage}% Complete
                    </span>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="px-4 pt-4">
                  <div className="h-2 bg-zinc-900 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-600 to-emerald-600"
                      style={{ width: `${item.project.completion_percentage}%` }}
                    />
                  </div>
                </div>

                {/* Achievement Badges */}
                <div className="px-4 py-4">
                  <div className="text-xs font-semibold text-zinc-400 mb-3 uppercase tracking-wider">
                    Achievements
                  </div>
                  <div className="space-y-2">
                    {item.achievements.map((achievement, idx) => (
                      <div key={idx} className="flex items-start gap-3 p-2 bg-zinc-900/30 rounded">
                        <span className="text-lg flex-shrink-0">{achievement.icon}</span>
                        <div className="min-w-0">
                          <div className="text-sm font-semibold text-zinc-100">
                            {achievement.badge_name}
                          </div>
                          <div className="text-xs text-zinc-500">{achievement.points}pts</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Stats */}
                <div className="px-4 py-3 border-t border-zinc-700/50 bg-zinc-900/20">
                  <div className="grid grid-cols-3 gap-2 text-center text-xs">
                    <div>
                      <div className="text-lg font-bold text-blue-400">{item.totalPoints}</div>
                      <div className="text-zinc-500">Points</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-purple-400">{item.artifact_count}</div>
                      <div className="text-zinc-500">Artifacts</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-emerald-400">{item.quality_score.toFixed(1)}</div>
                      <div className="text-zinc-500">Quality</div>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="px-4 py-3 border-t border-zinc-700/50 flex gap-2">
                  <button
                    onClick={() => setSelectedProject(item)}
                    className="flex-1 py-2 text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors"
                  >
                    View Details
                  </button>
                  <button
                    onClick={() => handleExport(item)}
                    className="flex-1 py-2 text-sm font-medium text-purple-400 hover:text-purple-300 transition-colors"
                  >
                    Export
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Detail Modal */}
      {selectedProject && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-zinc-900 border border-zinc-700 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="sticky top-0 bg-zinc-900 border-b border-zinc-700 p-6 flex justify-between items-center">
              <h2 className="text-2xl font-bold text-zinc-100">{selectedProject.project.name}</h2>
              <button
                onClick={() => setSelectedProject(null)}
                className="text-zinc-400 hover:text-zinc-100 text-2xl"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Overview */}
              <div>
                <h3 className="text-lg font-semibold text-zinc-100 mb-3">Overview</h3>
                <p className="text-zinc-400 mb-4">{selectedProject.project.description || 'No description'}</p>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-zinc-500">Status</div>
                    <div className="text-lg font-semibold text-zinc-100 capitalize">
                      {selectedProject.project.status.replace('_', ' ')}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-zinc-500">Created</div>
                    <div className="text-lg font-semibold text-zinc-100">
                      {new Date(selectedProject.project.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              </div>

              {/* Achievements */}
              <div>
                <h3 className="text-lg font-semibold text-zinc-100 mb-3">🏆 Achievements</h3>
                <div className="space-y-2">
                  {selectedProject.achievements.map((achievement, idx) => (
                    <div key={idx} className="flex items-start gap-3 p-3 bg-zinc-800/50 rounded">
                      <span className="text-2xl">{achievement.icon}</span>
                      <div>
                        <div className="font-semibold text-zinc-100">{achievement.badge_name}</div>
                        <div className="text-sm text-zinc-400">{achievement.description}</div>
                        <div className="text-xs text-zinc-500 mt-1">+{achievement.points} points</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Statistics */}
              <div>
                <h3 className="text-lg font-semibold text-zinc-100 mb-3">📊 Statistics</h3>
                <div className="grid grid-cols-4 gap-3 text-center">
                  <div className="p-3 bg-zinc-800/50 rounded">
                    <div className="text-2xl font-bold text-blue-400">{selectedProject.totalPoints}</div>
                    <div className="text-xs text-zinc-400 mt-1">Points</div>
                  </div>
                  <div className="p-3 bg-zinc-800/50 rounded">
                    <div className="text-2xl font-bold text-purple-400">{selectedProject.artifact_count}</div>
                    <div className="text-xs text-zinc-400 mt-1">Artifacts</div>
                  </div>
                  <div className="p-3 bg-zinc-800/50 rounded">
                    <div className="text-2xl font-bold text-emerald-400">{selectedProject.quality_score.toFixed(1)}</div>
                    <div className="text-xs text-zinc-400 mt-1">Quality</div>
                  </div>
                  <div className="p-3 bg-zinc-800/50 rounded">
                    <div className="text-2xl font-bold text-orange-400">{selectedProject.project.completion_percentage}%</div>
                    <div className="text-xs text-zinc-400 mt-1">Complete</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer Actions */}
            <div className="bg-zinc-800/50 border-t border-zinc-700 p-4 flex gap-3">
              <button
                onClick={() => handleExport(selectedProject)}
                className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded transition-colors"
              >
                📥 Export Project
              </button>
              <button
                onClick={() => setSelectedProject(null)}
                className="flex-1 px-4 py-2 bg-zinc-700 hover:bg-zinc-600 text-white font-medium rounded transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectGallery;
