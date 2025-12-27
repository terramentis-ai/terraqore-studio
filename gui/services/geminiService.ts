
import terraqoreAPI from './terraqoreAPIService';

/**
 * MetaAgentService - Production LLM orchestration service
 * Routes all LLM requests through the backend API to support multiple providers:
 * - Online: Gemini, Groq, OpenRouter
 * - Local: Ollama (phi3, llama, etc.)
 */
export class MetaAgentService {
  /**
   * Orchestrates task breakdown using the configured LLM provider
   */
  async planTask(userInput: string) {
    try {
      const plan = await terraqoreAPI.planTask(userInput);
      return plan;
    } catch (e: any) {
      console.error("Meta Controller failed to generate orchestration plan:", e);
      console.error("Error details:", e?.message || 'Unknown error');
      console.error("Tip: Check Settings (S tab) to ensure your LLM provider is configured with a valid API key and model.");
      return null;
    }
  }

  /**
   * Executes an agent task using the configured LLM provider
   */
  async executeAgentTask(agentType: string, taskDescription: string, context?: string) {
    try {
      const result = await terraqoreAPI.executeAgentTask(agentType, taskDescription, context);
      return result.output;
    } catch (e: any) {
      console.error(`Agent execution error for ${agentType}:`, e);
      console.error("Error details:", e?.message || 'Unknown error');
      return `Execution failed for ${agentType}. Please check your LLM provider configuration in Settings.`;
    }
  }

  /**
   * Generates a minimalist SVG path string for an agent type
   * Note: This is a lightweight fallback. For production, consider using a static icon library.
   */
  async generateAgentIcon(agentType: string): Promise<string | null> {
    try {
      const response = await terraqoreAPI.chat(
        `Generate a single SVG path 'd' attribute string for a minimalist, geometric icon representing a '${agentType}'. 
        Guidelines:
        - The icon should be abstract and minimalist.
        - Coordinate system: -10 to 10.
        - Output ONLY the raw path string (e.g., "M-5,-5 L5,5..."). 
        - Do not include any tags, markdown, or explanation.`,
        undefined,
        0.7,
        100
      );
      
      const path = response.content?.trim().replace(/^"(.*)"$/, '$1');
      return path || null;
    } catch (e) {
      // Rate limiting or other errors - use fallback icons
      console.warn(`Dynamic icon generation for ${agentType} unavailable. Using fallback.`);
      return null;
    }
  }
}

export const metaAgentService = new MetaAgentService();


  /**
   * Generates a minimalist SVG path string for an agent type
   */
  async generateAgentIcon(agentType: string): Promise<string | null> {
    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const response = await ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: `Generate a single SVG path 'd' attribute string for a minimalist, geometric icon representing a '${agentType}'. 
        Guidelines:
        - The icon should be abstract and minimalist.
        - Coordinate system: -10 to 10.
        - Output ONLY the raw path string (e.g., "M-5,-5 L5,5..."). 
        - Do not include any tags, markdown, or explanation.`,
      });
      const path = response.text?.trim().replace(/^"(.*)"$/, '$1'); // Basic cleanup
      return path || null;
    } catch (e) {
      // Catch quota errors and log a warning instead of an error to keep console clean
      console.warn(`System: Dynamic icon generation for ${agentType} unavailable (Rate Limited). Fallback active.`);
      return null;
    }
  }
}

export const metaAgentService = new MetaAgentService();
