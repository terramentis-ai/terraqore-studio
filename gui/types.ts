
export enum AgentStatus {
  IDLE = 'idle',
  THINKING = 'thinking',
  EXECUTING = 'executing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export enum AgentType {
  META = 'Meta-Controller',
  ORCHESTRATOR = 'Orchestrator',
  RESEARCHER = 'Researcher',
  CODER = 'Engineer',
  ANALYST = 'Data Analyst',
  REVIEWER = 'Quality Assurance',
  EXECUTOR = 'Execution Engine'
}

export enum Tab {
  WORKSPACE = 'workspace',
  PLAYGROUND = 'playground',
  GALLERY = 'gallery',
  MODELS = 'models',
  DASHBOARD = 'dashboard',
  HISTORY = 'history',
  SETTINGS = 'settings'
}

export interface AgentNode {
  id: string;
  type: AgentType;
  label: string;
  status: AgentStatus;
  output?: string;
  children?: AgentNode[];
  timestamp: number;
}

export interface ExecutionLog {
  id: string;
  agentId: string;
  agentName: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timestamp: number;
}

export interface MetaState {
  isProcessing: boolean;
  nodes: AgentNode[];
  logs: ExecutionLog[];
  userInput: string;
  activeNodeId: string | null;
  currentTab: Tab;
  dynamicIcons: Record<string, string>;
  enabledTools: string[];
}
