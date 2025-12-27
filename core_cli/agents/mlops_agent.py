"""
MLOpsAgent - Machine Learning Operations & Lifecycle Management

Specialized agent for handling ML model deployment, monitoring, versioning, 
experiment tracking, model registry, and production ML workflows.

Phase 5.5 Implementation
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import logging
from agents.base import BaseAgent, AgentContext, AgentResult
from core.security_validator import validate_agent_input, SecurityViolation

logger = logging.getLogger(__name__)


class DeploymentEnvironment(Enum):
    """Deployment environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    CANARY = "canary"
    A_B_TEST = "a_b_test"


class MonitoringMetricType(Enum):
    """Types of metrics to monitor"""
    MODEL_PERFORMANCE = "model_performance"
    DATA_DRIFT = "data_drift"
    PREDICTION_DRIFT = "prediction_drift"
    FEATURE_IMPORTANCE = "feature_importance"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    RESOURCE_UTILIZATION = "resource_utilization"


class ExperimentStatus(Enum):
    """Experiment lifecycle status"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ModelStrategy(Enum):
    """Model serving strategies"""
    DIRECT_SERVING = "direct_serving"
    BATCH_PREDICTION = "batch_prediction"
    STREAM_PROCESSING = "stream_processing"
    ENSEMBLE = "ensemble"
    MULTI_ARM_BANDIT = "multi_arm_bandit"
    SHADOW_MODE = "shadow_mode"


@dataclass
class ModelMetadata:
    """ML model metadata and versioning"""
    model_name: str
    version: str
    framework: str  # pytorch, tensorflow, sklearn, xgboost
    input_schema: Dict[str, str]
    output_schema: Dict[str, str]
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    training_data_hash: str = ""
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    onnx_compatible: bool = False
    model_size_mb: float = 0.0
    inference_time_ms: float = 0.0


@dataclass
class ExperimentTracking:
    """ML experiment tracking configuration"""
    experiment_id: str
    experiment_name: str
    project_id: str
    status: ExperimentStatus = ExperimentStatus.RUNNING
    parameters: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    parent_experiment_id: Optional[str] = None


@dataclass
class ModelRegistry:
    """Model registry entry"""
    model_id: str
    model_name: str
    versions: List[ModelMetadata] = field(default_factory=list)
    current_version: Optional[str] = None
    production_version: Optional[str] = None
    staging_version: Optional[str] = None
    archived_versions: List[str] = field(default_factory=list)
    owner: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    approval_status: str = "pending"  # pending, approved, rejected


@dataclass
class DeploymentConfig:
    """ML model deployment configuration"""
    model_id: str
    version: str
    environment: DeploymentEnvironment
    serving_strategy: ModelStrategy
    replicas: int = 1
    cpu_request: str = "100m"
    memory_request: str = "256Mi"
    cpu_limit: str = "1000m"
    memory_limit: str = "2Gi"
    container_image: str = ""
    health_check_endpoint: str = "/health"
    prediction_endpoint: str = "/predict"
    batch_endpoint: str = "/batch_predict"
    enable_monitoring: bool = True
    enable_logging: bool = True
    enable_tracing: bool = True
    autoscale_enabled: bool = True
    min_replicas: int = 1
    max_replicas: int = 10
    target_cpu_utilization: int = 70
    deployment_timeout_seconds: int = 300


@dataclass
class MonitoringConfig:
    """Model monitoring configuration"""
    model_id: str
    version: str
    metrics_to_track: List[MonitoringMetricType] = field(default_factory=list)
    alert_thresholds: Dict[str, float] = field(default_factory=dict)
    data_drift_threshold: float = 0.05
    prediction_drift_threshold: float = 0.05
    performance_degradation_threshold: float = 0.10
    latency_threshold_ms: float = 1000.0
    error_rate_threshold: float = 0.01
    data_drift_check_frequency: str = "daily"  # hourly, daily, weekly
    performance_check_frequency: str = "daily"
    sampling_rate: float = 1.0
    store_predictions: bool = True
    store_features: bool = True
    store_explanations: bool = True


@dataclass
class PromotionPolicy:
    """Model promotion policy between environments"""
    source_environment: DeploymentEnvironment
    target_environment: DeploymentEnvironment
    approval_required: bool = True
    approvers: List[str] = field(default_factory=list)
    minimum_performance_threshold: Dict[str, float] = field(default_factory=dict)
    minimum_test_coverage: float = 0.80
    require_load_testing: bool = True
    require_stress_testing: bool = False
    shadow_mode_duration_hours: int = 24
    canary_traffic_percentage: int = 10
    rollback_on_degradation: bool = True
    auto_promote_on_success: bool = False


@dataclass
class BatchPredictionJob:
    """Batch prediction job configuration"""
    job_id: str
    model_id: str
    model_version: str
    input_data_path: str
    output_data_path: str
    batch_size: int = 1000
    timeout_seconds: int = 3600
    retry_count: int = 3
    job_status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    rows_processed: int = 0
    rows_failed: int = 0
    execution_time_seconds: float = 0.0


@dataclass
class ModelExplainability:
    """Model explainability configuration"""
    model_id: str
    explanation_method: str = "shap"  # shap, lime, integrated_gradients
    feature_importance_enabled: bool = True
    prediction_explanation_enabled: bool = True
    global_explanation_enabled: bool = True
    local_explanation_enabled: bool = True
    explanation_sample_size: int = 1000
    background_data_size: int = 100


class MLOpsAgent:
    """
    Machine Learning Operations Agent
    
    Handles:
    - Model versioning and registry
    - Experiment tracking and management
    - Model deployment automation
    - Production monitoring and alerting
    - Model promotion and rollback
    - Data drift detection
    - Performance tracking
    - A/B testing and canary deployments
    - Batch prediction jobs
    - Model explainability
    """
    
    def __init__(self):
        """Initialize MLOps Agent"""
        self.name = "MLOpsAgent"
        self.description = "Handles ML model lifecycle, deployment, monitoring, and operations"
        self.capabilities = {
            "model_versioning": "Version and manage ML models",
            "experiment_tracking": "Track and manage ML experiments",
            "model_registry": "Maintain central model registry",
            "deployment": "Deploy models to various environments",
            "monitoring": "Monitor model performance in production",
            "data_drift": "Detect data drift and distribution changes",
            "performance_tracking": "Track model performance metrics",
            "a_b_testing": "Conduct A/B tests and canary deployments",
            "batch_prediction": "Execute batch prediction jobs",
            "explainability": "Generate model explanations",
            "rollback": "Rollback to previous model versions",
            "promotion": "Promote models between environments"
        }
        self.models_registry: Dict[str, ModelRegistry] = {}
        self.experiments: Dict[str, ExperimentTracking] = {}
        self.deployments: Dict[str, DeploymentConfig] = {}
        self.monitoring_configs: Dict[str, MonitoringConfig] = {}
        self.batch_jobs: Dict[str, BatchPredictionJob] = {}
    
    def register_model(
        self,
        model_metadata: ModelMetadata,
        description: str = "",
        tags: Optional[List[str]] = None
    ) -> ModelRegistry:
        """Register a new model in the model registry"""
        model_id = f"{model_metadata.model_name}_{model_metadata.version}"
        
        registry_entry = ModelRegistry(
            model_id=model_id,
            model_name=model_metadata.model_name,
            versions=[model_metadata],
            current_version=model_metadata.version,
            owner=model_metadata.created_by,
            description=description,
            tags=tags or []
        )
        
        self.models_registry[model_id] = registry_entry
        logger.info(f"Registered model: {model_id}")
        return registry_entry
    
    def start_experiment(
        self,
        experiment_name: str,
        project_id: str,
        parameters: Dict[str, Any],
        tags: Optional[List[str]] = None
    ) -> ExperimentTracking:
        """Start a new ML experiment"""
        experiment_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        experiment = ExperimentTracking(
            experiment_id=experiment_id,
            experiment_name=experiment_name,
            project_id=project_id,
            parameters=parameters,
            tags=tags or []
        )
        
        self.experiments[experiment_id] = experiment
        logger.info(f"Started experiment: {experiment_id}")
        return experiment
    
    def log_experiment_metrics(
        self,
        experiment_id: str,
        metrics: Dict[str, float]
    ) -> bool:
        """Log metrics for an experiment"""
        if experiment_id not in self.experiments:
            logger.error(f"Experiment {experiment_id} not found")
            return False
        
        self.experiments[experiment_id].metrics.update(metrics)
        logger.info(f"Logged metrics for experiment {experiment_id}")
        return True
    
    def end_experiment(
        self,
        experiment_id: str,
        status: ExperimentStatus = ExperimentStatus.COMPLETED
    ) -> bool:
        """End an experiment"""
        if experiment_id not in self.experiments:
            logger.error(f"Experiment {experiment_id} not found")
            return False
        
        experiment = self.experiments[experiment_id]
        experiment.status = status
        experiment.ended_at = datetime.now()
        experiment.duration_seconds = (
            experiment.ended_at - experiment.started_at
        ).total_seconds()
        
        logger.info(f"Ended experiment {experiment_id} with status {status.value}")
        return True
    
    def create_deployment(
        self,
        model_id: str,
        version: str,
        environment: DeploymentEnvironment,
        serving_strategy: ModelStrategy = ModelStrategy.DIRECT_SERVING,
        replicas: int = 1
    ) -> DeploymentConfig:
        """Create a deployment configuration"""
        deployment_id = f"{model_id}_{environment.value}_{datetime.now().timestamp()}"
        
        deployment = DeploymentConfig(
            model_id=model_id,
            version=version,
            environment=environment,
            serving_strategy=serving_strategy,
            replicas=replicas
        )
        
        self.deployments[deployment_id] = deployment
        logger.info(f"Created deployment: {deployment_id}")
        return deployment
    
    def configure_monitoring(
        self,
        model_id: str,
        version: str,
        metrics: List[MonitoringMetricType],
        alert_thresholds: Optional[Dict[str, float]] = None
    ) -> MonitoringConfig:
        """Configure monitoring for a deployed model"""
        monitoring_id = f"{model_id}_{version}_monitoring"
        
        monitoring = MonitoringConfig(
            model_id=model_id,
            version=version,
            metrics_to_track=metrics,
            alert_thresholds=alert_thresholds or {}
        )
        
        self.monitoring_configs[monitoring_id] = monitoring
        logger.info(f"Configured monitoring: {monitoring_id}")
        return monitoring
    
    def submit_batch_job(
        self,
        model_id: str,
        model_version: str,
        input_path: str,
        output_path: str,
        batch_size: int = 1000
    ) -> BatchPredictionJob:
        """Submit a batch prediction job"""
        job_id = f"batch_{model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        job = BatchPredictionJob(
            job_id=job_id,
            model_id=model_id,
            model_version=model_version,
            input_data_path=input_path,
            output_data_path=output_path,
            batch_size=batch_size
        )
        
        self.batch_jobs[job_id] = job
        logger.info(f"Submitted batch job: {job_id}")
        return job
    
    def get_experiment_summary(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of an experiment"""
        if experiment_id not in self.experiments:
            return None
        
        exp = self.experiments[experiment_id]
        return {
            "experiment_id": exp.experiment_id,
            "experiment_name": exp.experiment_name,
            "status": exp.status.value,
            "parameters": exp.parameters,
            "metrics": exp.metrics,
            "duration_seconds": exp.duration_seconds,
            "tags": exp.tags
        }
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get model information from registry"""
        if model_id not in self.models_registry:
            return None
        
        registry = self.models_registry[model_id]
        return {
            "model_id": registry.model_id,
            "model_name": registry.model_name,
            "current_version": registry.current_version,
            "production_version": registry.production_version,
            "staging_version": registry.staging_version,
            "owner": registry.owner,
            "version_count": len(registry.versions),
            "last_updated": registry.last_updated.isoformat()
        }
    
    def promote_model(
        self,
        model_id: str,
        version: str,
        target_environment: DeploymentEnvironment,
        approval_status: str = "approved"
    ) -> bool:
        """Promote model to target environment"""
        if model_id not in self.models_registry:
            logger.error(f"Model {model_id} not found")
            return False
        
        registry = self.models_registry[model_id]
        
        if target_environment == DeploymentEnvironment.PRODUCTION:
            registry.production_version = version
        elif target_environment == DeploymentEnvironment.STAGING:
            registry.staging_version = version
        
        registry.approval_status = approval_status
        logger.info(f"Promoted {model_id} v{version} to {target_environment.value}")
        return True
    
    def rollback_model(
        self,
        model_id: str,
        environment: DeploymentEnvironment,
        previous_version: str
    ) -> bool:
        """Rollback model to previous version"""
        if model_id not in self.models_registry:
            logger.error(f"Model {model_id} not found")
            return False
        
        registry = self.models_registry[model_id]
        
        if environment == DeploymentEnvironment.PRODUCTION:
            registry.production_version = previous_version
        elif environment == DeploymentEnvironment.STAGING:
            registry.staging_version = previous_version
        
        logger.info(f"Rolled back {model_id} to v{previous_version} in {environment.value}")
        return True
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MLOps operations based on context"""
        # Validate input for security violations
        try:
            validate_agent_input(lambda self, ctx: None)(self, context)
        except SecurityViolation as e:
            logger.error(f"[{self.name}] Security validation failed: {str(e)}")
            return {
                "agent": self.name,
                "status": "failed",
                "error": f"Security validation failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        operation = context.get("operation", "")
        
        result = {
            "agent": self.name,
            "operation": operation,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "data": {}
        }
        
        try:
            if operation == "register_model":
                metadata = context.get("model_metadata")
                registry = self.register_model(metadata)
                result["data"] = {
                    "model_id": registry.model_id,
                    "version": metadata.version
                }
            
            elif operation == "start_experiment":
                experiment = self.start_experiment(
                    context.get("experiment_name"),
                    context.get("project_id"),
                    context.get("parameters", {})
                )
                result["data"] = {"experiment_id": experiment.experiment_id}
            
            elif operation == "log_metrics":
                success = self.log_experiment_metrics(
                    context.get("experiment_id"),
                    context.get("metrics", {})
                )
                result["data"] = {"metrics_logged": success}
            
            elif operation == "create_deployment":
                deployment = self.create_deployment(
                    context.get("model_id"),
                    context.get("version"),
                    DeploymentEnvironment(context.get("environment", "staging"))
                )
                result["data"] = {
                    "deployment_id": context.get("model_id"),
                    "environment": deployment.environment.value
                }
            
            elif operation == "submit_batch_job":
                job = self.submit_batch_job(
                    context.get("model_id"),
                    context.get("version"),
                    context.get("input_path"),
                    context.get("output_path")
                )
                result["data"] = {"job_id": job.job_id}
            
            else:
                result["status"] = "unknown_operation"
        
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"MLOps operation failed: {e}")
        
        return result


# Export main agent class
__all__ = [
    "MLOpsAgent",
    "ModelMetadata",
    "ExperimentTracking",
    "DeploymentConfig",
    "MonitoringConfig",
    "BatchPredictionJob",
    "DeploymentEnvironment",
    "MonitoringMetricType",
    "ExperimentStatus"
]
