
export const COLORS = {
  META: '#a855f7', // Purple
  ORCHESTRATOR: '#6366f1', // Indigo
  RESEARCHER: '#0ea5e9', // Blue
  CODER: '#10b981', // Emerald
  ANALYST: '#f59e0b', // Amber
  REVIEWER: '#ef4444', // Red
  EXECUTOR: '#71717a', // Zinc
};

export const INITIAL_NODES = [
  {
    id: 'meta-root',
    type: 'Meta-Controller',
    label: 'Meta Control System',
    status: 'idle',
    timestamp: Date.now(),
    children: []
  }
];
