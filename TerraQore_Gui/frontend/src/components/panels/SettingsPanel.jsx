import React from 'react';
import { Sparkles, Shield, Zap, Activity, GitBranch } from 'lucide-react';

const SettingsPanel = () => {
  return (
    <div className="space-y-6">
      <LLMConfiguration />
      <SecuritySettings />
      <PSMPConfiguration />
      <BuildDataCollection />
      <CollaborationSettings />
      
      <button className="w-full bg-white text-black py-3 px-4 rounded font-medium hover:bg-white/90 transition">
        SAVE CONFIGURATION
      </button>
    </div>
  );
};

const LLMConfiguration = () => (
  <div className="border border-white/10 bg-white/5 rounded p-4">
    <div className="text-sm font-medium mb-4 flex items-center gap-2">
      <Sparkles className="w-4 h-4" />
      LLM PROVIDER
    </div>
    <div className="space-y-2">
      {['Gemini', 'Groq', 'Ollama'].map(provider => (
        <label key={provider} className="flex items-center gap-3 p-2 hover:bg-white/5 rounded cursor-pointer">
          <input type="radio" name="llm" defaultChecked={provider === 'Gemini'} className="w-4 h-4" />
          <span className="text-sm">{provider}</span>
        </label>
      ))}
    </div>
  </div>
);

const SecuritySettings = () => (
  <div className="border border-white/10 bg-white/5 rounded p-4">
    <div className="text-sm font-medium mb-4 flex items-center gap-2">
      <Shield className="w-4 h-4" />
      SECURITY
    </div>
    <div className="space-y-3">
      <label className="flex items-center justify-between">
        <span className="text-sm">Prompt Injection Protection</span>
        <input type="checkbox" defaultChecked className="w-4 h-4" />
      </label>
      <label className="flex items-center justify-between">
        <span className="text-sm">Context Validation</span>
        <input type="checkbox" defaultChecked className="w-4 h-4" />
      </label>
      <label className="flex items-center justify-between">
        <span className="text-sm">Conversation Monitoring</span>
        <input type="checkbox" defaultChecked className="w-4 h-4" />
      </label>
    </div>
  </div>
);

const PSMPConfiguration = () => (
  <div className="border border-white/10 bg-white/5 rounded p-4">
    <div className="text-sm font-medium mb-4 flex items-center gap-2">
      <Zap className="w-4 h-4" />
      PSMP (Project State Management)
    </div>
    <div className="space-y-3">
      <label className="flex items-center justify-between">
        <span className="text-sm">Auto-Block on Conflicts</span>
        <input type="checkbox" defaultChecked className="w-4 h-4" />
      </label>
      <label className="flex items-center justify-between">
        <span className="text-sm">Conflict Resolution Suggestions</span>
        <input type="checkbox" defaultChecked className="w-4 h-4" />
      </label>
      <div>
        <label className="text-sm block mb-2">Artifact Declaration Mode</label>
        <select className="w-full bg-black border border-white/20 rounded p-2 text-sm">
          <option>Mandatory (Strict)</option>
          <option>Optional (Permissive)</option>
        </select>
      </div>
    </div>
  </div>
);

const BuildDataCollection = () => (
  <div className="border border-white/10 bg-white/5 rounded p-4">
    <div className="text-sm font-medium mb-4 flex items-center gap-2">
      <Activity className="w-4 h-4" />
      BUILD DATA COLLECTION
    </div>
    <div className="space-y-3">
      <label className="flex items-center justify-between">
        <span className="text-sm">Stage Execution Tracking</span>
        <input type="checkbox" defaultChecked className="w-4 h-4" />
      </label>
      <label className="flex items-center justify-between">
        <span className="text-sm">Metrics Collection</span>
        <input type="checkbox" defaultChecked className="w-4 h-4" />
      </label>
      <label className="flex items-center justify-between">
        <span className="text-sm">Test Snapshot Saving</span>
        <input type="checkbox" defaultChecked className="w-4 h-4" />
      </label>
    </div>
  </div>
);

const CollaborationSettings = () => (
  <div className="border border-white/10 bg-white/5 rounded p-4">
    <div className="text-sm font-medium mb-4 flex items-center gap-2">
      <GitBranch className="w-4 h-4" />
      COLLABORATION
    </div>
    <div className="space-y-3">
      <div>
        <label className="text-sm block mb-2">Min Quality Threshold</label>
        <input 
          type="range" 
          min="0" 
          max="10" 
          step="0.5" 
          defaultValue="6"
          className="w-full"
        />
        <div className="text-xs text-white/60 text-right">6.0/10</div>
      </div>
      <div>
        <label className="text-sm block mb-2">Max Iterations per Agent</label>
        <input 
          type="number" 
          defaultValue="5"
          className="w-full bg-black border border-white/20 rounded p-2 text-sm"
        />
      </div>
    </div>
  </div>
);

export default SettingsPanel;