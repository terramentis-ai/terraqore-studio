"""
TerraQore Planner Agent
Specialized agent for breaking down projects into actionable tasks with dependencies.
"""

import time
import logging
from typing import Dict, Any, List, Optional
import json
import re

from agents.base import BaseAgent, AgentContext, AgentResult
from core.llm_client import LLMClient
from core.state import get_state_manager, Task, TaskStatus
from core.security_validator import validate_agent_input

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """Agent specialized in project planning and task breakdown.
    
    Capabilities:
    - Break projects into concrete tasks
    - Identify task dependencies
    - Organize tasks into milestones
    - Estimate effort and prioritize
    - Create executable roadmaps
    """
    
    def __init__(self, llm_client: LLMClient, verbose: bool = True, retriever: object = None):
        """Initialize Planner Agent.
        
        Args:
            llm_client: LLM client for AI interactions.
            verbose: Whether to log detailed execution info.
        """
        super().__init__(
            name="PlannerAgent",
            description="Breaks projects into tasks with dependencies and milestones",
            llm_client=llm_client,
            verbose=verbose,
            retriever=retriever
        )
        self.state_mgr = get_state_manager()
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for Planner Agent."""
        return """You are the Planner Agent - an expert in breaking down agentic AI projects into actionable tasks.

Your role is to:
1. Analyze project goals and requirements
2. Break work into concrete, achievable tasks
3. Identify task dependencies and relationships
4. Organize tasks into logical milestones/phases
5. Estimate effort and set priorities
6. Create clear, executable roadmaps

When creating tasks:
- Be specific and actionable (not vague like "Build the app")
- Each task should be completable in 1-8 hours
- Clearly state what "done" looks like
- Identify dependencies between tasks
- Consider MVP-first approach
- Think about what can be parallelized

When organizing milestones:
- Group related tasks together
- Each milestone should deliver value
- Typical milestones: Setup, Core Features, Testing, Deployment
- Consider incremental delivery

Output Format:
Provide tasks in structured JSON format with these fields:
- title: Short, action-oriented title
- description: What needs to be done and acceptance criteria
- milestone: Which phase this belongs to
- priority: 0 (low), 1 (medium), 2 (high)
- estimated_hours: Realistic time estimate
- dependencies: List of task titles this depends on
- agent_type: Which agent should handle it (e.g., "CoderAgent", "ResearchAgent", "manual")

Be practical and realistic. Focus on getting to a working MVP."""
    
    def execute(self, context: AgentContext) -> AgentResult:
        """Execute planning workflow.
        
        Args:
            context: Agent execution context.
            
        Returns:
            AgentResult with planning output.
        """
        # Validate input for security violations before processing
        try:
            validate_agent_input(lambda self, ctx: None)(self, context)
        except Exception as e:
            logger.error(f"[{self.name}] Security validation failed: {str(e)}")
            return self.create_result(
                success=False,
                output="",
                execution_time=0,
                error=f"Security validation failed: {str(e)}"
            )
        
        start_time = time.time()
        steps = []
        
        # Validate context
        if not self.validate_context(context):
            return self.create_result(
                success=False,
                output="Invalid context provided",
                execution_time=time.time() - start_time,
                error="Missing required context fields"
            )
        
        self.execution_count += 1
        self._log_step("Starting planning workflow")
        steps.append("Planning workflow started")
        
        try:
            # Get ideation results if available
            ideation_result = self.state_mgr.get_memory(context.project_id, "ideation_result")
            
            # Step 1: Generate task breakdown
            self._log_step("Generating task breakdown")
            task_plan = self._generate_task_plan(context, ideation_result)
            steps.append("Generated task breakdown")
            
            # Step 2: Parse and validate tasks
            self._log_step("Parsing task structure")
            tasks = self._parse_tasks(task_plan)
            steps.append(f"Parsed {len(tasks)} tasks")
            
            # Step 3: Create tasks in database
            self._log_step("Creating tasks in database")
            created_count = self._create_tasks(context.project_id, tasks)
            steps.append(f"Created {created_count} tasks")
            
            # Step 4: Generate summary
            self._log_step("Generating plan summary")
            summary = self._generate_summary(context, tasks, created_count)
            steps.append("Generated summary")
            
            execution_time = time.time() - start_time
            self._log_step(f"Completed in {execution_time:.2f}s")
            
            return self.create_result(
                success=True,
                output=summary,
                execution_time=execution_time,
                metadata={
                    "tasks_created": created_count,
                    "milestones": list(set(t.get("milestone") for t in tasks if t.get("milestone"))),
                    "total_estimated_hours": sum(t.get("estimated_hours", 0) for t in tasks)
                },
                intermediate_steps=steps
            )
            
        except Exception as e:
            error_msg = f"Planning failed: {str(e)}"
            logger.error(f"[{self.name}] {error_msg}", exc_info=True)
            
            return self.create_result(
                success=False,
                output="",
                execution_time=time.time() - start_time,
                error=error_msg,
                intermediate_steps=steps
            )
    
    def _generate_task_plan(
        self, 
        context: AgentContext,
        ideation_result: Optional[str]
    ) -> str:
        """Generate task breakdown using LLM.
        
        Args:
            context: Agent context.
            ideation_result: Previous ideation output if available.
            
        Returns:
            Task plan as JSON string.
        """
        prompt = f"""Break down this project into concrete, actionable tasks:

PROJECT:
{self._format_context(context)}

"""
        
        if ideation_result:
            prompt += f"""
IDEATION RESULTS:
{ideation_result[:2000]}  # Truncate if too long

"""
        
        prompt += """
Create a detailed task breakdown with the following structure:

Return a JSON array of tasks. Each task must have:
- title: Clear, action-oriented (e.g., "Set up Python environment", "Implement user authentication")
- description: What to do and acceptance criteria (2-3 sentences)
- milestone: Phase name (e.g., "Setup", "Core Features", "Testing", "Deployment")
- priority: 0, 1, or 2 (low, medium, high)
- estimated_hours: Realistic estimate (0.5 to 8 hours per task)
- dependencies: Array of task titles that must be completed first (use exact titles)
- agent_type: "CoderAgent", "ResearchAgent", "TestAgent", or "manual"

Guidelines:
- Start with setup tasks (environment, dependencies, project structure)
- Then core feature development
- Then testing and refinement
- Finally deployment and documentation
- Break large tasks into smaller ones (max 8 hours each)
- Identify clear dependencies
- MVP-first approach (mark nice-to-haves as low priority)

Generate 10-20 tasks covering the full development lifecycle.

Return ONLY valid JSON, no other text:
"""
        
        response = self._generate_response(prompt)
        
        if response.success:
            return response.content
        else:
            raise Exception(f"Task generation failed: {response.error}")
    
    def _parse_tasks(self, task_plan: str) -> List[Dict[str, Any]]:
        """Parse task plan JSON into structured format.
        
        Args:
            task_plan: JSON string with tasks.
            
        Returns:
            List of task dictionaries.
        """
        # Try to extract JSON from response
        json_match = re.search(r'\[[\s\S]*\]', task_plan)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = task_plan
        
        # Clean up control characters that might break JSON parsing
        json_str = json_str.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        # Remove multiple spaces
        json_str = re.sub(r' +', ' ', json_str)
        
        try:
            tasks = json.loads(json_str)
            if not isinstance(tasks, list):
                raise ValueError("Expected JSON array of tasks")
            
            # Validate required fields
            required = ['title', 'description', 'milestone']
            for i, task in enumerate(tasks):
                for field in required:
                    if field not in task:
                        logger.warning(f"Task {i} missing required field: {field}")
                        task[field] = task.get(field, "Unknown")
                
                # Ensure correct types
                task['priority'] = int(task.get('priority', 1))
                task['estimated_hours'] = float(task.get('estimated_hours', 2.0))
                task['dependencies'] = task.get('dependencies', [])
                if not isinstance(task['dependencies'], list):
                    task['dependencies'] = []
                task['agent_type'] = task.get('agent_type', 'manual')
            
            logger.info(f"Successfully parsed {len(tasks)} tasks")
            return tasks
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse task JSON: {e}")
            logger.debug(f"JSON content: {json_str[:500]}")
            raise Exception("Failed to parse task breakdown. Invalid JSON format.")
    
    def _create_tasks(self, project_id: int, tasks: List[Dict[str, Any]]) -> int:
        """Create tasks in the database with dependency resolution.
        
        Args:
            project_id: Project ID.
            tasks: List of task dictionaries.
            
        Returns:
            Number of tasks created.
        """
        # Create a mapping of task titles to IDs
        title_to_id = {}
        
        # First pass: Create all tasks without dependencies
        for task_data in tasks:
            task = Task(
                project_id=project_id,
                title=task_data['title'],
                description=task_data['description'],
                status=TaskStatus.PENDING.value,
                priority=task_data['priority'],
                milestone=task_data['milestone'],
                estimated_hours=task_data['estimated_hours'],
                agent_type=task_data.get('agent_type', 'manual'),
                dependencies=[]  # Will update in second pass
            )
            
            task_id = self.state_mgr.create_task(task)
            title_to_id[task_data['title']] = task_id
        
        # Second pass: Update dependencies
        for task_data in tasks:
            if task_data['dependencies']:
                task_id = title_to_id[task_data['title']]
                
                # Resolve dependency titles to IDs
                dependency_ids = []
                for dep_title in task_data['dependencies']:
                    if dep_title in title_to_id:
                        dependency_ids.append(title_to_id[dep_title])
                    else:
                        logger.warning(f"Dependency not found: {dep_title}")
                
                if dependency_ids:
                    self.state_mgr.update_task(task_id, dependencies=dependency_ids)
        
        return len(tasks)
    
    def _generate_summary(
        self, 
        context: AgentContext,
        tasks: List[Dict[str, Any]],
        created_count: int
    ) -> str:
        """Generate human-readable plan summary.
        
        Args:
            context: Agent context.
            tasks: List of task dictionaries.
            created_count: Number of tasks created.
            
        Returns:
            Formatted summary string.
        """
        # Group by milestone
        milestones = {}
        for task in tasks:
            milestone = task['milestone']
            if milestone not in milestones:
                milestones[milestone] = []
            milestones[milestone].append(task)
        
        # Calculate stats
        total_hours = sum(t['estimated_hours'] for t in tasks)
        high_priority = sum(1 for t in tasks if t['priority'] == 2)
        
        # Build summary
        summary = f"""# 📋 Project Plan for: {context.project_name}

## 📊 Overview
- **Total Tasks**: {created_count}
- **Milestones**: {len(milestones)}
- **Estimated Time**: {total_hours:.1f} hours
- **High Priority Tasks**: {high_priority}

---

"""
        
        # List tasks by milestone
        for milestone, milestone_tasks in milestones.items():
            milestone_hours = sum(t['estimated_hours'] for t in milestone_tasks)
            summary += f"## 🎯 {milestone} ({len(milestone_tasks)} tasks, ~{milestone_hours:.1f}h)\n\n"
            
            for task in milestone_tasks:
                priority_icon = {0: "🟢", 1: "🟡", 2: "🔴"}[task['priority']]
                deps_str = f" [Depends on: {', '.join(str(d) for d in task['dependencies'][:2])}]" if task['dependencies'] else ""
                
                summary += f"{priority_icon} **{task['title']}** (~{task['estimated_hours']}h){deps_str}\n"
                summary += f"   {task['description'][:100]}...\n\n"
        
        summary += """---

## 🚀 Next Steps
1. Review the task breakdown above
2. Start with tasks in the first milestone
3. Use `TerraQore tasks "Project Name"` to see available tasks
4. Execute tasks: `TerraQore run "Project Name"` (Coming Soon)

✨ Your project is now ready for execution!
"""
        
        return summary