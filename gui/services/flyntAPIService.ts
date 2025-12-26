/**
 * Flynt API Service
 * Client for communicating with the Flynt FastAPI backend
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export interface Project {
  id: number;
  name: string;
  description?: string;
  status: 'initialized' | 'planning' | 'in_progress' | 'blocked' | 'completed' | 'archived';
  created_at: string;
  updated_at?: string;
  task_count: number;
  completion_percentage: number;
}

export interface Task {
  id: number;
  project_id: number;
  title: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  milestone?: string;
  priority: number;
  estimated_hours?: number;
  actual_hours?: number;
  agent_type?: string;
  created_at: string;
  completed_at?: string;
}

export interface WorkflowExecutionResult {
  workflow_id: string;
  project_id: number;
  workflow_type: 'ideate' | 'plan';
  status: 'running' | 'completed' | 'failed';
  output: string;
  error?: string;
  execution_time: number;
}

export interface AgentExecutionResult {
  agent_name: string;
  project_id: number;
  success: boolean;
  output: string;
  execution_time: number;
  error?: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface ConflictInfo {
  library: string;
  requirements: Array<{
    agent: string;
    needs: string;
    purpose: string;
  }>;
  severity: string;
  suggested_resolutions: string[];
}

export interface ProjectBlock {
  project_id: number;
  status: string;
  conflicts: ConflictInfo[];
  blocked_since: string;
}

export interface LLMProviderInfo {
  id: string;
  name: string;
  requires_api_key: boolean;
  default_model?: string;
}

export interface LLMConfigSnapshot {
  primary_provider: string;
  primary_model: string;
  primary_temperature: number;
  primary_max_tokens: number;
  primary_api_key_set: boolean;
  fallback_provider?: string | null;
  fallback_model?: string | null;
  fallback_temperature?: number | null;
  fallback_max_tokens?: number | null;
  fallback_api_key_set?: boolean;
}

export interface LLMConfigUpdate {
  primary_provider: string;
  model: string;
  api_key?: string;
  temperature?: number;
  max_tokens?: number;
  fallback_provider?: string | null;
  fallback_model?: string | null;
  fallback_api_key?: string;
  fallback_temperature?: number;
  fallback_max_tokens?: number;
}

class FlyntAPIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    method: 'GET' | 'POST' | 'PATCH' | 'DELETE' = 'GET',
    body?: any
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(url, options);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error [${method} ${endpoint}]:`, error);
      throw error;
    }
  }

  // Projects API
  async createProject(name: string, description?: string): Promise<Project> {
    return this.request('/projects', 'POST', { name, description });
  }

  async getProjects(status?: string): Promise<{ projects: Project[]; total: number; page: number; page_size: number }> {
    let endpoint = '/projects';
    if (status) {
      endpoint += `?status=${encodeURIComponent(status)}`;
    }
    const data = await this.request<any>(endpoint);
    // Tolerate both array and object response shapes
    const projects: Project[] = Array.isArray(data) ? data : (data?.projects ?? []);
    const total = Array.isArray(data) ? projects.length : (typeof data?.total === 'number' ? data.total : projects.length);
    const page = typeof data?.page === 'number' ? data.page : 1;
    const page_size = typeof data?.page_size === 'number' ? data.page_size : projects.length;
    return { projects, total, page, page_size };
  }

  async getProject(projectId: number): Promise<Project> {
    return this.request(`/projects/${projectId}`);
  }

  async updateProject(projectId: number, updates: Partial<Project>): Promise<Project> {
    return this.request(`/projects/${projectId}`, 'PATCH', updates);
  }

  // Tasks API
  async createTask(
    projectId: number,
    title: string,
    description?: string,
    milestone?: string,
    priority?: number
  ): Promise<Task> {
    return this.request('/tasks', 'POST', {
      project_id: projectId,
      title,
      description,
      milestone,
      priority,
    });
  }

  async getProjectTasks(projectId: number, status?: string, milestone?: string): Promise<{ tasks: Task[]; total: number; project_id: number }> {
    let endpoint = `/tasks?project_id=${projectId}`;
    if (status) {
      endpoint += `&status=${encodeURIComponent(status)}`;
    }
    if (milestone) {
      endpoint += `&milestone=${encodeURIComponent(milestone)}`;
    }
    return this.request(endpoint);
  }

  async getTask(taskId: number): Promise<Task> {
    return this.request(`/tasks/${taskId}`);
  }

  async updateTask(taskId: number, updates: Partial<Task>): Promise<Task> {
    return this.request(`/tasks/${taskId}`, 'PATCH', updates);
  }

  // Workflows API
  async runWorkflow(projectId: number, workflowType: 'ideate' | 'plan'): Promise<WorkflowExecutionResult> {
    return this.request('/workflows/run', 'POST', {
      project_id: projectId,
      workflow_type: workflowType,
    });
  }

  async runAgent(
    agentType: string,
    projectId: number,
    userInput?: string,
    metadata?: Record<string, any>
  ): Promise<AgentExecutionResult> {
    return this.request('/workflows/agent/run', 'POST', {
      agent_type: agentType,
      project_id: projectId,
      user_input: userInput,
      metadata,
    });
  }

  // PSMP/Conflicts API
  async getProjectConflicts(projectId: number): Promise<ProjectBlock> {
    return this.request(`/workflows/conflicts/${projectId}`);
  }

  async resolveConflict(projectId: number, library: string, version: string): Promise<{ success: boolean; message: string; project_id: number }> {
    return this.request(`/workflows/conflicts/${projectId}/resolve`, 'POST', {
      library,
      version,
    });
  }

  async getProjectManifest(projectId: number): Promise<{ project_id: number; manifest: string; format: string }> {
    return this.request(`/workflows/manifest/${projectId}`);
  }

  // LLM Config API
  async listLLMProviders(): Promise<LLMProviderInfo[]> {
    const result = await this.request<{ providers: LLMProviderInfo[] }>(`/llm/providers`);
    return result.providers;
  }

  async getLLMConfig(): Promise<LLMConfigSnapshot> {
    return this.request(`/llm/config`);
  }

  async updateLLMConfig(payload: LLMConfigUpdate): Promise<{ status: string; llm_health: any }> {
    return this.request(`/llm/config`, 'POST', payload);
  }

  async chat(prompt: string, systemPrompt?: string, temperature?: number, maxTokens?: number): Promise<{
    content: string;
    provider: string;
    model: string;
    usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
  }> {
    return this.request(`/llm/chat`, 'POST', {
      prompt,
      system_prompt: systemPrompt,
      temperature,
      max_tokens: maxTokens
    });
  }

  async planTask(userInput: string): Promise<{
    objective: string;
    subtasks: Array<{
      agentType: string;
      description: string;
      priority: number;
    }>;
  }> {
    return this.request(`/llm/plan`, 'POST', { user_input: userInput });
  }

  async executeAgentTask(agentType: string, taskDescription: string, context?: string): Promise<{
    output: string;
    agent_type: string;
    provider: string;
    model: string;
  }> {
    return this.request(`/llm/execute`, 'POST', {
      agent_type: agentType,
      task_description: taskDescription,
      context
    });
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; service: string; version: string }> {
    return this.request('/health', 'GET');
  }
}

export const flyntAPI = new FlyntAPIClient();

export default flyntAPI;
