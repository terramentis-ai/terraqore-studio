"""
Project Template Registry
Pre-built project templates for non-technical users.
Each template provides a starting point for common project types.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class TemplateCategory(Enum):
    """Project template categories."""
    WEB_APP = "web_application"
    DATA_PIPELINE = "data_pipeline"
    API_SERVICE = "api_service"
    MOBILE_APP = "mobile_application"
    ML_MODEL = "ml_model"
    CHATBOT = "chatbot"
    E_COMMERCE = "e_commerce"
    AUTOMATION = "automation"
    DASHBOARD = "dashboard"
    DOCUMENTATION = "documentation"
    BUSINESS_TOOL = "business_tool"
    GAME = "game"


@dataclass
class TemplateRequirement:
    """Single requirement for a template."""
    package: str
    version: str
    description: str


@dataclass
class TemplatePhase:
    """Single phase in template workflow."""
    phase_name: str
    description: str
    tasks: List[str]
    expected_duration_hours: float


@dataclass
class ProjectTemplate:
    """A project template for quick-start."""
    id: str
    name: str
    description: str
    category: TemplateCategory
    difficulty_level: str  # beginner, intermediate, advanced
    estimated_hours: float
    technologies: List[str]
    requirements: List[TemplateRequirement]
    workflow_phases: List[TemplatePhase]
    example_files: List[str]
    success_criteria: List[str]
    prerequisites: List[str] = None
    best_for: str = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "difficulty_level": self.difficulty_level,
            "estimated_hours": self.estimated_hours,
            "technologies": self.technologies,
            "requirements": [asdict(r) for r in self.requirements],
            "workflow_phases": [asdict(p) for p in self.workflow_phases],
            "example_files": self.example_files,
            "success_criteria": self.success_criteria,
            "prerequisites": self.prerequisites or [],
            "best_for": self.best_for
        }


class TemplateRegistry:
    """Central registry for project templates."""
    
    def __init__(self):
        """Initialize template registry."""
        self.templates: Dict[str, ProjectTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self) -> None:
        """Load default built-in templates."""
        self.register_template(self._create_personal_blog_template())
        self.register_template(self._create_api_backend_template())
        self.register_template(self._create_data_analysis_template())
        self.register_template(self._create_todo_app_template())
        self.register_template(self._create_chatbot_template())
        self.register_template(self._create_ecommerce_store_template())
        self.register_template(self._create_portfolio_template())
        self.register_template(self._create_ml_classifier_template())
        self.register_template(self._create_automation_script_template())
        self.register_template(self._create_rest_api_template())
        self.register_template(self._create_dashboard_template())
        self.register_template(self._create_documentation_site_template())
    
    def register_template(self, template: ProjectTemplate) -> None:
        """Register a new template.
        
        Args:
            template: ProjectTemplate to register.
        """
        self.templates[template.id] = template
        logger.info(f"Registered template: {template.name}")
    
    def get_template(self, template_id: str) -> Optional[ProjectTemplate]:
        """Get a template by ID.
        
        Args:
            template_id: Template ID.
            
        Returns:
            ProjectTemplate or None if not found.
        """
        return self.templates.get(template_id)
    
    def list_templates(self, category: Optional[TemplateCategory] = None) -> List[ProjectTemplate]:
        """List all templates, optionally filtered by category.
        
        Args:
            category: Optional category to filter by.
            
        Returns:
            List of templates.
        """
        if category:
            return [t for t in self.templates.values() if t.category == category]
        return list(self.templates.values())
    
    def search_templates(self, keyword: str) -> List[ProjectTemplate]:
        """Search templates by keyword.
        
        Args:
            keyword: Search keyword.
            
        Returns:
            List of matching templates.
        """
        keyword_lower = keyword.lower()
        return [
            t for t in self.templates.values()
            if (keyword_lower in t.name.lower() or
                keyword_lower in t.description.lower() or
                any(keyword_lower in tech.lower() for tech in t.technologies))
        ]
    
    def get_all_templates(self) -> List[ProjectTemplate]:
        """Get all registered templates.
        
        Returns:
            List of all templates.
        """
        return list(self.templates.values())
    
    def template_count(self) -> int:
        """Get total number of registered templates.
        
        Returns:
            Number of templates.
        """
        return len(self.templates)
    
    def _create_personal_blog_template(self) -> ProjectTemplate:
        """Personal blog website template."""
        return ProjectTemplate(
            id="personal_blog",
            name="Personal Blog Website",
            description="A modern personal blog with posts, categories, and comments",
            category=TemplateCategory.WEB_APP,
            difficulty_level="beginner",
            estimated_hours=20,
            technologies=["React", "Python", "PostgreSQL", "FastAPI"],
            requirements=[
                TemplateRequirement("fastapi", ">=0.100.0", "REST API framework"),
                TemplateRequirement("sqlalchemy", ">=2.0.0", "Database ORM"),
                TemplateRequirement("pydantic", ">=2.0.0", "Data validation"),
            ],
            workflow_phases=[
                TemplatePhase(
                    "Planning",
                    "Define blog structure, features, and database schema",
                    ["Design database schema", "Create user stories", "Plan UI/UX"],
                    4.0
                ),
                TemplatePhase(
                    "Backend Setup",
                    "Create REST API with user auth and blog endpoints",
                    ["Setup FastAPI", "Create database models", "Implement auth"],
                    8.0
                ),
                TemplatePhase(
                    "Frontend Development",
                    "Build React UI for blog interface",
                    ["Create components", "Add styling", "Implement navigation"],
                    6.0
                ),
                TemplatePhase(
                    "Testing & Deployment",
                    "Test functionality and deploy",
                    ["Write tests", "Set up CI/CD", "Deploy to hosting"],
                    2.0
                ),
            ],
            example_files=["models.py", "routes.py", "Blog.tsx", "Post.tsx", "schema.sql"],
            success_criteria=[
                "Users can create accounts and log in",
                "Blog posts can be created, read, updated, deleted",
                "Posts support markdown formatting",
                "Comments system is functional",
                "Site is responsive on mobile"
            ],
            best_for="Beginners learning web development"
        )
    
    def _create_api_backend_template(self) -> ProjectTemplate:
        """REST API backend template."""
        return ProjectTemplate(
            id="rest_api_backend",
            name="REST API Backend Service",
            description="Production-ready REST API with authentication, logging, and testing",
            category=TemplateCategory.API_SERVICE,
            difficulty_level="intermediate",
            estimated_hours=30,
            technologies=["Python", "FastAPI", "PostgreSQL", "Docker"],
            requirements=[
                TemplateRequirement("fastapi", ">=0.100.0", "Web framework"),
                TemplateRequirement("pydantic", ">=2.0.0", "Data validation"),
                TemplateRequirement("sqlalchemy", ">=2.0.0", "ORM"),
                TemplateRequirement("pytest", ">=7.0.0", "Testing"),
            ],
            workflow_phases=[
                TemplatePhase(
                    "Architecture Design",
                    "Design API endpoints, data models, and authentication strategy",
                    ["API specification", "Database design", "Auth strategy"],
                    6.0
                ),
                TemplatePhase(
                    "Core Development",
                    "Implement API endpoints and business logic",
                    ["Create models", "Write endpoints", "Implement validation"],
                    12.0
                ),
                TemplatePhase(
                    "Testing & Documentation",
                    "Write tests and API documentation",
                    ["Unit tests", "Integration tests", "API docs"],
                    8.0
                ),
                TemplatePhase(
                    "Deployment",
                    "Containerize and deploy to production",
                    ["Create Dockerfile", "Setup monitoring", "Deploy"],
                    4.0
                ),
            ],
            example_files=["main.py", "models.py", "schemas.py", "auth.py", "test_api.py"],
            success_criteria=[
                "All endpoints are properly documented",
                "Authentication is secure",
                "Tests cover 80%+ of code",
                "API responds in < 500ms",
                "Error handling is comprehensive"
            ],
            best_for="Backend developers building scalable APIs"
        )
    
    def _create_data_analysis_template(self) -> ProjectTemplate:
        """Data analysis project template."""
        return ProjectTemplate(
            id="data_analysis",
            name="Data Analysis & Visualization",
            description="Data analysis project with pandas, visualization, and reports",
            category=TemplateCategory.DATA_PIPELINE,
            difficulty_level="intermediate",
            estimated_hours=25,
            technologies=["Python", "Pandas", "Matplotlib", "Jupyter"],
            requirements=[
                TemplateRequirement("pandas", ">=2.0.0", "Data manipulation"),
                TemplateRequirement("matplotlib", ">=3.5.0", "Visualization"),
                TemplateRequirement("seaborn", ">=0.12.0", "Statistical visualization"),
                TemplateRequirement("jupyter", ">=1.0.0", "Notebooks"),
            ],
            workflow_phases=[
                TemplatePhase(
                    "Data Collection",
                    "Gather and prepare data from various sources",
                    ["Source data", "Clean data", "Handle missing values"],
                    5.0
                ),
                TemplatePhase(
                    "Exploratory Analysis",
                    "Analyze data patterns and relationships",
                    ["Statistical analysis", "Correlation analysis", "Data profiling"],
                    8.0
                ),
                TemplatePhase(
                    "Visualization",
                    "Create compelling visualizations",
                    ["Create charts", "Build dashboards", "Generate reports"],
                    8.0
                ),
                TemplatePhase(
                    "Insights & Documentation",
                    "Document findings and recommendations",
                    ["Write analysis", "Create presentation", "Share findings"],
                    4.0
                ),
            ],
            example_files=["analysis.ipynb", "data_processor.py", "visualization.py", "report.md"],
            success_criteria=[
                "Data is cleaned and validated",
                "Key insights are documented",
                "Visualizations are clear and informative",
                "Report is reproducible",
                "Recommendations are actionable"
            ],
            best_for="Data analysts and business intelligence professionals"
        )
    
    def _create_todo_app_template(self) -> ProjectTemplate:
        """Simple todo application template."""
        return ProjectTemplate(
            id="todo_app",
            name="Todo Application",
            description="Full-stack todo app with real-time updates and persistence",
            category=TemplateCategory.WEB_APP,
            difficulty_level="beginner",
            estimated_hours=15,
            technologies=["React", "Python", "SQLite", "FastAPI"],
            requirements=[
                TemplateRequirement("fastapi", ">=0.100.0", "Backend"),
                TemplateRequirement("sqlalchemy", ">=2.0.0", "Database"),
            ],
            workflow_phases=[
                TemplatePhase(
                    "Setup",
                    "Initialize project structure and dependencies",
                    ["Setup repo", "Install dependencies", "Configure database"],
                    2.0
                ),
                TemplatePhase(
                    "Backend",
                    "Create API endpoints for todo management",
                    ["Create models", "Implement CRUD", "Add validation"],
                    5.0
                ),
                TemplatePhase(
                    "Frontend",
                    "Build React interface for todo management",
                    ["Create components", "Add styling", "Implement forms"],
                    5.0
                ),
                TemplatePhase(
                    "Polish",
                    "Test and enhance user experience",
                    ["Testing", "UX improvements", "Documentation"],
                    3.0
                ),
            ],
            example_files=["main.py", "models.py", "App.tsx", "TodoList.tsx"],
            success_criteria=[
                "Users can create, read, update, delete todos",
                "Data persists across sessions",
                "UI is intuitive and responsive",
                "No console errors",
                "App loads in < 2 seconds"
            ],
            best_for="Beginners learning full-stack development"
        )
    
    def _create_chatbot_template(self) -> ProjectTemplate:
        """AI chatbot template."""
        return ProjectTemplate(
            id="ai_chatbot",
            name="AI Chatbot Assistant",
            description="Conversational AI chatbot with LLM integration and memory",
            category=TemplateCategory.CHATBOT,
            difficulty_level="advanced",
            estimated_hours=35,
            technologies=["Python", "FastAPI", "LLM API", "Redis"],
            requirements=[
                TemplateRequirement("fastapi", ">=0.100.0", "API framework"),
                TemplateRequirement("openai", ">=1.0.0", "LLM integration"),
                TemplateRequirement("redis", ">=4.5.0", "Conversation memory"),
            ],
            workflow_phases=[
                TemplatePhase(
                    "Design",
                    "Design chatbot personality, capabilities, and conversation flow",
                    ["Define capabilities", "Design prompts", "Plan integrations"],
                    8.0
                ),
                TemplatePhase(
                    "Core Chatbot",
                    "Implement chatbot logic with LLM integration",
                    ["LLM integration", "Memory system", "Context management"],
                    12.0
                ),
                TemplatePhase(
                    "Integration",
                    "Integrate with communication platforms",
                    ["API endpoints", "Chat interface", "Rate limiting"],
                    10.0
                ),
                TemplatePhase(
                    "Testing & Deploy",
                    "Test conversations and deploy",
                    ["Conversation tests", "Performance testing", "Deployment"],
                    5.0
                ),
            ],
            example_files=["chatbot.py", "prompts.py", "memory.py", "api.py", "test_chatbot.py"],
            success_criteria=[
                "Chatbot understands context",
                "Conversations are coherent",
                "Response time < 2 seconds",
                "Memory system works reliably",
                "Error handling is graceful"
            ],
            best_for="Advanced developers building AI applications"
        )
    
    def _create_ecommerce_store_template(self) -> ProjectTemplate:
        """E-commerce store template."""
        return ProjectTemplate(
            id="ecommerce_store",
            name="E-Commerce Online Store",
            description="Full e-commerce platform with products, cart, and payment integration",
            category=TemplateCategory.E_COMMERCE,
            difficulty_level="advanced",
            estimated_hours=40,
            technologies=["React", "Python", "PostgreSQL", "Stripe"],
            requirements=[
                TemplateRequirement("fastapi", ">=0.100.0", "Backend"),
                TemplateRequirement("sqlalchemy", ">=2.0.0", "ORM"),
                TemplateRequirement("stripe", ">=5.0.0", "Payments"),
            ],
            workflow_phases=[
                TemplatePhase(
                    "Architecture",
                    "Design product catalog, cart, and payment flow",
                    ["Database design", "Payment flow", "User roles"],
                    8.0
                ),
                TemplatePhase(
                    "Backend Development",
                    "Implement product management and payment processing",
                    ["Product API", "Cart system", "Payment integration"],
                    12.0
                ),
                TemplatePhase(
                    "Frontend Development",
                    "Build shopping interface and checkout",
                    ["Product catalog", "Shopping cart", "Checkout flow"],
                    12.0
                ),
                TemplatePhase(
                    "Admin & Testing",
                    "Create admin panel and comprehensive testing",
                    ["Admin interface", "Testing", "Deployment"],
                    8.0
                ),
            ],
            example_files=["products.py", "cart.py", "payments.py", "Shop.tsx", "Checkout.tsx"],
            success_criteria=[
                "Products can be browsed and searched",
                "Cart system works reliably",
                "Payments process successfully",
                "Admin can manage inventory",
                "Security best practices are followed"
            ],
            best_for="Entrepreneurs building online stores"
        )
    
    def _create_portfolio_template(self) -> ProjectTemplate:
        """Professional portfolio website template."""
        return ProjectTemplate(
            id="portfolio_website",
            name="Professional Portfolio Website",
            description="Beautiful portfolio site showcasing projects and skills",
            category=TemplateCategory.WEB_APP,
            difficulty_level="beginner",
            estimated_hours=10,
            technologies=["React", "Tailwind CSS", "Next.js"],
            requirements=[
                TemplateRequirement("react", ">=18.0.0", "UI framework"),
                TemplateRequirement("next", ">=13.0.0", "Meta framework"),
            ],
            workflow_phases=[
                TemplatePhase(
                    "Design",
                    "Design portfolio layout and sections",
                    ["Wireframe", "Color scheme", "Typography"],
                    2.0
                ),
                TemplatePhase(
                    "Development",
                    "Build responsive portfolio site",
                    ["Create components", "Add content", "Styling"],
                    5.0
                ),
                TemplatePhase(
                    "Content",
                    "Add projects and professional information",
                    ["Project descriptions", "Skills list", "Contact form"],
                    2.0
                ),
                TemplatePhase(
                    "Launch",
                    "Optimize and deploy portfolio",
                    ["SEO optimization", "Performance", "Hosting"],
                    1.0
                ),
            ],
            example_files=["index.tsx", "projects.tsx", "Header.tsx", "Contact.tsx"],
            success_criteria=[
                "Site is responsive on all devices",
                "Navigation is intuitive",
                "Content is professional",
                "Performance is optimized",
                "SEO is implemented"
            ],
            best_for="Professionals showcasing their work"
        )
    
    def _create_ml_classifier_template(self) -> ProjectTemplate:
        """Machine learning classifier template."""
        return ProjectTemplate(
            id="ml_classifier",
            name="Machine Learning Classifier",
            description="ML model training and deployment pipeline",
            category=TemplateCategory.ML_MODEL,
            difficulty_level="advanced",
            estimated_hours=35,
            technologies=["Python", "Scikit-learn", "Pandas", "MLflow"],
            requirements=[
                TemplateRequirement("scikit-learn", ">=1.3.0", "ML algorithms"),
                TemplateRequirement("pandas", ">=2.0.0", "Data handling"),
                TemplateRequirement("mlflow", ">=2.0.0", "Model tracking"),
            ],
            workflow_phases=[
                TemplatePhase(
                    "Data Preparation",
                    "Load, clean, and prepare training data",
                    ["Data loading", "Cleaning", "Feature engineering"],
                    10.0
                ),
                TemplatePhase(
                    "Model Training",
                    "Train and evaluate ML models",
                    ["Model selection", "Training", "Evaluation"],
                    12.0
                ),
                TemplatePhase(
                    "Optimization",
                    "Optimize model performance",
                    ["Hyperparameter tuning", "Cross-validation", "Feature selection"],
                    8.0
                ),
                TemplatePhase(
                    "Deployment",
                    "Deploy model as API service",
                    ["Model export", "API creation", "Containerization"],
                    5.0
                ),
            ],
            example_files=["train.py", "evaluate.py", "model.py", "api.py", "requirements.txt"],
            success_criteria=[
                "Model accuracy meets target",
                "Cross-validation results are consistent",
                "Model can be served as API",
                "Performance is acceptable",
                "Results are reproducible"
            ],
            best_for="Data scientists building ML pipelines"
        )
    
    def _create_automation_script_template(self) -> ProjectTemplate:
        """Automation script template."""
        return ProjectTemplate(
            id="automation_script",
            name="Business Process Automation",
            description="Automated workflow for repetitive tasks",
            category=TemplateCategory.AUTOMATION,
            difficulty_level="beginner",
            estimated_hours=12,
            technologies=["Python", "Scheduled Tasks", "APIs"],
            requirements=[
                TemplateRequirement("schedule", ">=1.2.0", "Task scheduling"),
                TemplateRequirement("requests", ">=2.31.0", "HTTP library"),
            ],
            workflow_phases=[
                TemplatePhase(
                    "Analysis",
                    "Identify processes to automate",
                    ["Document workflow", "Find integration points", "Plan implementation"],
                    3.0
                ),
                TemplatePhase(
                    "Implementation",
                    "Build automation scripts",
                    ["Create scripts", "Add error handling", "Test thoroughly"],
                    6.0
                ),
                TemplatePhase(
                    "Scheduling",
                    "Schedule and monitor automated tasks",
                    ["Setup scheduler", "Logging", "Notifications"],
                    2.0
                ),
                TemplatePhase(
                    "Refinement",
                    "Monitor and improve automation",
                    ["Monitor performance", "Handle edge cases", "Optimize"],
                    1.0
                ),
            ],
            example_files=["automation.py", "tasks.py", "scheduler.py", "logger.py"],
            success_criteria=[
                "Tasks run on schedule",
                "Errors are properly logged",
                "Performance is acceptable",
                "No manual intervention needed",
                "Results are accurate"
            ],
            best_for="Business professionals automating workflows"
        )
    
    def _create_rest_api_template(self) -> ProjectTemplate:
        """REST API template (simplified)."""
        return ProjectTemplate(
            id="simple_rest_api",
            name="Simple REST API",
            description="Basic CRUD API for learning REST principles",
            category=TemplateCategory.API_SERVICE,
            difficulty_level="beginner",
            estimated_hours=8,
            technologies=["Python", "Flask", "SQLite"],
            requirements=[
                TemplateRequirement("flask", ">=2.3.0", "Web framework"),
                TemplateRequirement("flask-sqlalchemy", ">=3.0.0", "Database ORM"),
            ],
            workflow_phases=[
                TemplatePhase(
                    "Setup",
                    "Initialize Flask project structure",
                    ["Create app", "Setup database", "Configure routes"],
                    2.0
                ),
                TemplatePhase(
                    "CRUD Operations",
                    "Implement create, read, update, delete endpoints",
                    ["GET endpoints", "POST endpoint", "PUT/DELETE endpoints"],
                    4.0
                ),
                TemplatePhase(
                    "Testing & Docs",
                    "Test API and write documentation",
                    ["Test endpoints", "Write docs", "Example requests"],
                    2.0
                ),
            ],
            example_files=["app.py", "models.py", "routes.py", "test_api.py"],
            success_criteria=[
                "All CRUD operations work",
                "API returns proper status codes",
                "Documentation is clear",
                "Error handling works",
                "Data is persisted"
            ],
            best_for="Beginners learning API development"
        )
    
    def _create_dashboard_template(self) -> ProjectTemplate:
        """Dashboard template."""
        return ProjectTemplate(
            id="analytics_dashboard",
            name="Analytics Dashboard",
            description="Real-time analytics dashboard with charts and metrics",
            category=TemplateCategory.DASHBOARD,
            difficulty_level="intermediate",
            estimated_hours=20,
            technologies=["React", "D3.js", "Python", "Websockets"],
            requirements=[
                TemplateRequirement("plotly", ">=5.0.0", "Visualization"),
                TemplateRequirement("fastapi", ">=0.100.0", "Backend"),
            ],
            workflow_phases=[
                TemplatePhase(
                    "Design",
                    "Design dashboard layout and metrics",
                    ["Define KPIs", "Layout design", "Color scheme"],
                    4.0
                ),
                TemplatePhase(
                    "Backend",
                    "Create data aggregation endpoints",
                    ["Data sources", "Aggregation", "Caching"],
                    6.0
                ),
                TemplatePhase(
                    "Frontend",
                    "Build dashboard UI with charts",
                    ["Component creation", "Chart integration", "Styling"],
                    7.0
                ),
                TemplatePhase(
                    "Real-time Updates",
                    "Add WebSocket for live updates",
                    ["WebSocket setup", "Data streaming", "Refresh logic"],
                    3.0
                ),
            ],
            example_files=["dashboard.py", "metrics.py", "Dashboard.tsx", "Chart.tsx"],
            success_criteria=[
                "Dashboard displays all KPIs",
                "Charts update in real-time",
                "Performance is smooth",
                "Responsive design works",
                "Data is accurate"
            ],
            best_for="Analysts and business managers"
        )
    
    def _create_documentation_site_template(self) -> ProjectTemplate:
        """Documentation site template."""
        return ProjectTemplate(
            id="documentation_site",
            name="Project Documentation Site",
            description="Professional documentation site with search and versioning",
            category=TemplateCategory.DOCUMENTATION,
            difficulty_level="beginner",
            estimated_hours=10,
            technologies=["MkDocs", "Markdown", "Python"],
            requirements=[
                TemplateRequirement("mkdocs", ">=1.4.0", "Documentation generator"),
                TemplateRequirement("mkdocs-material", ">=9.0.0", "Theme"),
            ],
            workflow_phases=[
                TemplatePhase(
                    "Setup",
                    "Initialize MkDocs project",
                    ["Create project", "Select theme", "Configure"],
                    2.0
                ),
                TemplatePhase(
                    "Content Creation",
                    "Write comprehensive documentation",
                    ["User guide", "API reference", "Examples"],
                    5.0
                ),
                TemplatePhase(
                    "Organization",
                    "Organize docs with navigation",
                    ["Structure docs", "Add navigation", "Cross-linking"],
                    2.0
                ),
                TemplatePhase(
                    "Publishing",
                    "Deploy documentation",
                    ["Build site", "Deploy", "Setup CI/CD"],
                    1.0
                ),
            ],
            example_files=["mkdocs.yml", "index.md", "user_guide.md", "api_reference.md"],
            success_criteria=[
                "Documentation is comprehensive",
                "Site is easy to navigate",
                "Search functionality works",
                "Content is up-to-date",
                "Examples are clear"
            ],
            best_for="Project maintainers and technical writers"
        )


def get_template_registry() -> TemplateRegistry:
    """Get or create the global template registry.
    
    Returns:
        TemplateRegistry instance with all templates loaded.
    """
    return TemplateRegistry()
