
import React, { useMemo } from 'react';
import { AgentNode, AgentStatus, ExecutionLog } from '../types';
import { COLORS } from '../constants';

interface DashboardProps {
  nodes: AgentNode[];
  logs: ExecutionLog[];
}

const Dashboard: React.FC<DashboardProps> = ({ nodes, logs }) => {
  // Calculate Job Progress
  const progressMetrics = useMemo(() => {
    const allNodes: AgentNode[] = [];
    const flatten = (items: AgentNode[]) => {
      items.forEach(node => {
        allNodes.push(node);
        if (node.children) flatten(node.children);
      });
    };
    flatten(nodes);

    const total = allNodes.length;
    const completed = allNodes.filter(n => n.status === AgentStatus.COMPLETED).length;
    const failed = allNodes.filter(n => n.status === AgentStatus.FAILED).length;
    const executing = allNodes.filter(n => n.status === AgentStatus.EXECUTING || n.status === AgentStatus.THINKING).length;
    
    return {
      total,
      completed,
      failed,
      executing,
      percent: total > 0 ? Math.round((completed / total) * 100) : 0,
      activeTasks: allNodes.filter(n => n.status !== AgentStatus.IDLE && n.id !== 'meta-root')
    };
  }, [nodes]);

  // Calculate Agent Communications
  const agentMetrics = useMemo(() => {
    const stats: Record<string, number> = {};
    logs.forEach(log => {
      stats[log.agentName] = (stats[log.agentName] || 0) + 1;
    });
    
    // Sort agents by activity
    return Object.entries(stats)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count);
  }, [logs]);

  return (
    <div className="flex-1 overflow-y-auto p-12 bg-[#050505] animate-in fade-in duration-700 relative custom-scrollbar">
      <div className="max-w-6xl mx-auto space-y-12">
        {/* Header */}
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-2 h-8 bg-purple-600 rounded-full shadow-[0_0_15px_#a855f7]"></div>
            <h1 className="text-4xl font-light text-white tracking-tight">Mission <span className="text-zinc-500 font-medium">Dashboard</span></h1>
          </div>
          <p className="text-zinc-500 max-w-2xl text-sm leading-relaxed tracking-wide">
            Real-time analytics for the active Flynt orchestration cluster. Monitor agent throughput, communication density, and overall project convergence.
          </p>
        </div>

        {/* Top Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[
            { label: 'Overall Progress', value: `${progressMetrics.percent}%`, icon: '📊', color: 'text-purple-400' },
            { label: 'Completed Tasks', value: progressMetrics.completed, icon: '✅', color: 'text-emerald-400' },
            { label: 'Active Streams', value: progressMetrics.executing, icon: '⚡', color: 'text-blue-400' },
            { label: 'System Errors', value: progressMetrics.failed, icon: '⚠️', color: 'text-red-400' },
          ].map((m, i) => (
            <div key={i} className="material-card material-surface p-6 rounded-2xl border border-white/5 flex items-center justify-between">
              <div>
                <p className="text-[10px] font-black text-zinc-600 uppercase tracking-widest mb-1">{m.label}</p>
                <p className={`text-2xl font-bold tracking-tight ${m.color}`}>{m.value}</p>
              </div>
              <div className="text-2xl opacity-20">{m.icon}</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Job Progress Chart / Timeline */}
          <div className="lg:col-span-2 space-y-6">
            <div className="flex items-center gap-4">
              <h2 className="text-[10px] font-black text-zinc-600 uppercase tracking-[0.4em]">Sub-task Convergence</h2>
              <div className="h-[1px] flex-1 bg-white/5"></div>
            </div>
            <div className="material-surface rounded-2xl border border-white/5 p-8 space-y-6 min-h-[400px]">
              {progressMetrics.activeTasks.length > 0 ? (
                <div className="space-y-6">
                  {progressMetrics.activeTasks.map((task) => (
                    <div key={task.id} className="space-y-2 group">
                      <div className="flex items-center justify-between text-[11px]">
                        <div className="flex items-center gap-3">
                           <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: (COLORS as any)[task.type.split(' ')[0].toUpperCase()] || '#52525b' }}></span>
                           <span className="text-zinc-300 font-bold uppercase tracking-widest">{task.label}</span>
                           <span className="text-zinc-600 mono text-[9px]">{task.status}</span>
                        </div>
                        <span className="text-zinc-500 mono">{new Date(task.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                      <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                        <div 
                          className={`h-full transition-all duration-1000 ${
                            task.status === AgentStatus.COMPLETED ? 'bg-emerald-500 shadow-[0_0_10px_#10b981]' :
                            task.status === AgentStatus.FAILED ? 'bg-red-500' : 
                            'bg-purple-500 animate-pulse shadow-[0_0_10px_#a855f7]'
                          }`}
                          style={{ width: task.status === AgentStatus.COMPLETED ? '100%' : task.status === AgentStatus.IDLE ? '5%' : '65%' }}
                        ></div>
                      </div>
                      <p className="text-[10px] text-zinc-500 line-clamp-1 italic opacity-0 group-hover:opacity-100 transition-opacity">
                        {task.output || 'Waiting for agent commitment...'}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-zinc-700 space-y-4 py-20">
                   <div className="w-12 h-12 rounded-full border-2 border-dashed border-white/5 flex items-center justify-center opacity-30">
                      🌀
                   </div>
                   <p className="text-xs uppercase tracking-[0.2em] font-bold">No active deployment sequence</p>
                </div>
              )}
            </div>
          </div>

          {/* Communication Volume */}
          <div className="space-y-6">
            <div className="flex items-center gap-4">
              <h2 className="text-[10px] font-black text-zinc-600 uppercase tracking-[0.4em]">Interaction Density</h2>
              <div className="h-[1px] flex-1 bg-white/5"></div>
            </div>
            <div className="material-surface rounded-2xl border border-white/5 p-8 flex flex-col gap-6 min-h-[400px]">
              {agentMetrics.length > 0 ? (
                agentMetrics.map((agent, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="space-y-1 flex-1">
                      <div className="flex justify-between items-end mb-1">
                        <span className="text-[10px] font-black text-zinc-300 uppercase tracking-widest">{agent.name}</span>
                        <span className="text-[10px] mono text-zinc-500">{agent.count} packets</span>
                      </div>
                      <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-purple-600 to-indigo-500" 
                          style={{ width: `${(agent.count / logs.length) * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-zinc-700 space-y-4 py-20">
                   <p className="text-[10px] uppercase tracking-[0.2em] font-bold">Comm link inactive</p>
                </div>
              )}
              
              <div className="mt-auto pt-6 border-t border-white/5 space-y-4">
                 <h4 className="text-[9px] font-black text-zinc-600 uppercase tracking-widest">Protocol Stats</h4>
                 <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-white/5 rounded-xl border border-white/5">
                       <p className="text-[8px] text-zinc-500 uppercase font-bold mb-1">Success Rate</p>
                       <p className="text-xs font-bold text-emerald-400">99.4%</p>
                    </div>
                    <div className="p-3 bg-white/5 rounded-xl border border-white/5">
                       <p className="text-[8px] text-zinc-500 uppercase font-bold mb-1">Latent Sync</p>
                       <p className="text-xs font-bold text-blue-400">22ms</p>
                    </div>
                 </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
