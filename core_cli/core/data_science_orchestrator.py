"""
Data Science Agent Integration - Phase 5.3 Week 4

Master orchestrator for complete ML project generation and management
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ProjectStatus(Enum):
    """Project lifecycle status"""
    CREATED = "created"
    CONFIGURED = "configured"
    TRAINING = "training"
    EVALUATING = "evaluating"
    DEPLOYED = "deployed"
    SERVING = "serving"
    ARCHIVED = "archived"


@dataclass
class MLProjectWorkflow:
    """Complete ML project workflow"""
    project_id: str
    project_name: str
    project_type: str
    framework: str
    status: ProjectStatus
    created_at: datetime
    config: Dict[str, Any]
    
    # Components
    data_science_agent_config: Optional[Dict] = None
    feature_engineer_config: Optional[Dict] = None
    model_trainer_config: Optional[Dict] = None
    metrics_config: Optional[Dict] = None
    validator_config: Optional[Dict] = None
    experiment_config: Optional[Dict] = None
    pipeline_config: Optional[Dict] = None
    model_export_config: Optional[Dict] = None
    deployment_config: Optional[Dict] = None
    registry_config: Optional[Dict] = None


class DataScienceOrchestrator:
    """Orchestrate complete ML workflow across Phase 5.3 components"""
    
    def __init__(self):
        """Initialize orchestrator"""
        self.projects: Dict[str, MLProjectWorkflow] = {}
        self.execution_logs: Dict[str, List[Dict[str, Any]]] = {}
    
    def get_complete_workflow_code(self) -> str:
        """Generate complete end-to-end workflow code"""
        return """
import sys
sys.path.insert(0, 'appshell')

from agents.data_science_agent import get_data_science_agent, ProjectType, MLFramework, DataType
from core.feature_engineer import get_feature_engineer
from core.model_trainer import get_model_trainer
from core.metrics_calculator import get_metric_calculator, MetricCategory
from core.cross_validator import get_cross_validator, CVStrategy
from core.experiment_tracker import get_experiment_tracker
from core.visualization_engine import get_visualization_engine
from core.model_exporter import get_model_exporter
from core.pipeline_builder import get_pipeline_builder
from core.deployment_generator import get_deployment_generator
from core.model_registry import get_model_registry, ModelStage, ModelQuality
from core.serving_orchestrator import get_serving_orchestrator, InferenceMode

import pandas as pd
import numpy as np
from datetime import datetime

# Initialize all components
print("Initializing ML components...")
agent = get_data_science_agent()
engineer = get_feature_engineer()
trainer = get_model_trainer()
calculator = get_metric_calculator()
validator = get_cross_validator()
tracker = get_experiment_tracker()
visualizer = get_visualization_engine()
exporter = get_model_exporter()
builder = get_pipeline_builder()
deployer = get_deployment_generator()
registry = get_model_registry()
orchestrator = get_serving_orchestrator()

# STEP 1: Generate ML Project
print("\\n[1/8] Generating ML project...")
project = agent.generate_project(
    name='iris_classification_production',
    project_type=ProjectType.CLASSIFICATION,
    framework=MLFramework.SCIKIT_LEARN,
    data_type=DataType.TABULAR,
    problem_description='Production ML for iris classification',
    target_metric='accuracy'
)
print(f"✓ Generated project with {len(project.models)} models")

# STEP 2: Feature Engineering
print("\\n[2/8] Engineering features...")
plan = engineer.create_feature_engineering_plan(
    name='iris_features',
    feature_types={},
    scaling_strategy='standard',
    feature_selection=True,
    interaction_features=True
)
print(f"✓ Created feature engineering plan")

# STEP 3: Model Training
print("\\n[3/8] Training models...")
training_script = trainer.get_training_script('random_forest', 'scikit_learn')
print(f"✓ Generated training script ({len(training_script)} chars)")

# STEP 4: Cross-Validation
print("\\n[4/8] Setting up cross-validation...")
folds = validator.create_folds(150, 5, CVStrategy.STRATIFIED_KFOLD)
print(f"✓ Created {len(folds)} validation folds")

# STEP 5: Experiment Tracking
print("\\n[5/8] Setting up experiment tracking...")
experiment = tracker.create_experiment(
    'exp_iris_001',
    project.config,
    project.metrics,
    'Initial production model'
)
print(f"✓ Created experiment: {experiment.experiment_id}")

# STEP 6: Metrics & Visualization
print("\\n[6/8] Setting up metrics & visualization...")
cm_code = calculator.get_classification_metrics_code()
viz_roc = visualizer.get_roc_curve_code()
print(f"✓ Prepared metrics and visualizations")

# STEP 7: Model Export & Registry
print("\\n[7/8] Registering model...")
from core.model_exporter import ModelMetadata, ModelFramework as ExpFramework
metadata = ModelMetadata(
    model_name='iris_classifier',
    version='1.0.0',
    framework=ExpFramework.SCIKIT_LEARN,
    created_at=datetime.now(),
    trained_by='ml_orchestrator',
    training_duration=45.2,
    training_samples=120,
    input_shape={'rows': 120, 'cols': 4},
    output_shape={'rows': 120, 'cols': 1},
    performance_metrics={'accuracy': 0.96, 'f1': 0.95},
    hyperparameters={'n_estimators': 100},
    feature_names=['sepal_length', 'sepal_width', 'petal_length', 'petal_width']
)

artifact = exporter.register_model('model_iris_v1', metadata, 'models/iris_classifier.joblib')
registry_entry = registry.register_model(
    'model_iris_v1',
    'iris_classifier',
    '1.0.0',
    'scikit_learn',
    'classification',
    'models/iris_classifier.joblib',
    'ml_orchestrator',
    quality=ModelQuality.BETA,
    metrics={'accuracy': 0.96}
)
print(f"✓ Registered model: {registry_entry.model_id}")

# STEP 8: Deployment
print("\\n[8/8] Setting up deployment...")
from core.deployment_generator import DeploymentPlatform
deployment = deployer.create_deployment(
    'iris_classifier',
    DeploymentPlatform.FASTAPI,
    'models/iris_classifier.joblib'
)

endpoint = orchestrator.register_endpoint(
    'endpoint_iris_v1',
    'model_iris_v1',
    '1.0.0',
    'http://localhost',
    8000,
    'fastapi'
)

config = orchestrator.create_inference_config(
    'model_iris_v1',
    '1.0.0',
    InferenceMode.REAL_TIME
)

print(f"✓ Registered endpoint: {endpoint.endpoint_id}")

# Summary
print("\\n" + "="*70)
print("✅ COMPLETE ML WORKFLOW INITIALIZED")
print("="*70)
print(f"\\nProject: {project.name}")
print(f"Framework: {project.framework.value}")
print(f"Models: {len(project.models)}")
print(f"Experiment: {experiment.experiment_id}")
print(f"Registry Entry: {registry_entry.model_id}")
print(f"Endpoint: {endpoint.endpoint_id}")
print(f"\\nReady for training, evaluation, and production deployment!")
"""
    
    def create_project(
        self,
        project_id: str,
        project_name: str,
        project_type: str,
        framework: str
    ) -> MLProjectWorkflow:
        """Create ML project workflow"""
        workflow = MLProjectWorkflow(
            project_id=project_id,
            project_name=project_name,
            project_type=project_type,
            framework=framework,
            status=ProjectStatus.CREATED,
            created_at=datetime.now(),
            config={}
        )
        
        self.projects[project_id] = workflow
        self.execution_logs[project_id] = []
        
        logger.info(f"Created project: {project_id}")
        
        return workflow
    
    def configure_step(
        self,
        project_id: str,
        step_name: str,
        config: Dict[str, Any]
    ) -> bool:
        """Configure workflow step"""
        if project_id not in self.projects:
            logger.error(f"Project not found: {project_id}")
            return False
        
        project = self.projects[project_id]
        
        if step_name == "data_science_agent":
            project.data_science_agent_config = config
        elif step_name == "feature_engineer":
            project.feature_engineer_config = config
        elif step_name == "model_trainer":
            project.model_trainer_config = config
        elif step_name == "metrics":
            project.metrics_config = config
        elif step_name == "validator":
            project.validator_config = config
        elif step_name == "experiment":
            project.experiment_config = config
        elif step_name == "pipeline":
            project.pipeline_config = config
        elif step_name == "export":
            project.model_export_config = config
        elif step_name == "deployment":
            project.deployment_config = config
        elif step_name == "registry":
            project.registry_config = config
        
        self.log_execution(project_id, f"Configured {step_name}", config)
        
        return True
    
    def update_status(
        self,
        project_id: str,
        status: ProjectStatus
    ) -> bool:
        """Update project status"""
        if project_id not in self.projects:
            logger.error(f"Project not found: {project_id}")
            return False
        
        self.projects[project_id].status = status
        self.log_execution(project_id, f"Status: {status.value}", {})
        
        logger.info(f"Updated {project_id} status to {status.value}")
        
        return True
    
    def log_execution(
        self,
        project_id: str,
        event: str,
        details: Dict[str, Any]
    ) -> None:
        """Log workflow execution"""
        if project_id in self.execution_logs:
            self.execution_logs[project_id].append({
                'timestamp': datetime.now(),
                'event': event,
                'details': details
            })
    
    def get_execution_log(self, project_id: str) -> List[Dict[str, Any]]:
        """Get execution log"""
        return self.execution_logs.get(project_id, [])
    
    def get_project(self, project_id: str) -> Optional[MLProjectWorkflow]:
        """Get project"""
        return self.projects.get(project_id)


# Singleton factory
_orchestrator_instance: Optional[DataScienceOrchestrator] = None


def get_data_science_orchestrator() -> DataScienceOrchestrator:
    """Get DataScienceOrchestrator singleton"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = DataScienceOrchestrator()
        logger.info("DataScienceOrchestrator initialized")
    return _orchestrator_instance
