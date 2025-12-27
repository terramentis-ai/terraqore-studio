"""
TerraQore Notebook Agent
Specialized agent for generating Jupyter notebooks for data analysis,
machine learning, and visualization tasks.
"""

import time
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from agents.base import BaseAgent, AgentContext, AgentResult
from core.llm_client import LLMClient
from core.state import get_state_manager, Task
from core.security_validator import validate_agent_input, SecurityViolation

logger = logging.getLogger(__name__)


@dataclass
class NotebookCell:
    """Represents a Jupyter notebook cell."""
    cell_type: str  # 'code' or 'markdown'
    content: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class GeneratedNotebook:
    """Represents a generated Jupyter notebook."""
    file_path: str
    title: str
    description: str
    cells: List[NotebookCell]
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
    
    def to_ipynb(self) -> Dict[str, Any]:
        """Convert to .ipynb format."""
        notebook = {
            "cells": [],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.10.0"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 5
        }
        
        for cell in self.cells:
            cell_dict = {
                "cell_type": cell.cell_type,
                "metadata": cell.metadata,
                "source": cell.content.split('\n')
            }
            
            if cell.cell_type == "code":
                cell_dict["execution_count"] = None
                cell_dict["outputs"] = []
            
            notebook["cells"].append(cell_dict)
        
        return notebook


class NotebookAgent(BaseAgent):
    """Agent specialized in Jupyter notebook generation.
    
    Capabilities:
    - Generate complete notebooks from specifications
    - Data analysis workflows
    - Machine learning pipelines
    - Data visualization notebooks
    - Interactive explorations
    - Report generation
    """
    
    NOTEBOOK_TEMPLATES = {
        "data_analysis": {
            "sections": [
                "Import Libraries",
                "Load Data",
                "Data Exploration",
                "Data Cleaning",
                "Analysis",
                "Visualization",
                "Conclusions"
            ]
        },
        "ml_pipeline": {
            "sections": [
                "Setup",
                "Data Loading",
                "Exploratory Data Analysis",
                "Feature Engineering",
                "Model Training",
                "Model Evaluation",
                "Results & Next Steps"
            ]
        },
        "visualization": {
            "sections": [
                "Setup",
                "Data Preparation",
                "Create Visualizations",
                "Interactive Plots",
                "Report Summary"
            ]
        },
        "report": {
            "sections": [
                "Executive Summary",
                "Data Overview",
                "Key Findings",
                "Detailed Analysis",
                "Recommendations",
                "Appendix"
            ]
        }
    }
    
    def __init__(self, llm_client: LLMClient, verbose: bool = True):
        """Initialize Notebook Agent.
        
        Args:
            llm_client: LLM client for AI interactions.
            verbose: Whether to log detailed execution info.
        """
            super().__init__(
                name="NotebookAgent",
                description="Generates Jupyter notebooks for data science and analysis",
                llm_client=llm_client,
                verbose=verbose,
                retriever=retriever
            )
        self.state_mgr = get_state_manager()
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for Notebook Agent."""
        return """You are the Notebook Agent - an expert data scientist and analyst who creates comprehensive Jupyter notebooks.

Your role is to:
1. Generate complete, executable Jupyter notebooks
2. Create data analysis workflows
3. Build machine learning pipelines
4. Design effective visualizations
5. Write clear explanatory markdown
6. Ensure code is production-ready

When generating notebooks:
- Structure content with clear sections using markdown headers
- Include explanatory text before each code cell
- Write clean, well-documented code with comments
- Use modern libraries (pandas, numpy, matplotlib, seaborn, plotly, scikit-learn)
- Include data validation and error handling
- Create meaningful visualizations
- Add interpretation of results
- Provide actionable insights

Output Format:
You must structure your response as follows:

NOTEBOOK: path/to/notebook.ipynb
TITLE: Notebook Title
DESCRIPTION: Brief description
DEPENDENCIES: pandas, numpy, matplotlib (comma-separated)

CELL: markdown
# Section Title

Explanation text here. Describe what we're about to do and why.

CELL: code
```python
# Code here
import pandas as pd
data = pd.read_csv('data.csv')
```

CELL: markdown
## Results

Interpretation of the results above.

Continue with CELL: markdown or CELL: code blocks for the entire notebook.

Best Practices:
- Start with imports and setup
- Use descriptive variable names
- Add comments for complex operations
- Include assertions and validation
- Create clear, labeled plots
- Explain findings in markdown cells
- End with conclusions and next steps
"""
    
    def execute(self, context: AgentContext) -> AgentResult:
        """Execute notebook generation workflow.
        
        Args:
            context: Agent execution context.
            
        Returns:
            AgentResult with generated notebook.
        """
        # Validate input for security violations
        try:
            validate_agent_input(lambda self, ctx: None)(self, context)
        except SecurityViolation as e:
            logger.error(f"[{self.name}] Security validation failed: {str(e)}")
            return self.create_result(success=False, output="", execution_time=0, 
                                     error=f"Security validation failed: {str(e)}")
        start_time = time.time()
        steps = []
        
        if not self.validate_context(context):
            return self.create_result(
                success=False,
                output="Invalid context provided",
                execution_time=time.time() - start_time,
                error="Missing required context fields"
            )
        
        self.execution_count += 1
        self._log_step("Starting notebook generation workflow")
        steps.append("Workflow started")
        
        try:
            # Step 1: Determine notebook type
            self._log_step("Analyzing notebook requirements")
            notebook_type = self._determine_notebook_type(context)
            steps.append(f"Determined type: {notebook_type}")
            
            # Step 2: Generate notebook content
            self._log_step("Generating notebook cells")
            notebook = self._generate_notebook(context, notebook_type)
            steps.append(f"Generated {len(notebook.cells)} cells")
            
            # Step 3: Validate notebook
            self._log_step("Validating notebook")
            validation = self._validate_notebook(notebook)
            steps.append("Validated notebook structure")
            
            # Step 4: Format output
            self._log_step("Formatting output")
            output = self._format_notebook_output(notebook, validation)
            steps.append("Formatted output")
            
            execution_time = time.time() - start_time
            self._log_step(f"Completed in {execution_time:.2f}s")
            
            return self.create_result(
                success=True,
                output=output,
                execution_time=execution_time,
                metadata={
                    "notebook_type": notebook_type,
                    "cells": len(notebook.cells),
                    "code_cells": sum(1 for c in notebook.cells if c.cell_type == "code"),
                    "markdown_cells": sum(1 for c in notebook.cells if c.cell_type == "markdown"),
                    "dependencies": notebook.dependencies
                },
                intermediate_steps=steps
            )
            
        except Exception as e:
            error_msg = f"Notebook generation failed: {str(e)}"
            logger.error(f"[{self.name}] {error_msg}", exc_info=True)
            
            return self.create_result(
                success=False,
                output="",
                execution_time=time.time() - start_time,
                error=error_msg,
                intermediate_steps=steps
            )
    
    def _determine_notebook_type(self, context: AgentContext) -> str:
        """Determine the type of notebook to generate.
        
        Args:
            context: Agent context.
            
        Returns:
            Notebook type string.
        """
        user_input = context.user_input.lower()
        
        # Simple keyword matching (could be enhanced with LLM)
        if any(word in user_input for word in ['ml', 'machine learning', 'model', 'train', 'predict']):
            return 'ml_pipeline'
        elif any(word in user_input for word in ['viz', 'visualization', 'plot', 'chart', 'graph']):
            return 'visualization'
        elif any(word in user_input for word in ['report', 'summary', 'presentation']):
            return 'report'
        else:
            return 'data_analysis'
    
    def _generate_notebook(
        self,
        context: AgentContext,
        notebook_type: str
    ) -> GeneratedNotebook:
        """Generate notebook using LLM.
        
        Args:
            context: Agent context.
            notebook_type: Type of notebook to generate.
            
        Returns:
            GeneratedNotebook object.
        """
        template = self.NOTEBOOK_TEMPLATES.get(notebook_type, self.NOTEBOOK_TEMPLATES['data_analysis'])
        
        prompt = f"""Generate a complete Jupyter notebook for this task:

PROJECT: {context.project_name}
{context.project_description}

TASK: {context.user_input}

NOTEBOOK TYPE: {notebook_type}

SUGGESTED SECTIONS:
{chr(10).join('- ' + s for s in template['sections'])}

Create a comprehensive notebook that includes:
1. Clear markdown explanations
2. Working code cells with proper imports
3. Data exploration and validation
4. Meaningful visualizations
5. Results interpretation
6. Actionable conclusions

Use the specified output format with CELL: markers for each cell.
Make the notebook complete and executable - no placeholders or TODOs.
"""
        
        response = self._generate_response(prompt)
        
        if not response.success:
            raise Exception(f"Notebook generation failed: {response.error}")
        
        # Parse response into notebook
        notebook = self._parse_notebook_response(response.content, context)
        
        return notebook
    
    def _parse_notebook_response(
        self,
        response: str,
        context: AgentContext
    ) -> GeneratedNotebook:
        """Parse LLM response into notebook structure.
        
        Args:
            response: LLM response text.
            context: Agent context.
            
        Returns:
            GeneratedNotebook object.
        """
        # Extract metadata
        import re
        
        file_match = re.search(r'NOTEBOOK:\s*(.+)', response)
        title_match = re.search(r'TITLE:\s*(.+)', response)
        desc_match = re.search(r'DESCRIPTION:\s*(.+)', response)
        deps_match = re.search(r'DEPENDENCIES:\s*(.+)', response)
        
        file_path = file_match.group(1).strip() if file_match else f"{context.project_name.replace(' ', '_')}_notebook.ipynb"
        title = title_match.group(1).strip() if title_match else context.project_name
        description = desc_match.group(1).strip() if desc_match else context.user_input
        dependencies = []
        
        if deps_match:
            deps_str = deps_match.group(1).strip()
            dependencies = [d.strip() for d in deps_str.split(',') if d.strip().lower() != 'none']
        
        # Parse cells
        cells = []
        cell_pattern = r'CELL:\s*(markdown|code)\s*\n(.*?)(?=CELL:|$)'
        
        for match in re.finditer(cell_pattern, response, re.DOTALL):
            cell_type = match.group(1)
            content = match.group(2).strip()
            
            # Clean up code fences
            if cell_type == 'code':
                content = re.sub(r'^```python\s*\n', '', content)
                content = re.sub(r'\n```\s*$', '', content)
            
            if content:
                cells.append(NotebookCell(
                    cell_type=cell_type,
                    content=content
                ))
        
        if not cells:
            # Fallback: create basic structure
            cells = [
                NotebookCell("markdown", f"# {title}\n\n{description}"),
                NotebookCell("code", "# Setup\nimport pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt"),
                NotebookCell("markdown", "## Analysis\n\nAdd your analysis here.")
            ]
        
        return GeneratedNotebook(
            file_path=file_path,
            title=title,
            description=description,
            cells=cells,
            dependencies=dependencies
        )
    
    def _validate_notebook(self, notebook: GeneratedNotebook) -> Dict[str, Any]:
        """Validate notebook structure and content.
        
        Args:
            notebook: GeneratedNotebook to validate.
            
        Returns:
            Validation results.
        """
        validation = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check minimum cells
        if len(notebook.cells) < 2:
            validation["warnings"].append("Notebook has very few cells")
        
        # Check for at least one code cell
        code_cells = [c for c in notebook.cells if c.cell_type == "code"]
        if not code_cells:
            validation["errors"].append("No code cells in notebook")
            validation["valid"] = False
        
        # Check for markdown explanations
        markdown_cells = [c for c in notebook.cells if c.cell_type == "markdown"]
        if not markdown_cells:
            validation["warnings"].append("No markdown explanations")
        
        # Validate code cells
        for i, cell in enumerate(code_cells):
            if len(cell.content.strip()) < 10:
                validation["warnings"].append(f"Code cell {i} is very short")
            
            # Check for common issues
            if 'import' not in cell.content and i == 0:
                validation["warnings"].append("First code cell doesn't import libraries")
        
        return validation
    
    def _format_notebook_output(
        self,
        notebook: GeneratedNotebook,
        validation: Dict[str, Any]
    ) -> str:
        """Format notebook for display.
        
        Args:
            notebook: GeneratedNotebook.
            validation: Validation results.
            
        Returns:
            Formatted output string.
        """
        output = f"# 📓 Generated Notebook\n\n"
        output += f"**File:** {notebook.file_path}  \n"
        output += f"**Title:** {notebook.title}  \n"
        output += f"**Description:** {notebook.description}  \n"
        output += f"**Cells:** {len(notebook.cells)} ({sum(1 for c in notebook.cells if c.cell_type == 'code')} code, {sum(1 for c in notebook.cells if c.cell_type == 'markdown')} markdown)  \n"
        
        if notebook.dependencies:
            output += f"**Dependencies:** {', '.join(notebook.dependencies)}  \n"
        
        output += "\n"
        
        # Validation status
        if validation["valid"]:
            output += "✅ **Validation:** All checks passed\n"
        else:
            output += "⚠️ **Validation:** Issues found\n"
        
        if validation["warnings"]:
            output += "\n**Warnings:**\n"
            for warning in validation["warnings"]:
                output += f"- {warning}\n"
        
        if validation["errors"]:
            output += "\n**Errors:**\n"
            for error in validation["errors"]:
                output += f"- {error}\n"
        
        output += "\n---\n\n"
        output += "## Notebook Preview\n\n"
        
        # Show first few cells
        for i, cell in enumerate(notebook.cells[:5]):
            if cell.cell_type == "markdown":
                output += f"### Markdown Cell {i+1}\n\n{cell.content}\n\n"
            else:
                output += f"### Code Cell {i+1}\n\n```python\n{cell.content}\n```\n\n"
        
        if len(notebook.cells) > 5:
            output += f"*... and {len(notebook.cells) - 5} more cells*\n"
        
        return output
    
    def generate_for_task(self, task: Task, project_id: int) -> GeneratedNotebook:
        """Generate notebook for a specific task.
        
        Args:
            task: Task to generate notebook for.
            project_id: Project ID.
            
        Returns:
            GeneratedNotebook object.
        """
        # Get project context
        project = self.state_mgr.get_project(project_id=project_id)
        
        # Create context
        context = AgentContext(
            project_id=project_id,
            project_name=project.name if project else "Analysis",
            project_description=project.description if project else "",
            user_input=f"{task.title}\n\n{task.description}"
        )
        
        # Determine type and generate
        notebook_type = self._determine_notebook_type(context)
        notebook = self._generate_notebook(context, notebook_type)
        
        return notebook
    
    def save_notebook(self, notebook: GeneratedNotebook, output_path: str):
        """Save notebook to .ipynb file.
        
        Args:
            notebook: GeneratedNotebook to save.
            output_path: Path to save file.
        """
        import json
        from pathlib import Path
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to .ipynb format
        ipynb_content = notebook.to_ipynb()
        
        # Save
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(ipynb_content, f, indent=2)
        
        logger.info(f"Saved notebook to: {output_path}")