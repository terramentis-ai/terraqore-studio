"""
TerraQore Agent Orchestrator
Coordinates agent execution and workflow management.
"""

import logging
import time
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime

from agents.base import BaseAgent, AgentContext, AgentResult, get_agent_registry
from agents.idea_agent import IdeaAgent
from core.llm_client import LLMClient, create_llm_client_from_config
from core.config import get_config_manager
from core.rag_service import get_default_store
from core.state import get_state_manager, Task, TaskStatus, ProjectStatus
from core.collaboration_state import (
    get_collaboration_state_manager,
    AgentIteration,
    AgentFeedback,
    IterationType,
    FeedbackSeverity
)
from core.build_data_collector import (
    get_build_data_collector,
    BuildStage,
    MetricType
)
from core.psmp import ProjectBlockedException
from core.psmp_orchestrator_bridge import get_psmp_bridge

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates agent execution and manages workflows."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize orchestrator.
        
        Args:
            llm_client: Optional LLM client. If None, creates from config.
        """
        if llm_client is None:
            config_mgr = get_config_manager()
            config = config_mgr.load()
            llm_client = create_llm_client_from_config(config)
        
        self.llm_client = llm_client
        self.state_mgr = get_state_manager()
        self.collaboration_mgr = get_collaboration_state_manager()
        self.build_collector = get_build_data_collector()
        self.agent_registry = get_agent_registry()
        self.psmp_bridge = get_psmp_bridge()  # PSMP state management
        
        # Register available agents
        self._register_agents()
        
        logger.info("Agent orchestrator initialized")
    
    def _register_agents(self):
        """Register all available agents."""
        # Create shared retriever for agents
        retriever = get_default_store()
        # Register Idea Agent
        idea_agent = IdeaAgent(self.llm_client, verbose=True, retriever=retriever)
        self.agent_registry.register(idea_agent)
        
        # Register Idea Validator Agent
        from agents.idea_validator_agent import IdeaValidatorAgent
        idea_validator = IdeaValidatorAgent(self.llm_client, verbose=True, retriever=retriever)
        self.agent_registry.register(idea_validator)
        
        # Register Planner Agent
        from agents.planner_agent import PlannerAgent
        planner_agent = PlannerAgent(self.llm_client, verbose=True, retriever=retriever)
        self.agent_registry.register(planner_agent)
        
        # Register Coder Agent
        from agents.coder_agent import CoderAgent
        coder_agent = CoderAgent(self.llm_client, verbose=True, retriever=retriever)
        self.agent_registry.register(coder_agent)
        
        # Register Code Validator Agent
        from agents.code_validator_agent import CodeValidationAgent
        code_validator = CodeValidationAgent(self.llm_client, verbose=True, retriever=retriever)
        self.agent_registry.register(code_validator)
        
        # Register Security Agent
        from agents.security_agent import SecurityVulnerabilityAgent
        security_agent = SecurityVulnerabilityAgent(self.llm_client, verbose=True, retriever=retriever)
        self.agent_registry.register(security_agent)
        
        # Register Notebook Agent
        from agents.notebook_agent import NotebookAgent
        notebook_agent = NotebookAgent(self.llm_client, verbose=True, retriever=retriever)
        self.agent_registry.register(notebook_agent)
        
        # Register Conflict Resolver Agent (PSMP)
        from agents.conflict_resolver_agent import ConflictResolverAgent
        conflict_resolver = ConflictResolverAgent(self.llm_client, verbose=True, retriever=retriever)
        self.agent_registry.register(conflict_resolver)
        
        # Register Test Critique Agent
        from agents.test_critique_agent import TestCritiqueAgent
        test_critique = TestCritiqueAgent(self.llm_client, verbose=True, retriever=retriever)
        self.agent_registry.register(test_critique)
        
        logger.info(f"Registered {len(self.agent_registry.list_agents())} agents")
    
    def run_ideation(
        self,
        project_id: int,
        user_input: Optional[str] = None
    ) -> AgentResult:
        """Run ideation workflow for a project.
        
        Args:
            project_id: Project ID.
            user_input: Optional additional user input/guidance.
            
        Returns:
            AgentResult from ideation.
        """
        logger.info(f"Starting ideation for project {project_id}")
        
        # Get project
        project = self.state_mgr.get_project(project_id=project_id)
        if not project:
            logger.error(f"Project {project_id} not found")
            return AgentResult(
                success=False,
                output="",
                agent_name="orchestrator",
                execution_time=0.0,
                error="Project not found"
            )
        
        # Update project status
        self.state_mgr.update_project(
            project_id,
            status=ProjectStatus.PLANNING.value
        )
        
        # Create task
        task = Task(
            project_id=project_id,
            title="Ideation & Research",
            description="Research trends and generate project variations",
            status=TaskStatus.IN_PROGRESS.value,
            agent_type="IdeaAgent"
        )
        task_id = self.state_mgr.create_task(task)
        
        # Create context
        context = AgentContext(
            project_id=project_id,
            project_name=project.name,
            project_description=project.description,
            user_input=user_input or "Generate creative project ideas based on the project description."
        )
        
        # Get and execute Idea Agent
        idea_agent = self.agent_registry.get("IdeaAgent")
        if not idea_agent:
            error_msg = "Idea Agent not available"
            logger.error(error_msg)
            
            self.state_mgr.update_task(
                task_id,
                status=TaskStatus.FAILED.value,
                result=error_msg
            )
            
            return AgentResult(
                success=False,
                output="",
                agent_name="orchestrator",
                execution_time=0.0,
                error=error_msg
            )
        
        # Execute agent
        logger.info(f"Executing {idea_agent.name}")
        result = idea_agent.execute(context)
        
        # Update task with result
        if result.success:
            self.state_mgr.update_task(
                task_id,
                status=TaskStatus.COMPLETED.value,
                result=result.output,
                completed_at=datetime.now().isoformat(),
                metadata=result.metadata
            )
            logger.info(f"Ideation completed successfully")
        else:
            self.state_mgr.update_task(
                task_id,
                status=TaskStatus.FAILED.value,
                result=result.error or "Unknown error"
            )
            logger.error(f"Ideation failed: {result.error}")
        
        return result
    
    def run_planning(
        self,
        project_id: int,
        user_input: Optional[str] = None
    ) -> AgentResult:
        """Run planning workflow for a project.
        
        Args:
            project_id: Project ID.
            user_input: Optional additional user input/guidance.
            
        Returns:
            AgentResult from planning.
        """
        logger.info(f"Starting planning for project {project_id}")
        
        # Get project
        project = self.state_mgr.get_project(project_id=project_id)
        if not project:
            logger.error(f"Project {project_id} not found")
            return AgentResult(
                success=False,
                output="",
                agent_name="orchestrator",
                execution_time=0.0,
                error="Project not found"
            )
        
        # Update project status
        self.state_mgr.update_project(
            project_id,
            status=ProjectStatus.IN_PROGRESS.value
        )
        
        # Create planning task
        task = Task(
            project_id=project_id,
            title="Project Planning & Task Breakdown",
            description="Break project into actionable tasks with dependencies",
            status=TaskStatus.IN_PROGRESS.value,
            agent_type="PlannerAgent"
        )
        task_id = self.state_mgr.create_task(task)
        
        # Create context
        context = AgentContext(
            project_id=project_id,
            project_name=project.name,
            project_description=project.description,
            user_input=user_input or "Break this project into concrete, actionable tasks with clear dependencies."
        )
        
        # Get and execute Planner Agent
        planner_agent = self.agent_registry.get("PlannerAgent")
        if not planner_agent:
            error_msg = "Planner Agent not available"
            logger.error(error_msg)
            
            self.state_mgr.update_task(
                task_id,
                status=TaskStatus.FAILED.value,
                result=error_msg
            )
            
            return AgentResult(
                success=False,
                output="",
                agent_name="orchestrator",
                execution_time=0.0,
                error=error_msg
            )
        
        # Execute agent
        logger.info(f"Executing {planner_agent.name}")
        result = planner_agent.execute(context)
        
        # Update task with result
        if result.success:
            self.state_mgr.update_task(
                task_id,
                status=TaskStatus.COMPLETED.value,
                result=result.output,
                completed_at=datetime.now().isoformat(),
                metadata=result.metadata
            )
            logger.info(f"Planning completed successfully")
        else:
            self.state_mgr.update_task(
                task_id,
                status=TaskStatus.FAILED.value,
                result=result.error or "Unknown error"
            )
            logger.error(f"Planning failed: {result.error}")
        
        return result
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all registered agents.
        
        Returns:
            Dictionary with agent status information.
        """
        agents = self.agent_registry.get_all()
        
        status = {
            "total_agents": len(agents),
            "agents": {}
        }
        
        for name, agent in agents.items():
            status["agents"][name] = {
                "name": agent.name,
                "description": agent.description,
                "executions": agent.execution_count
            }
        
        return status
    
    def run_agent(
        self,
        agent_name: str,
        context: AgentContext
    ) -> AgentResult:
        """Run a specific agent with given context.
        
        Args:
            agent_name: Name of agent to run.
            context: Execution context.
            
        Returns:
            AgentResult from execution.
        """
        # Check if project is blocked (PSMP enforcement)
        if context.project_id:
            is_blocked, reason = self.psmp_bridge.check_project_blocked(context.project_id)
            if is_blocked:
                error_msg = f"Cannot execute agent: {reason}"
                logger.warning(error_msg)
                # Return blocking report to user
                report = self.psmp_bridge.get_blocking_report(context.project_id)
                return AgentResult(
                    success=False,
                    output=report,
                    agent_name="orchestrator",
                    execution_time=0.0,
                    error=error_msg
                )
        
        agent = self.agent_registry.get(agent_name)
        
        if not agent:
            return AgentResult(
                success=False,
                output="",
                agent_name="orchestrator",
                execution_time=0.0,
                error=f"Agent '{agent_name}' not found"
            )
        
        logger.info(f"Running agent: {agent_name}")
        result = agent.execute(context)
        logger.info(f"Agent {agent_name} completed: success={result.success}")
        
        # Declare artifact with PSMP (mandatory artifact declaration)
        if result.success and context.project_id:
            try:
                success, conflicts = self.psmp_bridge.declare_agent_artifact(
                    project_id=context.project_id,
                    agent_name=agent_name,
                    artifact_type=self._get_artifact_type_from_agent(agent_name),
                    result=result
                )
                
                if not success and conflicts:
                    # Project is now BLOCKED due to conflicts
                    logger.warning(f"Artifact declared but conflicts detected: {len(conflicts)} conflict(s)")
                    report = self.psmp_bridge.get_blocking_report(context.project_id)
                    # Update result to include blocking information
                    result.output += "\n\n" + report
                    result.error = "Project blocked due to dependency conflicts"
                    
            except ProjectBlockedException as e:
                logger.error(f"Cannot declare artifact: {e}")
                result.success = False
                result.error = str(e)
                result.output += f"\n\nError: {e}"
        
        return result
    
    def _get_artifact_type_from_agent(self, agent_name: str) -> str:
        """Determine artifact type based on agent name.
        
        Args:
            agent_name: Name of the agent.
            
        Returns:
            Artifact type string.
        """
        artifact_types = {
            "IdeaAgent": "idea",
            "IdeaValidatorAgent": "idea_validation",
            "PlannerAgent": "plan",
            "CoderAgent": "code",
            "CodeValidationAgent": "code_validation",
            "SecurityVulnerabilityAgent": "security_analysis",
            "NotebookAgent": "notebook",
            "DataScienceAgent": "data_science",
            "MLOpsAgent": "mlops",
            "ConflictResolverAgent": "conflict_resolution",
            "TestCritiqueAgent": "test_critique",
        }
        return artifact_types.get(agent_name, "unknown")
    
    def validate_idea(
        self,
        project_id: int,
        context: AgentContext
    ) -> tuple[bool, AgentResult]:
        """Validate project idea for feasibility.
        
        Args:
            project_id: Project ID.
            context: Execution context with idea details.
            
        Returns:
            Tuple of (validation_passed, result).
        """
        logger.info(f"Validating idea for project {project_id}")
        
        task = Task(
            project_id=project_id,
            title="Idea Validation & Feasibility Assessment",
            description="Validate idea feasibility and identify risks",
            status=TaskStatus.IN_PROGRESS.value,
            agent_type="IdeaValidatorAgent"
        )
        task_id = self.state_mgr.create_task(task)
        
        validator = self.agent_registry.get("IdeaValidatorAgent")
        if not validator:
            error_msg = "Idea Validator Agent not available"
            logger.error(error_msg)
            self.state_mgr.update_task(
                task_id,
                status=TaskStatus.FAILED.value,
                result=error_msg
            )
            return False, AgentResult(
                success=False,
                output="",
                agent_name="orchestrator",
                execution_time=0.0,
                error=error_msg
            )
        
        logger.info("Executing IdeaValidatorAgent")
        result = validator.execute(context)
        
        if result.success:
            self.state_mgr.update_task(
                task_id,
                status=TaskStatus.COMPLETED.value,
                result=result.output,
                completed_at=datetime.now().isoformat(),
                metadata=result.metadata
            )
            logger.info("Idea validation passed")
            # Check if feasibility score is acceptable (>= 5/10)
            validation_passed = True
            if result.metadata and "feasibility_score" in result.metadata:
                score = result.metadata.get("feasibility_score", {}).get("overall_score", 5)
                validation_passed = score >= 5.0
            return validation_passed, result
        else:
            self.state_mgr.update_task(
                task_id,
                status=TaskStatus.FAILED.value,
                result=result.error or "Validation failed"
            )
            logger.error(f"Idea validation failed: {result.error}")
            return False, result
    
    def validate_code(
        self,
        project_id: int,
        context: AgentContext
    ) -> tuple[bool, AgentResult]:
        """Validate generated code quality.
        
        Args:
            project_id: Project ID.
            context: Execution context with generated code.
            
        Returns:
            Tuple of (validation_passed, result).
        """
        logger.info(f"Validating code quality for project {project_id}")
        
        task = Task(
            project_id=project_id,
            title="Code Quality Validation",
            description="Validate code quality, type hints, and best practices",
            status=TaskStatus.IN_PROGRESS.value,
            agent_type="CodeValidationAgent"
        )
        task_id = self.state_mgr.create_task(task)
        
        validator = self.agent_registry.get("CodeValidationAgent")
        if not validator:
            error_msg = "Code Validator Agent not available"
            logger.error(error_msg)
            self.state_mgr.update_task(
                task_id,
                status=TaskStatus.FAILED.value,
                result=error_msg
            )
            return False, AgentResult(
                success=False,
                output="",
                agent_name="orchestrator",
                execution_time=0.0,
                error=error_msg
            )
        
        logger.info("Executing CodeValidationAgent")
        result = validator.execute(context)
        
        if result.success:
            self.state_mgr.update_task(
                task_id,
                status=TaskStatus.COMPLETED.value,
                result=result.output,
                completed_at=datetime.now().isoformat(),
                metadata=result.metadata
            )
            logger.info("Code validation passed")
            # Check if quality score is acceptable (>= 6/10)
            validation_passed = True
            if result.metadata and "overall_score" in result.metadata:
                score = result.metadata.get("overall_score", 6)
                validation_passed = score >= 6.0
            return validation_passed, result
        else:
            self.state_mgr.update_task(
                task_id,
                status=TaskStatus.FAILED.value,
                result=result.error or "Validation failed"
            )
            logger.error(f"Code validation failed: {result.error}")
            return False, result
    
    def scan_security(
        self,
        project_id: int,
        context: AgentContext
    ) -> tuple[bool, AgentResult]:
        """Scan code for security vulnerabilities.
        
        Args:
            project_id: Project ID.
            context: Execution context with code to scan.
            
        Returns:
            Tuple of (scan_passed, result).
        """
        logger.info(f"Scanning security for project {project_id}")
        
        task = Task(
            project_id=project_id,
            title="Security Vulnerability Scan",
            description="Scan for hardcoded credentials, injection attacks, vulnerable dependencies",
            status=TaskStatus.IN_PROGRESS.value,
            agent_type="SecurityVulnerabilityAgent"
        )
        task_id = self.state_mgr.create_task(task)
        
        scanner = self.agent_registry.get("SecurityVulnerabilityAgent")
        if not scanner:
            error_msg = "Security Agent not available"
            logger.error(error_msg)
            self.state_mgr.update_task(
                task_id,
                status=TaskStatus.FAILED.value,
                result=error_msg
            )
            return False, AgentResult(
                success=False,
                output="",
                agent_name="orchestrator",
                execution_time=0.0,
                error=error_msg
            )
        
        logger.info("Executing SecurityVulnerabilityAgent")
        result = scanner.execute(context)
        
        if result.success:
            self.state_mgr.update_task(
                task_id,
                status=TaskStatus.COMPLETED.value,
                result=result.output,
                completed_at=datetime.now().isoformat(),
                metadata=result.metadata
            )
            logger.info("Security scan completed")
            # Fail if critical vulnerabilities found
            scan_passed = True
            if result.metadata and "critical_count" in result.metadata:
                critical_count = result.metadata.get("critical_count", 0)
                scan_passed = critical_count == 0
            return scan_passed, result
        else:
            self.state_mgr.update_task(
                task_id,
                status=TaskStatus.FAILED.value,
                result=result.error or "Security scan failed"
            )
            logger.error(f"Security scan failed: {result.error}")
            return False, result
    
    def run_full_workflow(
        self,
        project_id: int,
        user_input: Optional[str] = None
    ) -> Dict[str, AgentResult]:
        """Run complete workflow: ideate → validate → plan → code → validate → security scan.
        
        Args:
            project_id: Project ID.
            user_input: Optional user guidance.
            
        Returns:
            Dictionary with results from each stage.
        """
        logger.info(f"Starting full workflow for project {project_id}")
        results = {}
        
        # Get project
        project = self.state_mgr.get_project(project_id=project_id)
        if not project:
            logger.error(f"Project {project_id} not found")
            return results
        
        # Stage 1: Ideation
        logger.info("=== STAGE 1: IDEATION ===")
        context = AgentContext(
            project_id=project_id,
            project_name=project.name,
            project_description=project.description,
            user_input=user_input or "Generate project ideas and variations"
        )
        results["ideation"] = self.run_ideation(project_id, user_input)
        
        # Stage 2: Idea Validation
        logger.info("=== STAGE 2: IDEA VALIDATION ===")
        context.user_input = results["ideation"].output
        validation_passed, results["idea_validation"] = self.validate_idea(project_id, context)
        
        if not validation_passed:
            logger.warning("Idea validation failed - stopping workflow")
            self.state_mgr.update_project(
                project_id,
                status=ProjectStatus.FAILED.value
            )
            return results
        
        # Stage 3: Planning
        logger.info("=== STAGE 3: PLANNING ===")
        context.user_input = "Create detailed project plan based on validated idea"
        results["planning"] = self.run_planning(project_id, "Create detailed project plan")
        
        # Stage 4: Code Generation
        logger.info("=== STAGE 4: CODE GENERATION ===")
        coder = self.agent_registry.get("CoderAgent")
        if coder:
            context.user_input = results["planning"].output
            results["code_generation"] = coder.execute(context)
        
        # Stage 5: Code Validation
        logger.info("=== STAGE 5: CODE VALIDATION ===")
        code_validation_passed, results["code_validation"] = self.validate_code(project_id, context)
        
        if not code_validation_passed:
            logger.warning("Code validation failed - stopping before security scan")
            # Continue to security scan anyway for visibility
        
        # Stage 6: Security Scan
        logger.info("=== STAGE 6: SECURITY SCAN ===")
        security_passed, results["security_scan"] = self.scan_security(project_id, context)
        
        if not security_passed:
            logger.warning("Security scan found critical vulnerabilities - stopping deployment")
            self.state_mgr.update_project(
                project_id,
                status=ProjectStatus.FAILED.value
            )
            return results
        
        # All stages passed
        logger.info("=== WORKFLOW COMPLETE ===")
        logger.info("All validation gates passed - project ready for deployment")
        self.state_mgr.update_project(
            project_id,
            status=ProjectStatus.COMPLETED.value
        )
        
        return results

    def track_agent_iteration(
        self,
        project_id: int,
        agent_name: str,
        iteration_type: str,
        input_context: Dict[str, Any],
        output_result: Dict[str, Any],
        quality_score: float,
        validation_passed: bool,
        execution_time: float
    ) -> int:
        """Track an agent iteration in collaboration state and database.
        
        Args:
            project_id: Project ID.
            agent_name: Name of the agent.
            iteration_type: Type of iteration (generation, validation, etc).
            input_context: Input context for iteration.
            output_result: Output result.
            quality_score: Quality score (0-10).
            validation_passed: Whether validation passed.
            execution_time: Execution time in seconds.
            
        Returns:
            Iteration ID.
        """
        # Ensure collaboration state exists
        collab_state = self.collaboration_mgr.get_project_state(project_id)
        if not collab_state:
            self.collaboration_mgr.create_project_state(project_id)
            collab_state = self.collaboration_mgr.get_project_state(project_id)
        
        # Get next iteration number
        iterations = collab_state.agent_iterations.get(agent_name, [])
        iteration_number = len(iterations) + 1
        
        # Create iteration object
        iteration = AgentIteration(
            project_id=project_id,
            agent_name=agent_name,
            iteration_number=iteration_number,
            iteration_type=IterationType[iteration_type.upper()],
            input_context=input_context,
            output_result=output_result,
            quality_score=quality_score,
            validation_passed=validation_passed,
            feedback_received=[],
            timestamp=datetime.now().isoformat(),
            execution_time=execution_time
        )
        
        # Store in collaboration state
        self.collaboration_mgr.add_iteration(project_id, iteration)
        
        # Store in database
        iteration_id = self.state_mgr.store_agent_iteration(
            project_id=project_id,
            agent_name=agent_name,
            iteration_number=iteration_number,
            iteration_type=iteration_type,
            input_context=input_context,
            output_result=output_result,
            quality_score=quality_score,
            validation_passed=validation_passed,
            execution_time=execution_time
        )
        
        logger.info(
            f"Tracked iteration for {agent_name}: "
            f"#{iteration_number}, score={quality_score:.1f}/10"
        )
        
        return iteration_id
    
    def send_agent_feedback(
        self,
        project_id: int,
        source_agent: str,
        target_agent: str,
        feedback_type: str,
        message: str,
        severity: str,
        suggestions: List[str],
        iteration_number: Optional[int] = None
    ) -> int:
        """Send feedback from one agent to another.
        
        Args:
            project_id: Project ID.
            source_agent: Agent providing feedback.
            target_agent: Agent receiving feedback.
            feedback_type: Type of feedback (improvement, blocker, suggestion, etc).
            message: Feedback message.
            severity: Severity level (info, warning, error, critical).
            suggestions: List of suggestions.
            iteration_number: Optional target iteration number.
            
        Returns:
            Feedback ID.
        """
        # Create feedback object
        feedback = AgentFeedback(
            source_agent=source_agent,
            target_agent=target_agent,
            feedback_type=feedback_type,
            message=message,
            severity=FeedbackSeverity[severity.upper()],
            suggestions=suggestions,
            timestamp=datetime.now().isoformat(),
            iteration_number=iteration_number or 0
        )
        
        # Store in collaboration state
        self.collaboration_mgr.add_feedback(project_id, feedback)
        
        # Store in database
        feedback_id = self.state_mgr.store_feedback(
            project_id=project_id,
            source_agent=source_agent,
            target_agent=target_agent,
            feedback_type=feedback_type,
            message=message,
            severity=severity,
            suggestions=suggestions,
            iteration_number=iteration_number
        )
        
        logger.info(
            f"Feedback from {source_agent} to {target_agent} "
            f"({severity}): {message[:50]}..."
        )
        
        return feedback_id
    
    def get_collaboration_summary(self, project_id: int) -> Dict[str, Any]:
        """Get collaboration summary for a project.
        
        Args:
            project_id: Project ID.
            
        Returns:
            Collaboration summary.
        """
        summary = self.collaboration_mgr.get_project_summary(project_id)
        
        if summary:
            logger.info(
                f"Project {project_id}: {summary['total_iterations']} iterations, "
                f"{summary['feedback_count']} feedback messages"
            )
        
        return summary
    
    def should_iterate_agent(
        self,
        project_id: int,
        agent_name: str,
        min_quality: float = 6.0
    ) -> bool:
        """Determine if an agent should iterate again.
        
        Args:
            project_id: Project ID.
            agent_name: Agent name.
            min_quality: Minimum quality threshold.
            
        Returns:
            True if agent should iterate again.
        """
        collab_state = self.collaboration_mgr.get_project_state(project_id)
        if not collab_state:
            return True
        
        return collab_state.should_iterate_again(agent_name, min_quality)

    def list_available_agents(self) -> list[str]:
        """List all available agents.
        
        Returns:
            List of agent names.
        """
        return self.agent_registry.list_agents()
    
    # Build Data Collection Methods (Phase 5.2+)
    
    def start_build_session(self, build_id: str, project_id: int) -> None:
        """Start a new build data collection session.
        
        Args:
            build_id: Unique build identifier
            project_id: Associated project ID
        """
        self.build_collector.start_build(build_id, project_id)
        logger.info(f"Build session started: {build_id}")
    
    def record_stage_execution(
        self,
        build_id: str,
        project_id: int,
        stage: str,
        status: str,
        agent_name: Optional[str] = None,
        duration: Optional[float] = None,
        metrics: Optional[Dict[str, Any]] = None,
        issues: Optional[List[str]] = None,
        decisions: Optional[List[str]] = None
    ) -> None:
        """Record a stage execution for build data.
        
        Args:
            build_id: Build session ID
            project_id: Project ID
            stage: Stage name
            status: Execution status
            agent_name: Agent involved
            duration: Execution time
            metrics: Stage metrics
            issues: Issues encountered
            decisions: Decisions made
        """
        self.build_collector.record_stage(
            build_id=build_id,
            project_id=project_id,
            stage=stage,
            status=status,
            agent_involved=agent_name,
            metrics=metrics or {},
            issues=issues or [],
            decisions=decisions or [],
            duration_seconds=duration
        )
    
    def record_execution_metric(
        self,
        build_id: str,
        project_id: int,
        metric_type: str,
        value: float,
        stage: str,
        agent_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record execution metric for build data.
        
        Args:
            build_id: Build session ID
            project_id: Project ID
            metric_type: Type of metric
            value: Metric value
            stage: Current stage
            agent_name: Agent name
            context: Additional context
        """
        self.build_collector.record_metric(
            build_id=build_id,
            project_id=project_id,
            metric_type=metric_type,
            value=value,
            stage=stage,
            agent_name=agent_name,
            context=context
        )
    
    def record_build_error(
        self,
        build_id: str,
        project_id: int,
        stage: str,
        error_type: str,
        error_message: str,
        agent_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record error during build for diagnostics.
        
        Args:
            build_id: Build session ID
            project_id: Project ID
            stage: Stage where error occurred
            error_type: Error type classification
            error_message: Error message
            agent_name: Agent involved
            context: Additional context
        """
        self.build_collector.record_error(
            build_id=build_id,
            project_id=project_id,
            stage=stage,
            error_type=error_type,
            error_message=error_message,
            agent_name=agent_name,
            context=context
        )
    
    def save_test_data(
        self,
        build_id: str,
        project_id: int,
        snapshot_type: str,
        stage: str,
        data: Dict[str, Any]
    ) -> None:
        """Save test data snapshot for later use in testing.
        
        Args:
            build_id: Build session ID
            project_id: Project ID
            snapshot_type: Type of data being saved
            stage: Associated stage
            data: Data to snapshot
        """
        self.build_collector.save_test_snapshot(
            build_id=build_id,
            project_id=project_id,
            snapshot_type=snapshot_type,
            stage=stage,
            data=data
        )
    
    def end_build_session(self, build_id: str, final_status: str = "completed") -> None:
        """End build data collection session.
        
        Args:
            build_id: Build session ID
            final_status: Final status of build
        """
        self.build_collector.end_build(build_id, final_status)
        logger.info(f"Build session ended: {build_id} with status {final_status}")
    
    def get_build_report(self, build_id: str) -> Dict[str, Any]:
        """Get comprehensive build report.
        
        Args:
            build_id: Build session ID
            
        Returns:
            Build report with all collected data
        """
        summary = self.build_collector.get_build_summary(build_id)
        snapshots = self.build_collector.get_test_snapshots(build_id)
        
        return {
            "summary": summary,
            "test_data": snapshots
        }


# Singleton instance
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Get or create the global orchestrator.
    
    Returns:
        AgentOrchestrator singleton instance.
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator