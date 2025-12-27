"""
DataScienceAgent - ML/Data Science Project Generator

Phase 5.3 Implementation
Generates complete ML project scaffolding with model training pipelines
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


class MLFramework(Enum):
    """Supported ML frameworks"""
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    SCIKIT_LEARN = "scikit_learn"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    HUGGINGFACE = "huggingface"


class ProjectType(Enum):
    """ML project types"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    NLP = "nlp"
    COMPUTER_VISION = "computer_vision"
    TIME_SERIES = "time_series"
    CLUSTERING = "clustering"


class DataType(Enum):
    """Data modality types"""
    TABULAR = "tabular"
    IMAGE = "image"
    TEXT = "text"
    AUDIO = "audio"
    TIME_SERIES = "time_series"
    MIXED = "mixed"


@dataclass
class MLProjectSpec:
    """ML project specification"""
    name: str
    project_type: ProjectType
    framework: MLFramework
    data_type: DataType
    target_metric: str  # e.g., "accuracy", "rmse", "f1"
    dataset_size: str  # "small" (< 10k), "medium" (10k-1M), "large" (> 1M)
    problem_description: str
    features_count: int = 0
    classes_count: int = 0  # For classification
    test_split: float = 0.2
    val_split: float = 0.1
    random_seed: int = 42
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DataProcessingPipeline:
    """Data processing configuration"""
    name: str
    raw_data_path: str
    processed_data_path: str
    steps: List[str] = field(default_factory=list)
    scaling_method: Optional[str] = None  # "standard", "minmax", "robust"
    handling_missing: str = "mean"  # "mean", "median", "drop", "forward_fill"
    outlier_method: Optional[str] = None  # "iqr", "zscore"
    categorical_encoding: str = "onehot"  # "onehot", "label", "target"
    feature_selection: Optional[str] = None  # "correlation", "mutual_info", "rfe"


@dataclass
class ModelConfig:
    """Model training configuration"""
    model_name: str
    model_type: str  # e.g., "random_forest", "neural_network", "xgboost"
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    validation_strategy: str = "stratified_kfold"  # "kfold", "stratified_kfold", "time_series_split"
    cv_folds: int = 5
    early_stopping: bool = True
    early_stopping_metric: str = "val_loss"
    early_stopping_patience: int = 10
    batch_size: Optional[int] = None
    learning_rate: Optional[float] = None
    epochs: int = 100


@dataclass
class EvaluationFramework:
    """Model evaluation configuration"""
    primary_metric: str  # "accuracy", "rmse", "auc", etc.
    secondary_metrics: List[str] = field(default_factory=list)
    test_metrics: List[str] = field(default_factory=list)
    confusion_matrix: bool = True
    feature_importance: bool = True
    shap_analysis: bool = False
    cross_validation: bool = True
    threshold_optimization: bool = False
    calibration_analysis: bool = False


@dataclass
class ProjectTemplate:
    """Complete project template"""
    spec: MLProjectSpec
    data_pipeline: DataProcessingPipeline
    models: List[ModelConfig]
    evaluation: EvaluationFramework
    requirements: List[str] = field(default_factory=list)
    config_yaml: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class MLProjectGenerator:
    """Generates complete ML project scaffolding"""
    
    # Classification templates
    CLASSIFICATION_TEMPLATES = {
        "binary_sklearn": {
            "framework": MLFramework.SCIKIT_LEARN,
            "models": ["logistic_regression", "random_forest", "gradient_boosting"],
            "evaluation": ["accuracy", "precision", "recall", "f1", "auc"],
            "requirements": ["scikit-learn", "pandas", "numpy", "matplotlib", "seaborn"]
        },
        "multiclass_torch": {
            "framework": MLFramework.PYTORCH,
            "models": ["neural_network", "resnet"],
            "evaluation": ["accuracy", "f1_weighted", "confusion_matrix"],
            "requirements": ["torch", "torchvision", "pandas", "numpy", "tensorboard"]
        },
        "xgboost_classifier": {
            "framework": MLFramework.XGBOOST,
            "models": ["xgboost", "lightgbm"],
            "evaluation": ["accuracy", "auc", "feature_importance"],
            "requirements": ["xgboost", "lightgbm", "scikit-learn", "pandas", "numpy"]
        }
    }
    
    # Regression templates
    REGRESSION_TEMPLATES = {
        "linear_sklearn": {
            "framework": MLFramework.SCIKIT_LEARN,
            "models": ["linear_regression", "ridge", "lasso"],
            "evaluation": ["rmse", "mse", "mae", "r2"],
            "requirements": ["scikit-learn", "pandas", "numpy", "matplotlib"]
        },
        "gradient_boost": {
            "framework": MLFramework.XGBOOST,
            "models": ["xgboost", "lightgbm", "gradient_boosting"],
            "evaluation": ["rmse", "mae", "r2"],
            "requirements": ["xgboost", "lightgbm", "scikit-learn", "pandas"]
        },
        "neural_network": {
            "framework": MLFramework.TENSORFLOW,
            "models": ["dense_nn", "dropout_regularized"],
            "evaluation": ["mse", "mae"],
            "requirements": ["tensorflow", "keras", "pandas", "numpy", "tensorboard"]
        }
    }
    
    # NLP templates
    NLP_TEMPLATES = {
        "text_classification": {
            "framework": MLFramework.HUGGINGFACE,
            "models": ["bert", "distilbert", "roberta"],
            "evaluation": ["accuracy", "f1", "confusion_matrix"],
            "requirements": ["transformers", "torch", "datasets", "pandas"]
        },
        "named_entity_recognition": {
            "framework": MLFramework.PYTORCH,
            "models": ["bilstm_crf", "transformer_based"],
            "evaluation": ["precision", "recall", "f1"],
            "requirements": ["torch", "transformers", "pandas", "numpy"]
        },
        "sentiment_analysis": {
            "framework": MLFramework.HUGGINGFACE,
            "models": ["distilbert", "bert"],
            "evaluation": ["accuracy", "f1", "roc_auc"],
            "requirements": ["transformers", "torch", "sklearn", "pandas"]
        }
    }
    
    # Computer Vision templates
    CV_TEMPLATES = {
        "image_classification": {
            "framework": MLFramework.PYTORCH,
            "models": ["resnet50", "efficientnet", "vit"],
            "evaluation": ["accuracy", "top5_accuracy", "confusion_matrix"],
            "requirements": ["torch", "torchvision", "pillow", "pandas", "numpy"]
        },
        "object_detection": {
            "framework": MLFramework.PYTORCH,
            "models": ["yolov5", "faster_rcnn"],
            "evaluation": ["map", "precision", "recall"],
            "requirements": ["torch", "torchvision", "opencv-python", "pandas"]
        },
        "semantic_segmentation": {
            "framework": MLFramework.PYTORCH,
            "models": ["unet", "deeplabv3"],
            "evaluation": ["iou", "dice", "pixel_accuracy"],
            "requirements": ["torch", "torchvision", "opencv-python", "pandas"]
        }
    }
    
    # Time Series templates
    TS_TEMPLATES = {
        "forecasting": {
            "framework": MLFramework.PYTORCH,
            "models": ["lstm", "transformer", "tcn"],
            "evaluation": ["mae", "rmse", "mape"],
            "requirements": ["torch", "pandas", "numpy", "statsmodels"]
        },
        "anomaly_detection": {
            "framework": MLFramework.SCIKIT_LEARN,
            "models": ["isolation_forest", "autoencoder"],
            "evaluation": ["precision", "recall", "f1"],
            "requirements": ["scikit-learn", "pandas", "numpy"]
        }
    }
    
    # Clustering templates
    CLUSTERING_TEMPLATES = {
        "unsupervised": {
            "framework": MLFramework.SCIKIT_LEARN,
            "models": ["kmeans", "dbscan", "gaussian_mixture"],
            "evaluation": ["silhouette", "davies_bouldin", "calinski_harabasz"],
            "requirements": ["scikit-learn", "pandas", "numpy", "matplotlib"]
        }
    }
    
    def __init__(self):
        """Initialize ML project generator"""
        self.projects: Dict[str, ProjectTemplate] = {}
        self.templates_cache = {
            ProjectType.CLASSIFICATION: self.CLASSIFICATION_TEMPLATES,
            ProjectType.REGRESSION: self.REGRESSION_TEMPLATES,
            ProjectType.NLP: self.NLP_TEMPLATES,
            ProjectType.COMPUTER_VISION: self.CV_TEMPLATES,
            ProjectType.TIME_SERIES: self.TS_TEMPLATES,
            ProjectType.CLUSTERING: self.CLUSTERING_TEMPLATES,
        }
    
    def generate_project(
        self,
        name: str,
        project_type: ProjectType,
        framework: MLFramework,
        data_type: DataType,
        problem_description: str,
        target_metric: str = "accuracy",
        dataset_size: str = "medium"
    ) -> ProjectTemplate:
        """Generate ML project template"""
        
        spec = MLProjectSpec(
            name=name,
            project_type=project_type,
            framework=framework,
            data_type=data_type,
            target_metric=target_metric,
            dataset_size=dataset_size,
            problem_description=problem_description
        )
        
        # Create data processing pipeline
        data_pipeline = DataProcessingPipeline(
            name=f"{name}_pipeline",
            raw_data_path="data/raw/",
            processed_data_path="data/processed/",
            scaling_method="standard" if project_type in [ProjectType.CLUSTERING, ProjectType.REGRESSION] else None,
            handling_missing="mean",
            feature_selection="correlation" if data_type == DataType.TABULAR else None
        )
        
        # Generate models based on type
        models = self._generate_models(project_type, framework)
        
        # Create evaluation framework
        evaluation = self._create_evaluation_framework(project_type, target_metric)
        
        # Generate requirements
        requirements = self._generate_requirements(framework, project_type)
        
        # Create config
        config_yaml = self._create_config(spec, data_pipeline, models, evaluation)
        
        template = ProjectTemplate(
            spec=spec,
            data_pipeline=data_pipeline,
            models=models,
            evaluation=evaluation,
            requirements=requirements,
            config_yaml=config_yaml
        )
        
        self.projects[name] = template
        logger.info(f"Generated ML project: {name} ({project_type.value}, {framework.value})")
        
        return template
    
    def _generate_models(self, project_type: ProjectType, framework: MLFramework) -> List[ModelConfig]:
        """Generate model configurations"""
        models = []
        
        templates_map = {
            ProjectType.CLASSIFICATION: [
                ("logistic_regression", {"C": 1.0, "max_iter": 1000}),
                ("random_forest", {"n_estimators": 100, "max_depth": 10}),
                ("gradient_boosting", {"n_estimators": 100, "learning_rate": 0.1})
            ],
            ProjectType.REGRESSION: [
                ("linear_regression", {}),
                ("random_forest", {"n_estimators": 100, "max_depth": 15}),
                ("gradient_boosting", {"n_estimators": 100, "learning_rate": 0.1})
            ],
            ProjectType.NLP: [
                ("bert", {"max_length": 128, "learning_rate": 2e-5}),
                ("distilbert", {"max_length": 128, "learning_rate": 5e-5})
            ],
            ProjectType.COMPUTER_VISION: [
                ("resnet50", {"pretrained": True, "learning_rate": 1e-4}),
                ("efficientnet", {"pretrained": True, "learning_rate": 1e-4})
            ],
            ProjectType.TIME_SERIES: [
                ("lstm", {"hidden_size": 64, "learning_rate": 1e-3}),
                ("transformer", {"hidden_size": 128, "learning_rate": 1e-3})
            ],
            ProjectType.CLUSTERING: [
                ("kmeans", {"n_clusters": 3, "n_init": 10}),
                ("dbscan", {"eps": 0.5, "min_samples": 5})
            ]
        }
        
        for model_name, hyperparams in templates_map.get(project_type, []):
            model = ModelConfig(
                model_name=model_name,
                model_type=model_name,
                hyperparameters=hyperparams,
                batch_size=32 if project_type in [ProjectType.NLP, ProjectType.COMPUTER_VISION] else None,
                learning_rate=1e-3 if project_type != ProjectType.CLUSTERING else None,
                epochs=100 if project_type in [ProjectType.NLP, ProjectType.COMPUTER_VISION] else 50
            )
            models.append(model)
        
        return models
    
    def _create_evaluation_framework(self, project_type: ProjectType, target_metric: str) -> EvaluationFramework:
        """Create evaluation framework"""
        metrics_map = {
            ProjectType.CLASSIFICATION: ["accuracy", "precision", "recall", "f1", "auc"],
            ProjectType.REGRESSION: ["rmse", "mae", "r2", "mape"],
            ProjectType.NLP: ["accuracy", "f1", "precision", "recall"],
            ProjectType.COMPUTER_VISION: ["accuracy", "precision", "recall", "iou"],
            ProjectType.TIME_SERIES: ["mae", "rmse", "mape"],
            ProjectType.CLUSTERING: ["silhouette", "davies_bouldin"]
        }
        
        secondary_metrics = [m for m in metrics_map.get(project_type, []) if m != target_metric][:3]
        
        return EvaluationFramework(
            primary_metric=target_metric,
            secondary_metrics=secondary_metrics,
            test_metrics=secondary_metrics + [target_metric],
            confusion_matrix=project_type == ProjectType.CLASSIFICATION,
            feature_importance=project_type in [ProjectType.CLASSIFICATION, ProjectType.REGRESSION],
            shap_analysis=project_type in [ProjectType.CLASSIFICATION, ProjectType.REGRESSION],
            cross_validation=True,
            threshold_optimization=project_type == ProjectType.CLASSIFICATION
        )
    
    def _generate_requirements(self, framework: MLFramework, project_type: ProjectType) -> List[str]:
        """Generate requirements list"""
        framework_requirements = {
            MLFramework.PYTORCH: ["torch", "torchvision", "torchaudio"],
            MLFramework.TENSORFLOW: ["tensorflow", "keras"],
            MLFramework.SCIKIT_LEARN: ["scikit-learn"],
            MLFramework.XGBOOST: ["xgboost"],
            MLFramework.LIGHTGBM: ["lightgbm"],
            MLFramework.HUGGINGFACE: ["transformers", "datasets"]
        }
        
        common_requirements = ["pandas", "numpy", "matplotlib", "seaborn", "jupyter", "ipython"]
        
        return framework_requirements.get(framework, []) + common_requirements
    
    def _create_config(
        self,
        spec: MLProjectSpec,
        pipeline: DataProcessingPipeline,
        models: List[ModelConfig],
        evaluation: EvaluationFramework
    ) -> Dict[str, Any]:
        """Create config YAML structure"""
        return {
            "project": {
                "name": spec.name,
                "type": spec.project_type.value,
                "framework": spec.framework.value,
                "data_type": spec.data_type.value,
                "description": spec.problem_description
            },
            "data": {
                "raw_path": pipeline.raw_data_path,
                "processed_path": pipeline.processed_data_path,
                "test_split": spec.test_split,
                "val_split": spec.val_split,
                "random_seed": spec.random_seed,
                "scaling": pipeline.scaling_method,
                "missing_value_strategy": pipeline.handling_missing
            },
            "models": [
                {
                    "name": m.model_name,
                    "type": m.model_type,
                    "hyperparameters": m.hyperparameters,
                    "validation": {
                        "strategy": m.validation_strategy,
                        "folds": m.cv_folds,
                        "early_stopping": m.early_stopping
                    }
                }
                for m in models
            ],
            "evaluation": {
                "primary_metric": evaluation.primary_metric,
                "secondary_metrics": evaluation.secondary_metrics,
                "cross_validation": evaluation.cross_validation,
                "confusion_matrix": evaluation.confusion_matrix,
                "feature_importance": evaluation.feature_importance
            }
        }
    
    def get_project(self, name: str) -> Optional[ProjectTemplate]:
        """Retrieve generated project"""
        return self.projects.get(name)
    
    def list_projects(self) -> List[str]:
        """List all generated projects"""
        return list(self.projects.keys())
    
    def export_project_config(self, name: str) -> str:
        """Export project config as YAML string"""
        project = self.get_project(name)
        if not project:
            return ""
        
        import yaml
        return yaml.dump(project.config_yaml, default_flow_style=False)


# Singleton factory
_generator_instance: Optional[MLProjectGenerator] = None


def get_data_science_agent() -> MLProjectGenerator:
    """Get DataScienceAgent singleton"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = MLProjectGenerator()
        logger.info("DataScienceAgent initialized")
    return _generator_instance
