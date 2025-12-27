
import React, { useState, useMemo } from 'react';
import { ExecutionLog } from '../types';

const MODELS = [
  {
    name: 'Gemini 3 Pro',
    id: 'gemini-3-pro-preview',
    type: 'Reasoning',
    description: 'Advanced reasoning, coding, and multi-step complex tasks.',
    specs: { context: '2M+', modalities: 'Text, Code, Vision', performance: '99th' },
    status: 'High Performance'
  },
  {
    name: 'Gemini 3 Flash',
    id: 'gemini-3-flash-preview',
    type: 'Speed',
    description: 'Fast, efficient performance for high-volume summarization and Q&A.',
    specs: { context: '1M', modalities: 'Text, Vision', latency: 'Sub-100ms' },
    status: 'Active'
  },
  {
    name: 'Gemini 2.5 Native Audio',
    id: 'gemini-2.5-flash-native-audio-preview-09-2025',
    type: 'Audio',
    description: 'Low-latency, real-time voice and audio processing.',
    specs: { latency: '<500ms', modalities: 'Audio In/Out', sampleRate: '24kHz' },
    status: 'Real-time'
  },
  {
    name: 'Veo 3.1 Fast',
    id: 'veo-3.1-fast-generate-preview',
    type: 'Video',
    description: 'High-quality cinematic video generation from text/image prompts.',
    specs: { resolution: '1080p', fps: '24/30', maxDuration: '60s' },
    status: 'Experimental'
  }
];

type ToolStatus = 'online' | 'offline' | 'maintenance';

interface Tool {
  id: string;
  name: string;
  icon: string;
  description: string;
  category: string;
  status: ToolStatus;
  maintenanceSchedule?: string;
}

const TOOLS: Tool[] = [
  // Intelligence & RAG
  { id: 'search', name: 'Google Search', icon: '🌐', description: 'Real-time web grounding for news and current events.', category: 'RAG & Intelligence', status: 'online' },
  { id: 'rag-vector', name: 'Vector DB', icon: '🗂️', description: 'High-performance retrieval across internal document embeddings.', category: 'RAG & Intelligence', status: 'online' },
  { id: 'knowledge-graph', name: 'Knowledge Graph', icon: '🕸️', description: 'Semantic mapping of entity relationships.', category: 'RAG & Intelligence', status: 'online' },
  { id: 'mcp-bridge', name: 'MCP Bridge', icon: '🌉', description: 'Model Context Protocol connector for external ecosystem data.', category: 'MCP', status: 'online' },
  
  // Data Science & ML
  { id: 'spark', name: 'Spark Engine', icon: '⚡', description: 'Distributed data processing for massive datasets.', category: 'Data Science', status: 'online' },
  { id: 'pandas', name: 'Pandas Node', icon: '🐼', description: 'Local Python-based data manipulation and cleaning.', category: 'Data Science', status: 'online' },
  { id: 'ml-inference', name: 'Inference Node', icon: '🧠', description: 'Real-time prediction and model serving.', category: 'ML', status: 'online' },
  
  // DevOps & MLOps
  { id: 'k8s', name: 'K8s Controller', icon: '☸️', description: 'Automated container orchestration and scaling.', category: 'DevOps', status: 'online' },
  { id: 'ci-cd', name: 'CI/CD Bridge', icon: '🚀', description: 'Automated testing and deployment pipelines.', category: 'DevOps', status: 'online' },
  { id: 'model-reg', name: 'Model Registry', icon: '📜', description: 'Version control and tracking for ML models.', category: 'MLOps', status: 'online' },
  { id: 'feature-store', name: 'Feature Store', icon: '🏪', description: 'Shared repository for model features.', category: 'MLOps', status: 'maintenance', maintenanceSchedule: 'Nov 12, 01:00 UTC' },
  
  // Execution & Core
  { id: 'interpreter', name: 'Code Interpreter', icon: '💻', description: 'Sandboxed Python execution.', category: 'Core', status: 'online' },
  { id: 'functions', name: 'Function Calling', icon: '🛠️', description: 'Dynamic interface for external API orchestration.', category: 'Core', status: 'online' },
  { id: 'dep-manager', name: 'Dependency Manager', icon: '📦', description: 'Resolves execution requirements.', category: 'Core', status: 'online' },
  { id: 'debugger', name: 'Step Debugger', icon: '🐛', description: 'Trace execution flow.', category: 'Core', status: 'offline' }
];

interface ModelsAndToolsProps {
  enabledTools: string[];
  onToggleTool: (toolName: string) => void;
  onReportIssue: (name: string, message: string, type: ExecutionLog['type']) => void;
}

const ModelsAndTools: React.FC<ModelsAndToolsProps> = ({ enabledTools, onToggleTool, onReportIssue }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [favorites, setFavorites] = useState<string[]>([]);
  const [activeMaintenanceInfo, setActiveMaintenanceInfo] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'all' | 'Intelligence' | 'Data Science' | 'Ops' | 'Core'>('all');

  const filteredModels = useMemo(() => {
    if (activeTab !== 'all' && activeTab !== 'Core') return [];
    return MODELS.filter(m => 
      m.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
      m.description.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [searchTerm, activeTab]);

  const filteredTools = useMemo<Tool[]>(() => {
    return TOOLS.filter(t => {
      const matchesSearch = t.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                           t.category.toLowerCase().includes(searchTerm.toLowerCase());
      if (activeTab === 'all') return matchesSearch;
      if (activeTab === 'Intelligence') return matchesSearch && (t.category === 'RAG & Intelligence' || t.category === 'MCP');
      if (activeTab === 'Ops') return matchesSearch && (t.category === 'DevOps' || t.category === 'MLOps');
      return matchesSearch && t.category === activeTab;
    });
  }, [searchTerm, activeTab]);

  const toggleFavorite = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setFavorites(prev => prev.includes(id) ? prev.filter(f => f !== id) : [...prev, id]);
  };

  const toolsByCategory = useMemo<Record<string, Tool[]>>(() => {
    const categories: Record<string, Tool[]> = {};
    filteredTools.forEach(tool => {
      if (!categories[tool.category]) categories[tool.category] = [];
      categories[tool.category].push(tool);
    });
    return categories;
  }, [filteredTools]);

  return (
    <div className="flex-1 overflow-y-auto p-12 bg-[#050505] animate-in fade-in duration-700 relative custom-scrollbar">
      <div className="max-w-6xl mx-auto space-y-12">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-4">
             <div className="flex items-center gap-3">
                <div className="w-2 h-8 bg-purple-600 rounded-full shadow-[0_0_15px_#a855f7]"></div>
                <h1 className="text-4xl font-light text-white tracking-tight">Registry <span className="text-zinc-500 font-medium">Explorer</span></h1>
             </div>
            <p className="text-zinc-500 max-w-2xl text-sm leading-relaxed tracking-wide">
              TerraQore Studio's unified resource platform. Manage RAG pipelines, DS engines, and MLOps deployments within a high-density material ecosystem.
            </p>
          </div>
          
          <div className="flex flex-col gap-4 items-end">
            <div className="relative w-80">
              <input
                type="text"
                placeholder="Search resources..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-12 pr-4 text-sm text-zinc-200 focus:outline-none focus:ring-2 focus:ring-purple-500/20 material-surface"
              />
              <svg className="w-5 h-5 absolute left-4 top-3 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            
            <div className="flex bg-black/40 p-1 rounded-xl border border-white/5 backdrop-blur-md material-surface">
               {(['all', 'Intelligence', 'Data Science', 'Ops', 'Core'] as const).map((tab) => (
                 <button
                   key={tab}
                   onClick={() => setActiveTab(tab)}
                   className={`px-4 py-2 text-[9px] font-black uppercase tracking-widest rounded-lg transition-all duration-300 ${
                     activeTab === tab 
                       ? 'bg-purple-600 text-white shadow-lg' 
                       : 'text-zinc-500 hover:text-zinc-300'
                   }`}
                 >
                   {tab}
                 </button>
               ))}
            </div>
          </div>
        </div>

        {filteredModels.length > 0 && (
          <section className="space-y-6">
            <div className="flex items-center gap-4">
              <h2 className="text-[10px] font-black text-zinc-600 uppercase tracking-[0.4em]">Proprietary Compute</h2>
              <div className="h-[1px] flex-1 bg-white/5"></div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {filteredModels.map((model) => (
                <div key={model.id} className="group material-card p-6 rounded-2xl material-surface border border-white/5 flex flex-col justify-between h-[280px] relative">
                  <div>
                    <span className="text-[9px] font-black text-purple-400 uppercase tracking-widest mb-4 block">
                      {model.type}
                    </span>
                    <h3 className="text-lg font-semibold text-zinc-100 mb-2 tracking-tight">{model.name}</h3>
                    <p className="text-[10px] text-zinc-500 leading-relaxed line-clamp-2">{model.description}</p>
                    
                    {/* Report Issue button for models with statuses other than High Performance/Active */}
                    {model.status !== 'High Performance' && model.status !== 'Active' && (
                      <button 
                        onClick={() => onReportIssue(model.name, 'issue reported', 'error')}
                        className="mt-3 px-3 py-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 text-[9px] font-black uppercase tracking-widest rounded-lg transition-all"
                      >
                        Report Issue
                      </button>
                    )}
                  </div>
                  <div className="flex justify-between items-center pt-4 border-t border-white/5">
                    <span className="text-[9px] text-zinc-400 mono">{model.specs.context}</span>
                    <span className="text-[9px] text-zinc-600 font-bold uppercase">{model.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="space-y-12 pb-20">
          {(Object.entries(toolsByCategory) as [string, Tool[]][]).map(([category, tools]) => (
            <div key={category} className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
              <div className="flex items-center gap-4">
                <h3 className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.3em] bg-white/5 px-4 py-1.5 rounded-xl border border-white/5">
                  {category}
                </h3>
                <div className="h-[1px] flex-1 bg-white/5"></div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {tools.map((tool) => {
                  const isActive = enabledTools.includes(tool.name);
                  const isStarred = favorites.includes(tool.id);
                  const isMaintenance = tool.status === 'maintenance';
                  const isOffline = tool.status === 'offline';
                  
                  return (
                    <div 
                      key={tool.id} 
                      className={`material-card p-6 rounded-2xl border transition-all duration-300 relative overflow-hidden flex flex-col h-full material-surface cursor-pointer ${
                        isActive ? 'border-purple-500/50 shadow-[0_0_30px_rgba(168,85,247,0.1)]' : 'border-white/5 hover:border-white/20'
                      }`}
                      onClick={() => tool.status === 'online' && onToggleTool(tool.name)}
                    >
                      <div className="flex justify-between items-start mb-6">
                        <div className="text-3xl filter drop-shadow-[0_0_8px_rgba(255,255,255,0.2)]">
                          {tool.icon}
                        </div>
                        <div className="flex items-center gap-3">
                           <div 
                             className={`w-2 h-2 rounded-full ${tool.status === 'online' ? 'bg-emerald-500 shadow-[0_0_8px_#10b981]' : isMaintenance ? 'bg-amber-500 animate-pulse' : 'bg-red-500'}`}
                             onClick={(e) => {
                               e.stopPropagation();
                               if (isMaintenance) setActiveMaintenanceInfo(tool.id);
                               if (isOffline) onReportIssue(tool.name, "Critical outage reported.", "error");
                             }}
                           ></div>
                           {tool.status === 'online' && (
                             <div className={`w-8 h-4 rounded-full p-0.5 transition-all ${isActive ? 'bg-purple-600' : 'bg-white/10'}`}>
                               <div className={`w-3 h-3 bg-white rounded-full transition-all ${isActive ? 'translate-x-4' : ''}`}></div>
                             </div>
                           )}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className={`text-sm font-bold tracking-tight ${isActive ? 'text-white' : 'text-zinc-300'}`}>{tool.name}</h4>
                        <button 
                          onClick={(e) => toggleFavorite(tool.id, e)}
                          className={`hover:scale-125 transition-transform ${isStarred ? 'text-amber-400' : 'text-zinc-800'}`}
                        >
                          ★
                        </button>
                      </div>
                      <p className="text-[10px] text-zinc-500 leading-relaxed font-medium flex-1">
                        {tool.description}
                      </p>

                      {isMaintenance && activeMaintenanceInfo === tool.id && (
                        <div className="mt-3 p-2 bg-amber-500/10 border border-amber-500/20 rounded-lg text-[9px] text-amber-400 mono">
                          Next: {tool.maintenanceSchedule}
                        </div>
                      )}
                      
                      {isActive && <div className="absolute left-0 top-0 bottom-0 w-1 bg-purple-500 shadow-[0_0_10px_#a855f7]"></div>}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
};

export default ModelsAndTools;
