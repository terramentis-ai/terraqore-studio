
import React, { useState, useCallback, useEffect } from 'react';
import { AgentNode, AgentStatus, AgentType, ExecutionLog, MetaState, Tab } from './types';
import { INITIAL_NODES } from './constants';
import ModelsAndTools from './components/ModelsAndTools';
import Dashboard from './components/Dashboard';
import Playground from './components/Playground';
import ProjectDashboard from './components/ProjectDashboard';
import ProjectDetail from './components/ProjectDetail';
import ProjectGallery from './components/ProjectGallery';
import { metaAgentService } from './services/geminiService';
import terraqoreAPI from './services/terraqoreAPIService';
import { Project } from './services/terraqoreAPIService';
import Settings from './components/Settings';

const App: React.FC = () => {
  const [state, setState] = useState<MetaState>({
    isProcessing: false,
    nodes: JSON.parse(JSON.stringify(INITIAL_NODES)),
    logs: [],
    userInput: '',
    activeNodeId: null,
    currentTab: Tab.WORKSPACE,
    dynamicIcons: {},
    enabledTools: ['Google Search', 'Code Interpreter']
  });

  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [projectViewMode, setProjectViewMode] = useState<'dashboard' | 'detail'>('dashboard');

  // Initialize Dynamic Icons from AI sequentially to prevent 429 Quota Exhaustion
  useEffect(() => {
    const fetchIcons = async () => {
      const types = Object.values(AgentType);
      const iconMap: Record<string, string> = {};
      
      addLog('System', 'Initializing TerraQore Icon Engine...', 'info');
      
      // Process icons one by one to respect rate limits
      for (const type of types) {
        try {
          const path = await metaAgentService.generateAgentIcon(type);
          if (path) {
            iconMap[type] = path;
            // Update state incrementally so UI improves as icons arrive
            setState(prev => ({
              ...prev,
              dynamicIcons: { ...prev.dynamicIcons, [type]: path }
            }));
          }
          // Small delay to further mitigate rate limiting
          await new Promise(resolve => setTimeout(resolve, 200));
        } catch (error) {
          console.warn(`Could not generate custom icon for ${type}, using fallback.`);
        }
      }
      
      addLog('System', 'Platform assets synchronized.', 'success');
    };

    fetchIcons();
  }, []);

  // Health check on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await terraqoreAPI.healthCheck();
        addLog('System', 'FastAPI backend connected successfully.', 'success');
      } catch (err) {
        addLog('System', 'Warning: FastAPI backend not available. Running in offline mode.', 'warning');
      }
    };

    checkHealth();
  }, []);

  const addLog = useCallback((agentName: string, message: string, type: ExecutionLog['type'] = 'info') => {
    const newLog: ExecutionLog = {
      id: Math.random().toString(36).substr(2, 9),
      agentId: 'system',
      agentName,
      message,
      type,
      timestamp: Date.now(),
    };
    setState(prev => ({ ...prev, logs: [...prev.logs, newLog] }));
  }, []);

  const updateNode = useCallback((nodeId: string, updates: Partial<AgentNode>) => {
    setState(prev => {
      const newNodes = [...prev.nodes];
      const findAndReplace = (nodes: AgentNode[]): boolean => {
        for (let i = 0; i < nodes.length; i++) {
          if (nodes[i].id === nodeId) {
            nodes[i] = { ...nodes[i], ...updates };
            return true;
          }
          if (nodes[i].children && findAndReplace(nodes[i].children!)) return true;
        }
        return false;
      };
      findAndReplace(newNodes);
      return { ...prev, nodes: newNodes };
    });
  }, []);

  const handleExecute = async (prompt: string) => {
    setState(prev => ({ 
      ...prev, 
      isProcessing: true, 
      userInput: prompt,
      nodes: JSON.parse(JSON.stringify(INITIAL_NODES)),
      logs: [],
      activeNodeId: 'meta-root',
      currentTab: Tab.PLAYGROUND
    }));

    addLog('System', 'Launching TerraQore Orchestration Protocol...', 'info');
    addLog('System', `Active tools: ${state.enabledTools.join(', ')}`, 'info');
    
    updateNode('meta-root', { status: AgentStatus.THINKING });
    addLog('Meta-Controller', `Analyzing objective: "${prompt}"`, 'info');
    
    const plan = await metaAgentService.planTask(prompt);
    
    if (!plan) {
      addLog('Meta-Controller', 'Failed to generate orchestration plan.', 'error');
      updateNode('meta-root', { status: AgentStatus.FAILED });
      setState(prev => ({ ...prev, isProcessing: false }));
      return;
    }

    addLog('Meta-Controller', `Plan generated. Objective: ${plan.objective}`, 'success');
    addLog('Meta-Controller', `Delegating to ${plan.subtasks.length} specialized agents.`, 'info');

    const subTasks = plan.subtasks.map((st: any, idx: number) => ({
      id: `task-${idx}`,
      type: st.agentType as AgentType,
      label: st.agentType,
      status: AgentStatus.IDLE,
      timestamp: Date.now(),
      output: st.description,
      children: []
    }));

    updateNode('meta-root', { 
      status: AgentStatus.COMPLETED,
      children: subTasks,
      output: `Objective: ${plan.objective}\nOrchestration strategy: Multi-agent concurrent execution defined.`
    });

    let cumulativeContext = `Primary Objective: ${plan.objective}\n`;

    // Process tasks
    for (let i = 0; i < subTasks.length; i++) {
      const task = subTasks[i];
      setState(prev => ({ ...prev, activeNodeId: task.id }));
      updateNode(task.id, { status: AgentStatus.THINKING });
      addLog(task.type, `Executing: ${task.output}`, 'info');

      await new Promise(r => setTimeout(r, 2000));

      try {
        const result = await metaAgentService.executeAgentTask(task.type, task.output || '', cumulativeContext);
        cumulativeContext += `\n[${task.type} Output]: ${result}`;
        
        updateNode(task.id, { status: AgentStatus.COMPLETED, output: result });
        addLog(task.type, 'Task finalized.', 'success');
      } catch (err) {
        updateNode(task.id, { status: AgentStatus.FAILED });
        addLog(task.type, 'Execution error.', 'error');
      }
    }

    setState(prev => ({ ...prev, activeNodeId: 'meta-root' }));
    addLog('Meta-Controller', 'Workflow complete. Deployment finalized.', 'success');
    setState(prev => ({ ...prev, isProcessing: false }));
  };

  const handleExecuteWorkflow = async (projectId: number, workflowType: string) => {
    try {
      setState(prev => ({ ...prev, isProcessing: true }));
      addLog('System', `Executing ${workflowType} workflow for project...`, 'info');
      
      const result = await terraqoreAPI.runWorkflow(projectId, workflowType);
      
      setState(prev => ({
        ...prev,
        logs: [
          ...prev.logs,
          {
            id: Math.random().toString(36).substr(2, 9),
            agentId: 'workflow-' + workflowType,
            agentName: workflowType.toUpperCase(),
            message: result.output,
            type: result.status === 'success' ? 'success' : 'error',
            timestamp: Date.now(),
          }
        ]
      }));
    } catch (err) {
      addLog('System', `Workflow failed: ${err instanceof Error ? err.message : 'Unknown error'}`, 'error');
    } finally {
      setState(prev => ({ ...prev, isProcessing: false }));
    }
  };

  const handleToggleTool = (toolName: string) => {
    setState(prev => {
      const isEnabled = prev.enabledTools.includes(toolName);
      return {
        ...prev,
        enabledTools: isEnabled 
          ? prev.enabledTools.filter(t => t !== toolName)
          : [...prev.enabledTools, toolName]
      };
    });
  };

  return (
    <div className="flex min-h-screen w-full overflow-hidden bg-[#050505] text-zinc-100">
      {/* Sidebar / Left Nav - Material Surface */}
      <div className="w-16 flex-shrink-0 border-r border-white/10 flex flex-col items-center py-8 gap-8 bg-black/20 backdrop-blur-3xl z-30 shadow-2xl sticky top-0 h-screen overflow-y-auto">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-500/30 transform transition-transform hover:scale-110 active:scale-95">
          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div className="flex flex-col gap-6">
          {[
            { id: Tab.WORKSPACE, icon: 'W', label: 'Project Workspace' },
            { id: Tab.PLAYGROUND, icon: 'P', label: 'Workflow Playground' },
            { id: Tab.GALLERY, icon: 'G', label: 'Project Gallery' },
            { id: Tab.DASHBOARD, icon: 'D', label: 'Mission Dashboard' },
            { id: Tab.MODELS, icon: 'R', label: 'Resources Registry' },
            { id: Tab.HISTORY, icon: 'H', label: 'Task History' },
            { id: Tab.SETTINGS, icon: 'S', label: 'System Settings' },
          ].map((tab) => (
            <button 
              key={tab.id} 
              onClick={() => setState(prev => ({ ...prev, currentTab: tab.id }))}
              title={tab.label}
              className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300 relative group ${
                state.currentTab === tab.id 
                  ? 'bg-white/10 text-white shadow-[0_0_15px_rgba(255,255,255,0.05)]' 
                  : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/5'
              }`}
            >
              <span className="text-[11px] font-bold tracking-tighter">{tab.icon}</span>
              {state.currentTab === tab.id && (
                <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-5 bg-purple-500 rounded-l-full shadow-[0_0_10px_#a855f7]"></div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Main Container */}
      <div className="flex-1 flex flex-col relative min-h-0 overflow-auto">
        <header className="h-16 border-b border-white/5 flex items-center px-8 justify-between bg-[#080808]/80 backdrop-blur-md z-20 shadow-xl">
          <div className="flex items-center gap-4">
            <h1 className="text-sm font-bold tracking-[0.3em] uppercase text-transparent bg-clip-text bg-gradient-to-r from-zinc-100 to-zinc-500">
              TerraQore Studio
            </h1>
            <div className="h-4 w-[1px] bg-white/10"></div>
            <div className="flex items-center gap-2">
               <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                {state.currentTab === Tab.WORKSPACE
                  ? 'Project Workspace'
                  : state.currentTab === Tab.PLAYGROUND
                  ? 'Workflow Playground'
                  : state.currentTab === Tab.GALLERY
                  ? 'Project Gallery'
                  : state.currentTab === Tab.MODELS
                  ? 'Registry Explorer'
                  : state.currentTab === Tab.DASHBOARD
                  ? 'System Dashboard'
                  : 'TerraQore Studio'}
               </span>
            </div>
          </div>
          <div className="flex items-center gap-6">
            {state.isProcessing && (
              <div className="flex items-center gap-3 px-4 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/30 animate-in fade-in zoom-in duration-300">
                <div className="w-1.5 h-1.5 bg-purple-500 rounded-full animate-ping shadow-[0_0_8px_#a855f7]"></div>
                <span className="text-[10px] font-bold text-purple-400 uppercase tracking-widest">Orchestrating Logic</span>
              </div>
            )}
            <div className="flex items-center gap-3 group cursor-pointer">
              <div className="text-right">
                <p className="text-[10px] font-bold text-zinc-200 uppercase leading-none">Jordan D.</p>
                <p className="text-[8px] text-zinc-500 uppercase tracking-tighter">Admin Principal</p>
              </div>
              <div className="h-9 w-9 rounded-xl material-surface flex items-center justify-center text-[10px] text-purple-400 font-bold border border-purple-500/20 group-hover:border-purple-500/50 transition-colors">
                JD
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 flex overflow-auto relative min-h-0">
          {state.currentTab === Tab.WORKSPACE ? (
            selectedProject && projectViewMode === 'detail' ? (
              <ProjectDetail 
                project={selectedProject}
                onBack={() => {
                  setSelectedProject(null);
                  setProjectViewMode('dashboard');
                }}
                onExecuteWorkflow={handleExecuteWorkflow}
              />
            ) : (
              <ProjectDashboard 
                onSelectProject={(project) => {
                  setSelectedProject(project);
                  setProjectViewMode('detail');
                }}
                onCreateProject={() => {
                  setProjectViewMode('dashboard');
                }}
              />
            )
          ) : state.currentTab === Tab.PLAYGROUND ? (
            <Playground 
              nodes={state.nodes}
              logs={state.logs}
              userInput={state.userInput}
              isProcessing={state.isProcessing}
              onExecute={handleExecute}
            />
          ) : state.currentTab === Tab.GALLERY ? (
            <ProjectGallery />
          ) : state.currentTab === Tab.DASHBOARD ? (
            <Dashboard nodes={state.nodes} logs={state.logs} />
          ) : state.currentTab === Tab.MODELS ? (
            <ModelsAndTools 
              enabledTools={state.enabledTools} 
              onToggleTool={handleToggleTool} 
              onReportIssue={(name, msg, type) => addLog(name, msg, type)}
            />
          ) : state.currentTab === Tab.SETTINGS ? (
            <Settings />
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-zinc-600 space-y-4">
              <div className="w-16 h-16 rounded-full border border-white/5 flex items-center justify-center text-2xl opacity-20">⚙️</div>
              <p className="italic text-xs tracking-widest uppercase">System module under encryption...</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
