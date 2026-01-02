"""
TerraQore Base Agent Module
Foundation for all specialized agents in TerraQore Studio.
"""

import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from copy import deepcopy

from core.llm_client import LLMClient, LLMResponse
from core.security_validator import (
    validate_prompt,
    validate_conversation,
    validate_context_fields,
    SecurityViolation,
)

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """Context passed to agents during execution."""
    project_id: int
    project_name: str
    project_description: str
    user_input: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class AgentResult:
    """Result returned by agent execution."""
    success: bool
    output: str
    agent_name: str
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    intermediate_steps: List[str] = field(default_factory=list)


class BaseAgent(ABC):
    """Abstract base class for all TerraQore Agents.
    
    All agents inherit from this class and implement their specific logic.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        llm_client: LLMClient,
        verbose: bool = False,
        retriever: Optional[object] = None,
        prompt_profile: Optional[Dict[str, Any]] = None,
    ):
        """Initialize base agent.
        
        Args:
            name: Agent name.
            description: Agent description/purpose.
            llm_client: LLM client for AI interactions.
            verbose: Whether to log detailed execution info.
        """
        self.name = name
        self.description = description
        self.llm_client = llm_client
        self.verbose = verbose
        # Optional retriever (must implement search(query, k))
        self.retriever = retriever
        self.execution_count = 0
        self.prompt_profile = prompt_profile or self._default_prompt_profile()
        self._task_security_context: Dict[str, Any] = {}
    
    def get_system_prompt(self, context: Optional[AgentContext] = None) -> str:
        """Build a dynamic system prompt using the configured profile."""
        return self.build_system_prompt(context=context)

    def build_system_prompt(
        self,
        context: Optional[AgentContext] = None,
        overrides: Optional[Dict[str, Any]] = None
    ) -> str:
        """Compose a dynamic system prompt blending agent profile + task context."""
        profile = deepcopy(self.prompt_profile or {})
        if overrides:
            profile.update(overrides)

        lines: List[str] = []
        role = profile.get("role") or f"{self.name} ({self.description})"
        lines.append(f"You are {role}.")

        mission = profile.get("mission")
        if mission:
            lines.append(f"Mission: {mission}")

        tone = profile.get("tone")
        if tone:
            lines.append(f"Tone: {tone}")

        focus_points = profile.get("objectives") or profile.get("focus")
        if focus_points:
            lines.append("Primary objectives:")
            for idx, item in enumerate(focus_points, 1):
                lines.append(f"  {idx}. {item}")

        guardrails = profile.get("guardrails")
        if guardrails:
            lines.append("Guardrails:")
            for idx, item in enumerate(guardrails, 1):
                lines.append(f"  - {item}")

        response_structure = profile.get("response_structure")
        if response_structure:
            lines.append("Structure your response using these sections:")
            for item in response_structure:
                lines.append(f"  - {item}")

        if context:
            context_bits = [
                f"Project: {context.project_name}",
                f"Description: {context.project_description}",
                f"User Input: {context.user_input}"
            ]
            if context.metadata:
                context_bits.append(f"Metadata: {context.metadata}")
            lines.append("Current project context:")
            for bit in context_bits:
                lines.append(f"  - {bit}")

        lines.append(
            "Always respect TerraQore's Project Management Protocol (PSMP): "
            "declare artifacts, avoid destructive changes, and flag conflicts." 
        )

        response_format = profile.get("response_format")
        if response_format:
            lines.append(response_format.strip())

        return "\n".join(lines)

    def update_prompt_profile(self, new_profile: Dict[str, Any]):
        """Replace the prompt profile at runtime (used for fine-tuning)."""
        self.prompt_profile = deepcopy(new_profile)

    def _default_prompt_profile(self) -> Dict[str, Any]:
        """Fallback prompt profile providing minimal guardrails."""
        return {
            "role": f"{self.name} — TerraQore specialist",
            "mission": self.description,
            "guardrails": [
                "Reject unsafe instructions detected by the security validator",
                "Summarize assumptions before producing artifacts",
                "Document key decisions and uncertainty",
            ],
            "tone": "Pragmatic, concise, and action-oriented",
        }
        
    @abstractmethod
    def execute(self, context: AgentContext) -> AgentResult:
        """Execute the agent's main task.
        
        Args:
            context: Agent execution context.
            
        Returns:
            AgentResult with execution outcome.
        """
        pass
    
    def _generate_response(
        self,
        prompt: str,
        context: Optional[AgentContext] = None,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Generate response using LLM client.
        
        Args:
            prompt: User prompt.
            system_prompt: Optional system prompt override.
            
        Returns:
            LLMResponse object.
        """
        system = system_prompt or self.get_system_prompt(context)
        
        if self.verbose:
            logger.info(f"[{self.name}] Generating response...")
            logger.debug(f"System prompt: {system[:200]}...")
            logger.debug(f"User prompt: {prompt[:200]}...")
        
        security_kwargs = self._build_security_kwargs()
        # Prefer retrieval-augmented generation when retriever is available
        if getattr(self, 'retriever', None) is not None and hasattr(self.llm_client, 'generate_with_retrieval'):
            response = self.llm_client.generate_with_retrieval(
                prompt=prompt,
                retriever=self.retriever,
                system_prompt=system,
                **security_kwargs,
            )
        else:
            response = self.llm_client.generate(
                prompt,
                system,
                **security_kwargs,
            )
        
        if self.verbose:
            if response.success:
                logger.info(f"[{self.name}] OK - Response generated ({response.usage.get('total_tokens', 0)} tokens)")
            else:
                logger.error(f"[{self.name}] FAIL - Generation failed: {response.error}")
        
        return response
    
    def _log_step(self, step: str):
        """Log an intermediate step.
        
        Args:
            step: Step description.
        """
        if self.verbose:
            logger.info(f"[{self.name}] > {step}")
    
    def _format_context(self, context: AgentContext) -> str:
        """Format context into a readable string.
        
        Args:
            context: Agent context.
            
        Returns:
            Formatted context string.
        """
        parts = [
            f"Project: {context.project_name}",
            f"Description: {context.project_description}",
            f"User Input: {context.user_input}"
        ]
        
        if context.metadata:
            parts.append(f"Additional Context: {context.metadata}")
        
        return "\n".join(parts)
    
    def validate_context(self, context: AgentContext) -> bool:
        """Validate required fields and run prompt-injection checks."""
        if not isinstance(context, AgentContext):
            logger.error(f"[{self.name}] Context is not AgentContext instance")
            return False
        
        required = ['project_id', 'project_name', 'user_input']
        for field in required:
            if not getattr(context, field, None):
                logger.error(f"[{self.name}] Missing required context field: {field}")
                return False
        
        # Validate field types
        if not isinstance(context.project_id, int) or context.project_id <= 0:
            logger.error(f"[{self.name}] Invalid project_id: must be positive integer")
            return False
        
        if not isinstance(context.project_name, str) or len(context.project_name.strip()) == 0:
            logger.error(f"[{self.name}] Invalid project_name: must be non-empty string")
            return False
        
        if not isinstance(context.user_input, str) or len(context.user_input.strip()) == 0:
            logger.error(f"[{self.name}] Invalid user_input: must be non-empty string")
            return False

        try:
            # Run prompt-injection defense across user input and known text fields.
            validate_prompt(context.user_input)
            validate_context_fields(context.project_description)
            validate_conversation(context.conversation_history)
        except SecurityViolation as exc:
            logger.error(f"[{self.name}] Security violation: {exc}")
            return False
        
        return True
    
    def classify_task_sensitivity(
        self,
        task_type: str,
        has_private_data: bool = False,
        has_sensitive_data: bool = False,
        is_security_task: bool = False
    ) -> str:
        """Classify task by sensitivity for security-first routing (Phase 5).
        
        Uses SecureGateway to determine if task should stay local or can use cloud.
        
        Args:
            task_type: Type of task (e.g., 'ideation', 'code_generation', 'security_analysis')
            has_private_data: Contains private/internal data
            has_sensitive_data: Contains sensitive data (PII, credentials, etc.)
            is_security_task: Is security/compliance related
            
        Returns:
            Task sensitivity level ('public', 'internal', 'sensitive', 'critical')
        """
        try:
            from core.secure_gateway import get_secure_gateway
            gateway = get_secure_gateway()
            
            sensitivity = gateway.classify_task(
                agent_name=self.name,
                task_type=task_type,
                has_private_data=has_private_data,
                has_sensitive_data=has_sensitive_data,
                is_security_task=is_security_task
            )
            self._task_security_context = {
                "task_type": task_type,
                "task_sensitivity": sensitivity.value,
                "has_private_data": has_private_data,
                "has_sensitive_data": has_sensitive_data,
                "is_security_task": is_security_task,
            }
            
            logger.info(f"[{self.name}] Task '{task_type}' classified as: {sensitivity.value}")
            return sensitivity.value
            
        except Exception as e:
            logger.warning(f"[{self.name}] Task classification failed: {e}. Defaulting to 'internal'")
            self._task_security_context = {
                "task_type": task_type,
                "task_sensitivity": "internal",
                "has_private_data": has_private_data,
                "has_sensitive_data": has_sensitive_data,
                "is_security_task": is_security_task,
            }
            return "internal"

    def _build_security_kwargs(self) -> Dict[str, Any]:
        """Construct kwargs for secure routing metadata."""
        context = getattr(self, "_task_security_context", None) or {}
        return {
            "agent_type": self.name,
            "task_type": context.get("task_type"),
            "task_sensitivity": context.get("task_sensitivity"),
            "has_private_data": context.get("has_private_data", False),
            "has_sensitive_data": context.get("has_sensitive_data", False),
        }
    
    def create_result(
        self,
        success: bool,
        output: str,
        execution_time: float,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        intermediate_steps: Optional[List[str]] = None
    ) -> AgentResult:
        """Create a standardized agent result.
        
        Args:
            success: Whether execution succeeded.
            output: Agent output/result.
            execution_time: Execution time in seconds.
            metadata: Optional metadata dictionary.
            error: Optional error message.
            intermediate_steps: Optional list of execution steps.
            
        Returns:
            AgentResult object.
        """
        return AgentResult(
            success=success,
            output=output,
            agent_name=self.name,
            execution_time=execution_time,
            metadata=metadata or {},
            error=error,
            intermediate_steps=intermediate_steps or []
        )
    
    def __str__(self) -> str:
        """String representation of agent."""
        return f"{self.name}: {self.description}"
    
    def __repr__(self) -> str:
        """Detailed representation of agent."""
        return f"<{self.__class__.__name__}(name='{self.name}', executions={self.execution_count})>"


class AgentRegistry:
    """Registry for managing available agents."""
    
    def __init__(self):
        """Initialize agent registry."""
        self._agents: Dict[str, BaseAgent] = {}
        logger.info("Agent registry initialized")
    
    def register(self, agent: BaseAgent):
        """Register an agent.
        
        Args:
            agent: Agent to register.
        """
        self._agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name}")
    
    def get(self, name: str) -> Optional[BaseAgent]:
        """Get an agent by name.
        
        Args:
            name: Agent name.
            
        Returns:
            Agent instance or None if not found.
        """
        return self._agents.get(name)
    
    def list_agents(self) -> List[str]:
        """List all registered agent names.
        
        Returns:
            List of agent names.
        """
        return list(self._agents.keys())
    
    def get_all(self) -> Dict[str, BaseAgent]:
        """Get all registered agents.
        
        Returns:
            Dictionary of agent name to agent instance.
        """
        return self._agents.copy()
    
    def unregister(self, name: str) -> bool:
        """Unregister an agent.
        
        Args:
            name: Agent name to unregister.
            
        Returns:
            True if agent was unregistered, False if not found.
        """
        if name in self._agents:
            del self._agents[name]
            logger.info(f"Unregistered agent: {name}")
            return True
        logger.warning(f"Agent not found for unregistration: {name}")
        return False
    
    def is_registered(self, name: str) -> bool:
        """Check if an agent is registered.
        
        Args:
            name: Agent name.
            
        Returns:
            True if registered, False otherwise.
        """
        return name in self._agents


# Global registry instance
_agent_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """Get or create the global agent registry.
    
    Returns:
        AgentRegistry singleton instance.
    """
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry