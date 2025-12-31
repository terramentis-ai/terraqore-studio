import React, { useState, useCallback, useMemo } from 'react';
import { AgentNode, AgentStatus, AgentType, ExecutionLog } from '../types';
import { COLORS } from '../constants';

interface PlaygroundProps {
  nodes: AgentNode[];
  logs: ExecutionLog[];
  userInput: string;
  isProcessing: boolean;
  onExecute: (prompt: string) => void;
}

interface WorkflowStep {
  id: string;
  label: string;
  status: AgentStatus;
  type: AgentType;
  output?: string;
  timestamp: number;
  duration?: number;
}

const Playground: React.FC<PlaygroundProps> = ({ 
  nodes, 
  logs, 
  userInput, 
  isProcessing, 
  onExecute 
}) => {
  const [prompt, setPrompt] = useState('');
  const [selectedStep, setSelectedStep] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState<boolean>(true); // controls Preview Console visibility
  const [previewMode, setPreviewMode] = useState<'raw' | 'code' | 'markdown'>('raw');

  // Flatten workflow tree into steps for visualization
  const workflowSteps = useMemo(() => {
    const steps: WorkflowStep[] = [];
    const processNode = (node: AgentNode, depth: number = 0) => {
      steps.push({
        id: node.id,
        label: node.label,
        status: node.status,
        type: node.type as AgentType,
        output: node.output,
        timestamp: node.timestamp,
      });
      if (node.children) {
        node.children.forEach(child => processNode(child, depth + 1));
      }
    };
    nodes.forEach(node => processNode(node));
    return steps;
  }, [nodes]);

  const handleExecute = useCallback(() => {
    if (prompt.trim()) {
      onExecute(prompt);
      setPrompt('');
      setSelectedStep(null);
    }
  }, [prompt, onExecute]);

  const getStatusColor = (status: AgentStatus): string => {
    switch (status) {
      case AgentStatus.COMPLETED:
        return 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300';
      case AgentStatus.FAILED:
        return 'bg-red-500/20 border-red-500/50 text-red-300';
      case AgentStatus.EXECUTING:
      case AgentStatus.THINKING:
        return 'bg-blue-500/20 border-blue-500/50 text-blue-300 animate-pulse';
      default:
        return 'bg-zinc-800/50 border-zinc-700/50 text-zinc-300';
    }
  };

  const getStatusIcon = (status: AgentStatus): string => {
    switch (status) {
      case AgentStatus.COMPLETED:
        return '✓';
      case AgentStatus.FAILED:
        return '✕';
      case AgentStatus.EXECUTING:
        return '⚙';
      case AgentStatus.THINKING:
        return '◉';
      default:
        return '○';
    }
  };

  const selectedStepData = selectedStep 
    ? workflowSteps.find(s => s.id === selectedStep)
    : null;

  const handleDownloadArtifact = useCallback(() => {
    const content = selectedStepData?.output || '';
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedStepData?.label?.replace(/\s+/g, '_') || 'artifact'}.txt`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }, [selectedStepData]);

  const openGitHubExport = useCallback(() => {
    window.open('https://github.com/new', '_blank');
  }, []);

  const openAgentsHub = useCallback(() => {
    // Placeholder: replace with actual TerraQore AgentsHub deployment URL when available
    window.open('https://terraqore.com', '_blank');
  }, []);

  return (
    <div className="flex-1 overflow-auto bg-[#050505] flex flex-col animate-in fade-in duration-700 min-h-0">
      {/* Header */}
      <div className="border-b border-white/10 p-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-2 h-8 bg-cyan-500 rounded-full shadow-[0_0_15px_#06b6d4]"></div>
          <h1 className="text-3xl font-light text-white tracking-tight">
            Workflow <span className="text-zinc-500 font-medium">Playground</span>
          </h1>
        </div>
        <p className="text-zinc-500 text-sm max-w-2xl leading-relaxed">
          Design and visualize your AI agent workflows in real-time. Monitor execution flow, task status, and generated outputs.
        </p>
        {/* Deploy / Export Toolbar */}
        <div className="flex flex-wrap gap-3 pt-2">
          <button
            onClick={openAgentsHub}
            className="px-3 py-2 text-xs rounded-lg border border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/10 transition"
            title="Deploy to TerraQore AgentsHub"
          >
            🚀 Deploy to AgentsHub
          </button>
          <button
            onClick={openGitHubExport}
            className="px-3 py-2 text-xs rounded-lg border border-white/10 text-zinc-300 hover:bg-white/5 transition"
            title="Export to GitHub"
          >
            🌐 Export to GitHub
          </button>
          <button
            onClick={handleDownloadArtifact}
            disabled={!selectedStepData?.output}
            className="px-3 py-2 text-xs rounded-lg border border-white/10 text-zinc-300 hover:bg-white/5 disabled:opacity-50 disabled:cursor-not-allowed transition"
            title="Download current step output"
          >
            ⬇ Download Artifact
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto flex flex-col lg:flex-row gap-6 p-6 min-h-0">
        {/* Left Panel: Workflow Input & Visualization */}
        <div className="flex-1 flex flex-col space-y-6 overflow-auto min-h-0">
          {/* Workflow Prompt */}
          <div className="space-y-3">
            <label className="text-[10px] font-black text-zinc-600 uppercase tracking-[0.4em]">
              Workflow Prompt
            </label>
            <div className="flex gap-2">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe your workflow or task for the agent cluster..."
                className="flex-1 bg-zinc-900/50 border border-white/10 rounded-xl p-4 text-white text-sm placeholder-zinc-600 focus:outline-none focus:border-cyan-500/50 resize-none h-24"
                disabled={isProcessing}
              />
            </div>
            <div className="flex gap-3 items-center">
              <button
                onClick={handleExecute}
                disabled={isProcessing || !prompt.trim()}
                className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 text-white font-medium rounded-lg hover:shadow-lg hover:shadow-cyan-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center gap-2"
              >
                {isProcessing ? (
                  <>
                    <span className="inline-block animate-spin">⚙</span>
                    Executing...
                  </>
                ) : (
                  <>
                    ▶ Execute Workflow
                  </>
                )}
              </button>
              <div className="flex-1 flex gap-4 text-[11px]">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                  <span className="text-zinc-400">Pending</span>
                </div>
              </div>
            </div>
          </div>

          {/* Step Details (moved under Workflow Prompt) */}
          <div className="flex flex-col space-y-3 overflow-hidden">
            <div className="flex items-center gap-3">
              <h2 className="text-[10px] font-black text-zinc-600 uppercase tracking-[0.4em]">Step Details</h2>
              <div className="h-[1px] flex-1 bg-white/5"></div>
            </div>
            {selectedStepData ? (
              <div className="material-surface rounded-2xl border border-white/5 p-6 overflow-hidden flex flex-col space-y-4">
                <div className="space-y-2 pb-4 border-b border-white/5">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: (COLORS as any)[selectedStepData.type.split(' ')[0].toUpperCase()] || '#52525b' }}></div>
                    <h3 className="text-sm font-bold text-white">{selectedStepData.label}</h3>
                  </div>
                  <div className="flex gap-3 text-[10px] text-zinc-500">
                    <span className={`px-2 py-1 rounded border ${getStatusColor(selectedStepData.status)}`}>{selectedStepData.status.toUpperCase()}</span>
                    <span>{selectedStepData.type}</span>
                    <span className="ml-auto text-zinc-600">{new Date(selectedStepData.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
                <div className="text-[10px] text-zinc-500">
                  <span className="text-zinc-600">ID:</span> <span className="font-mono text-zinc-400">{selectedStepData.id}</span>
                </div>
              </div>
            ) : (
              <div className="material-surface rounded-2xl border border-white/5 p-6 flex items-center justify-center text-zinc-600 text-xs">Select a step to view details.</div>
            )}
          </div>

          {/* Activity Log (moved under Workflow Prompt) */}
          <div className="flex flex-col space-y-3 overflow-hidden">
            <div className="flex items-center gap-3">
              <h2 className="text-[10px] font-black text-zinc-600 uppercase tracking-[0.4em]">Activity Log</h2>
              <div className="h-[1px] flex-1 bg-white/5"></div>
            </div>
            <div className="material-surface rounded-2xl border border-white/5 p-4 overflow-y-auto custom-scrollbar space-y-2 max-h-64">
              {logs.slice(-10).reverse().map((log) => (
                <div key={log.id} className={`text-[10px] p-2 rounded border pl-3 border-l-2 ${
                    log.type === 'success'
                      ? 'bg-emerald-500/10 border-emerald-600 text-emerald-300'
                      : log.type === 'error'
                      ? 'bg-red-500/10 border-red-600 text-red-300'
                      : log.type === 'warning'
                      ? 'bg-amber-500/10 border-amber-600 text-amber-300'
                      : 'bg-blue-500/10 border-blue-600 text-blue-300'
                  }`}>
                  <div className="font-bold uppercase tracking-widest">{log.agentName}</div>
                  <div className="text-[9px] opacity-90 mt-1">{log.message}</div>
                  <div className="text-[8px] opacity-60 mt-1">{new Date(log.timestamp).toLocaleTimeString()}</div>
                </div>
              ))}
              {logs.length === 0 && (
                <div className="flex items-center justify-center h-full text-zinc-600 text-xs">No logs yet</div>
              )}
            </div>
          </div>

          {/* Workflow Steps Visualization */}
          <div className="flex-1 overflow-auto flex flex-col space-y-3 min-h-0">
            <div className="flex items-center gap-3">
              <h2 className="text-[10px] font-black text-zinc-600 uppercase tracking-[0.4em]">
                Execution Flow
              </h2>
              <div className="h-[1px] flex-1 bg-white/5"></div>
              <button
                onClick={() => setShowDetails(v => !v)}
                className="text-[10px] px-2 py-1 rounded border border-white/10 text-zinc-400 hover:text-white hover:border-white/20 transition"
                title={showDetails ? 'Hide preview console' : 'Show preview console'}
              >
                {showDetails ? 'Hide Preview' : 'Show Preview'}
              </button>
            </div>

            {workflowSteps.length > 0 ? (
              <div className="flex-1 overflow-y-auto custom-scrollbar space-y-2 pr-2">
                {workflowSteps.map((step, index) => (
                  <div
                    key={step.id}
                    onClick={() => setSelectedStep(step.id)}
                    className={`group cursor-pointer transition-all duration-200 ${
                      selectedStep === step.id ? 'ring-2 ring-cyan-500/50' : ''
                    }`}
                  >
                    <div className={`border rounded-lg p-3 backdrop-blur-sm ${getStatusColor(step.status)}`}>
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-start gap-3 flex-1 min-w-0">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-xs font-bold">
                            {getStatusIcon(step.status)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-bold uppercase tracking-wide truncate">
                              {step.label}
                            </p>
                            <p className="text-[9px] text-zinc-500 mt-1">
                              Step {index + 1} • {step.type}
                            </p>
                          </div>
                        </div>
                        <div className="flex-shrink-0 text-xs font-mono text-zinc-500">
                          {step.status}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center space-y-2">
                  <p className="text-zinc-600 text-sm">No workflow steps yet</p>
                  <p className="text-zinc-700 text-xs">Enter a prompt and execute to see the workflow</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel: Preview Console */}
        {showDetails && (
          <div className="w-full lg:w-96 min-w-64 flex flex-col space-y-3 overflow-auto">
            <div className="flex items-center gap-3">
              <h2 className="text-[10px] font-black text-zinc-600 uppercase tracking-[0.4em]">Preview Console</h2>
              <div className="h-[1px] flex-1 bg-white/5"></div>
              <div className="flex items-center gap-2 text-[10px]">
                <button onClick={() => setPreviewMode('raw')} className={`px-2 py-1 rounded border ${previewMode==='raw'?'border-cyan-500/50 text-white':'border-white/10 text-zinc-400'} hover:border-white/20`}>Raw</button>
                <button onClick={() => setPreviewMode('code')} className={`px-2 py-1 rounded border ${previewMode==='code'?'border-cyan-500/50 text-white':'border-white/10 text-zinc-400'} hover:border-white/20`}>Code</button>
                <button onClick={() => setPreviewMode('markdown')} className={`px-2 py-1 rounded border ${previewMode==='markdown'?'border-cyan-500/50 text-white':'border-white/10 text-zinc-400'} hover:border-white/20`}>Markdown</button>
              </div>
            </div>
            <div className="flex-1 material-surface rounded-2xl border border-white/5 p-0 overflow-hidden flex flex-col">
              {selectedStepData?.output ? (
                <div className="flex-1 overflow-auto custom-scrollbar bg-black/50">
                  <pre className="text-xs text-zinc-200 font-mono p-4 whitespace-pre-wrap break-words">
                    {selectedStepData.output}
                  </pre>
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center text-zinc-600 text-xs p-6">
                  Select a step with output to preview.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Playground;
