"""
Coder Agent - Generates production-ready code from task specifications.

Phase 4 Component: Responsible for converting task descriptions into actual
code files, supporting multiple programming languages (Python, JavaScript/TypeScript).
"""

import json
import logging
import re
import time
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from .base import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger(__name__)


@dataclass
class CodeFile:
    """Represents a generated code file."""
    path: str                    # e.g., "src/main.py" or "app/routes.js"
    language: str               # "python", "javascript", "typescript"
    content: str                # Actual code content
    description: str            # What this file does
    test_code: Optional[str] = None  # Optional test code
    dependencies: List[str] = None   # Package dependencies


@dataclass
class CodeGeneration:
    """Result of code generation for a task."""
    task_id: int
    task_title: str
    language: str
    files: List[CodeFile]
    summary: str
    execution_notes: str
    validation_passed: bool


class CoderAgent(BaseAgent):
    """
    Code generation agent that converts tasks into production-ready code.
    
    Workflow:
    1. Analyze task requirements and technical specifications
    2. Determine appropriate language(s) for implementation
    3. Generate code files with proper structure
    4. Include test code for validation
    5. Document generated code
    """
    
    def __init__(self, llm_client=None, description: str = "Generates production-ready code from task specifications", test_mode: bool = False, verbose: bool = False, retriever: object = None):
        """Initialize CoderAgent.

        Args:
            llm_client: Optional LLM client to use for generation. If None, the agent will
                        expect one to be provided by the orchestrator or will error when
                        trying to generate code.
            description: Agent description.
            test_mode: If True, use deterministic stubbed code generation instead of calling LLMs.
            verbose: Whether to log detailed execution info.
        """
        # Defer llm_client creation to orchestrator when possible; pass None if unavailable
        super().__init__(name="CoderAgent", description=description, llm_client=llm_client, verbose=verbose, retriever=retriever)
        self.supported_languages = ["python", "javascript", "typescript"]
        self.code_generation_count = 0
        self.files_generated = 0
        self.test_mode = bool(test_mode)
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the Coder Agent."""
        return """You are an expert full-stack developer and code generation AI assistant.

Your role: Generate production-ready code from task specifications.

Guidelines:
- Generate clean, well-documented, production-quality code
- Follow language best practices and conventions
- Include error handling and input validation
- Add comprehensive comments explaining complex logic
- Generate test code to validate functionality
- Keep code DRY and maintainable
- Use appropriate design patterns
- Consider security best practices
- Optimize for readability and performance

Code Structure:
- Use proper folder structure (src/, tests/, config/, etc.)
- Separate concerns (models, routes, utilities, etc.)
- Include configuration files (requirements.txt, package.json, etc.)
- Add README sections for new modules

Output Format:
Return ONLY a valid JSON object with this structure (no other text):
{
    "task_title": "Task name",
    "language": "python" or "javascript" or "typescript",
    "files": [
        {
            "path": "relative/path/to/file.py",
            "description": "What this file does",
            "content": "Full code content here",
            "test_code": "Optional test code",
            "dependencies": ["package1", "package2"]
        }
    ],
    "summary": "Brief summary of what was generated",
    "execution_notes": "How to run/test this code",
    "validation_tips": "Tips for validating the generated code"
}"""
    
    def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute code generation for a task.
        
        Args:
            context: AgentContext with task information
            
        Returns:
            AgentResult with generated code and metadata
        """
        try:
            start_time = time.time()
            steps = []
            
            # Step 1: Extract task requirements
            self._log_step("Extracting task requirements")
            task_info = self._extract_task_info(context)
            steps.append("Extracted task requirements")
            
            # Step 2: Determine language(s)
            self._log_step("Determining target language")
            language = self._determine_language(task_info, context)
            steps.append(f"Selected {language} as target language")
            
            # Step 3: Generate code
            self._log_step("Generating code files")
            code_generation = self._generate_code(context, task_info, language)
            steps.append(f"Generated {len(code_generation.files)} files")
            
            # Step 4: Validate generated code
            self._log_step("Validating generated code")
            validation_passed = self._validate_code(code_generation)
            code_generation.validation_passed = validation_passed
            steps.append(f"Validation {'passed' if validation_passed else 'completed with warnings'}")
            
            execution_time = time.time() - start_time
            self._log_step(f"Completed in {execution_time:.2f}s")
            
            self.code_generation_count += 1
            self.files_generated += len(code_generation.files)
            
            return self.create_result(
                success=validation_passed,
                output=self._format_code_generation_output(code_generation),
                execution_time=execution_time,
                metadata={
                    "language": language,
                    "files_generated": len(code_generation.files),
                    "task_id": task_info.get("id", "unknown"),
                    "validation_passed": validation_passed,
                    "provider": "coder_agent",
                    "code_generation": asdict(code_generation)
                },
                intermediate_steps=steps
            )
            
        except Exception as e:
            error_msg = f"Code generation failed: {str(e)}"
            logger.error(f"[{self.name}] {error_msg}", exc_info=True)
            
            return self.create_result(
                success=False,
                output="",
                execution_time=0,
                metadata={"provider": "coder_agent", "error": str(e)},
                intermediate_steps=[]
            )
    
    def _extract_task_info(self, context: AgentContext) -> Dict[str, Any]:
        """Extract task information from context."""
        task_data = {
            "id": context.metadata.get("task_id", 0),
            "title": context.metadata.get("task_title", context.project_name),
            "description": context.metadata.get("description", context.user_input or context.project_description),
            "priority": context.metadata.get("priority", "medium"),
            "estimated_hours": context.metadata.get("estimated_hours", 4),
            "dependencies": context.metadata.get("dependencies", []),
            "milestone": context.metadata.get("milestone", "unknown"),
            "suggested_language": context.metadata.get("language_hint", None),
        }
        return task_data
    
    def _determine_language(self, task_info: Dict[str, Any], context: AgentContext) -> str:
        """Determine the best programming language for the task."""
        
        # Check if language was suggested
        if task_info.get("suggested_language"):
            lang = task_info["suggested_language"].lower()
            if lang in self.supported_languages:
                return lang
        
        # Analyze task description for language hints
        task_desc = (task_info["title"] + " " + task_info["description"]).lower()
        
        # Python indicators
        if any(keyword in task_desc for keyword in 
               ["api", "backend", "server", "fastapi", "flask", "django", 
                "data", "ml", "machine learning", "script", "automation"]):
            return "python"
        
        # JavaScript/TypeScript indicators
        if any(keyword in task_desc for keyword in 
               ["react", "frontend", "client", "web", "node", "express", 
                "typescript", "angular", "vue", "browser"]):
            return "javascript"
        
        # Default to Python for backend tasks, JavaScript for frontend
        if "frontend" in task_desc or "ui" in task_desc or "component" in task_desc:
            return "javascript"
        
        return "python"  # Default language
    
    def _generate_code(
        self, 
        context: AgentContext, 
        task_info: Dict[str, Any],
        language: str
    ) -> CodeGeneration:
        """Generate code files for the task."""
        
        # If running in test mode, return deterministic stubbed code
        if getattr(self, "test_mode", False):
            logger.info("Test mode enabled - using stubbed code generation")
            return self._stub_generate_code(context, task_info, language)

        # Build the code generation prompt
        prompt = self._build_code_prompt(task_info, language, context)
        
        # Get code from LLM
        try:
            response = self._generate_response(prompt)
        except Exception as e:
            logger.warning(f"LLM generation failed with exception: {e}. Falling back to stubbed generator.")
            return self._stub_generate_code(context, task_info, language)
        
        if not response.success:
            # Known failure (e.g., invalid API keys / unavailable providers) -> fallback
            logger.warning(f"LLM providers unavailable: {response.error}. Falling back to stubbed generator.")
            return self._stub_generate_code(context, task_info, language)
        
        # Parse the generated code
        files = self._parse_code_response(response.content, language)
        
        # Create CodeGeneration object
        code_gen = CodeGeneration(
            task_id=task_info["id"],
            task_title=task_info["title"],
            language=language,
            files=files,
            summary=f"Generated {len(files)} files for {task_info['title']}",
            execution_notes=self._generate_execution_notes(files, language),
            validation_passed=True
        )
        
        return code_gen

    def _stub_generate_code(self, context: AgentContext, task_info: Dict[str, Any], language: str) -> CodeGeneration:
        """Deterministic stubbed code generator used when LLMs are unavailable or for testing.

        Returns a small, valid set of files suitable for running tests and exercising the apply/rollback flow.
        """
        files = []
        project_marker = context.project_name or "project"

        if language == "python":
            files.append(CodeFile(path="src/__init__.py", language="python", content="", description="Package init"))
            files.append(CodeFile(
                path="src/main.py",
                language="python",
                content=("def greet():\n"
                         f"    return \"Hello from {project_marker}\"\n\n"
                         "if __name__ == '__main__':\n"
                         "    print(greet())\n"),
                description="Simple entrypoint function"
            ))
            files.append(CodeFile(
                path="tests/test_main.py",
                language="python",
                content=("from src.main import greet\n\n"
                         "def test_greet():\n"
                         f"    assert greet() == \"Hello from {project_marker}\"\n"),
                description="Basic unit test for greet()"
            ))
            files.append(CodeFile(path="requirements.txt", language="text", content="pytest\n", description="Test requirements"))

        elif language in ["javascript", "typescript"]:
            files.append(CodeFile(
                path="src/index.js",
                language="javascript",
                content=("function greet() {\n"
                         f"  return 'Hello from {project_marker}';\n"
                         "}\n\nmodule.exports = { greet };\n"),
                description="Simple greet function"
            ))
            files.append(CodeFile(
                path="tests/test_index.js",
                language="javascript",
                content=("const { greet } = require('../src/index');\n\n"
                         "test('greet returns expected message', () => {\n"
                         f"  expect(greet()).toBe('Hello from {project_marker}');\n"
                         "});\n"),
                description="Basic Jest test for greet()"
            ))
            files.append(CodeFile(path="package.json", language="json", content='{"scripts": {"test": "jest"}}', description="Package info"))

        else:
            # Default fallback file if language unknown
            files.append(CodeFile(path="README.md", language="text", content=f"Generated stub for {project_marker}", description="Placeholder"))

        code_gen = CodeGeneration(
            task_id=task_info.get("id", 0),
            task_title=task_info.get("title", "Stubbed Task"),
            language=language,
            files=files,
            summary=f"Stubbed generation: {len(files)} files for {task_info.get('title', '')}",
            execution_notes="Run tests with pytest or npm test depending on language",
            validation_passed=True
        )

        return code_gen
    
    def _build_code_prompt(
        self,
        task_info: Dict[str, Any],
        language: str,
        context: AgentContext
    ) -> str:
        """Build the prompt for code generation."""
        
        lang_info = self._get_language_info(language)
        
        prompt = f"""Generate production-ready code for this task:

Task Title: {task_info['title']}
Description: {task_info['description']}
Priority: {task_info['priority']}
Estimated Effort: {task_info['estimated_hours']} hours
Milestone: {task_info['milestone']}

Language: {language}
Framework Preferences: {', '.join(str(f) for f in lang_info['frameworks'])}
Package Manager: {lang_info['package_manager']}

Project Context:
- Project Name: {context.project_name}
- Project Description: {context.project_description}

Requirements:
- Generate complete, working code
- Include proper error handling
- Add input validation
- Include type hints/types where applicable
- Add comprehensive comments
- Generate test code
- List all required dependencies
- Follow {language} best practices
- Ensure code is secure and maintainable

Directory Structure to Use:
{lang_info['directory_structure']}

Provide the code in valid JSON format as specified in the system prompt."""
        
        return prompt
    
    def _get_language_info(self, language: str) -> Dict[str, Any]:
        """Get language-specific information."""
        
        language_config = {
            "python": {
                "frameworks": ["FastAPI", "Flask", "Django", "aiohttp"],
                "package_manager": "pip",
                "directory_structure": """
src/
  __init__.py
  main.py
  models.py
  utils.py
tests/
  __init__.py
  test_main.py
requirements.txt
README.md
.gitignore""",
            },
            "javascript": {
                "frameworks": ["Express", "Next.js", "React", "Vue"],
                "package_manager": "npm",
                "directory_structure": """
src/
  index.js
  app.js
  routes/
  middleware/
tests/
  test.js
package.json
.gitignore
README.md""",
            },
            "typescript": {
                "frameworks": ["Express", "Next.js", "React", "NestJS"],
                "package_manager": "npm",
                "directory_structure": """
src/
  index.ts
  app.ts
  routes/
  middleware/
  types/
tests/
  test.ts
package.json
tsconfig.json
.gitignore
README.md""",
            }
        }
        
        return language_config.get(language, language_config["python"])
    
    def _parse_code_response(self, response: str, language: str) -> List[CodeFile]:
        """Parse the LLM response into CodeFile objects."""
        
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                raise ValueError("No JSON found in response")
            
            json_str = json_match.group(0)
            
            # Clean up the JSON (handle newlines, control characters)
            json_str = json_str.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
            json_str = re.sub(r' +', ' ', json_str)
            
            data = json.loads(json_str)
            
            files = []
            for file_data in data.get("files", []):
                code_file = CodeFile(
                    path=file_data.get("path", ""),
                    language=language,
                    content=file_data.get("content", ""),
                    description=file_data.get("description", ""),
                    test_code=file_data.get("test_code"),
                    dependencies=file_data.get("dependencies", [])
                )
                files.append(code_file)
            
            return files
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse code response: {str(e)}")
            return []
    
    def _validate_code(self, code_generation: CodeGeneration) -> bool:
        """Validate the generated code."""
        
        # Check that we have files
        if not code_generation.files:
            logger.warning("No files were generated")
            return False
        
        # Check file paths and content
        for code_file in code_generation.files:
            if not code_file.path:
                logger.warning(f"File has no path: {code_file.description}")
                return False
            
            if not code_file.content:
                logger.warning(f"File {code_file.path} has no content")
                return False
            
            # Language-specific validation
            if code_generation.language == "python":
                if not self._validate_python_code(code_file):
                    logger.warning(f"Python validation failed for {code_file.path}")
                    return False
            
            elif code_generation.language in ["javascript", "typescript"]:
                if not self._validate_js_code(code_file):
                    logger.warning(f"JavaScript/TypeScript validation failed for {code_file.path}")
                    return False
        
        return True
    
    def _validate_python_code(self, code_file: CodeFile) -> bool:
        """Validate Python code syntax."""
        try:
            compile(code_file.content, code_file.path, 'exec')
            return True
        except SyntaxError as e:
            logger.warning(f"Python syntax error in {code_file.path}: {e}")
            return False
    
    def _validate_js_code(self, code_file: CodeFile) -> bool:
        """Basic validation for JavaScript/TypeScript code."""
        # Basic checks (full validation requires a JS parser)
        issues = []
        
        # Check for common patterns
        if code_file.content.count('{') != code_file.content.count('}'):
            issues.append("Mismatched braces")
        
        if code_file.content.count('(') != code_file.content.count(')'):
            issues.append("Mismatched parentheses")
        
        if code_file.content.count('[') != code_file.content.count(']'):
            issues.append("Mismatched brackets")
        
        if issues:
            logger.warning(f"JS/TS validation issues in {code_file.path}: {', '.join(issues)}")
            return False
        
        return True
    
    def _generate_execution_notes(self, files: List[CodeFile], language: str) -> str:
        """Generate notes on how to execute the generated code."""
        
        if language == "python":
            return f"""Python Code Execution:
1. Install dependencies: pip install -r requirements.txt
2. Run main file: python src/main.py
3. Run tests: python -m pytest tests/
4. Expected output: Check console for results"""
        
        elif language in ["javascript", "typescript"]:
            return f"""JavaScript/TypeScript Code Execution:
1. Install dependencies: npm install
2. For JavaScript: npm start or node src/index.js
3. For TypeScript: npm run build && npm start
4. Run tests: npm test
5. Expected output: Check console for results"""
        
        return "Refer to framework documentation for execution details"
    
    def _format_code_generation_output(self, code_gen: CodeGeneration) -> str:
        """Format the code generation output for display."""
        
        output = f"""
Generated Code for: {code_gen.task_title}
Language: {code_gen.language.upper()}
Files: {len(code_gen.files)}

Files Generated:
"""
        for file in code_gen.files:
            output += f"\n  📄 {file.path}\n"
            output += f"     {file.description}\n"
            if file.dependencies:
                output += f"     Dependencies: {', '.join(str(d) for d in file.dependencies)}\n"
        
        output += f"\nSummary: {code_gen.summary}\n"
        output += f"Execution Notes:\n{code_gen.execution_notes}\n"
        output += f"Validation: {'✓ PASSED' if code_gen.validation_passed else '⚠ WARNINGS'}\n"
        
        return output
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics about code generation."""
        return {
            "code_generations": self.code_generation_count,
            "files_generated": self.files_generated,
            "executions": self.execution_count,
        }
