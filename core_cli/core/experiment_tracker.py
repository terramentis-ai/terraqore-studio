"""
Experiment Tracking & Management - Phase 5.3 Week 2

Track ML experiments, hyperparameters, metrics, and model versioning
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """Experiment status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


@dataclass
class Hyperparameters:
    """Model hyperparameters"""
    params: Dict[str, Any]
    source: str = "manual"  # manual, grid_search, random_search, bayesian
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'params': self.params,
            'source': self.source,
            'notes': self.notes
        }


@dataclass
class ExperimentConfig:
    """Experiment configuration"""
    name: str
    project_type: str
    framework: str
    model_name: str
    dataset_name: str
    test_size: float
    random_state: int
    validation_strategy: str
    n_splits: int
    preprocessing_steps: List[str]
    feature_engineering: List[str]
    hyperparameters: Hyperparameters
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'project_type': self.project_type,
            'framework': self.framework,
            'model_name': self.model_name,
            'dataset_name': self.dataset_name,
            'test_size': self.test_size,
            'random_state': self.random_state,
            'validation_strategy': self.validation_strategy,
            'n_splits': self.n_splits,
            'preprocessing_steps': self.preprocessing_steps,
            'feature_engineering': self.feature_engineering,
            'hyperparameters': self.hyperparameters.to_dict()
        }


@dataclass
class ExperimentMetrics:
    """Experiment metrics and performance"""
    primary_metric_name: str
    primary_metric_value: float
    secondary_metrics: Dict[str, float]
    cv_mean: Optional[float] = None
    cv_std: Optional[float] = None
    training_time: Optional[float] = None  # seconds
    inference_time: Optional[float] = None  # ms per sample
    model_size: Optional[float] = None  # MB
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'primary_metric': {
                'name': self.primary_metric_name,
                'value': self.primary_metric_value
            },
            'secondary_metrics': self.secondary_metrics,
            'cv_mean': self.cv_mean,
            'cv_std': self.cv_std,
            'training_time': self.training_time,
            'inference_time': self.inference_time,
            'model_size': self.model_size
        }


@dataclass
class Experiment:
    """ML Experiment tracking"""
    experiment_id: str
    config: ExperimentConfig
    metrics: ExperimentMetrics
    status: ExperimentStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    artifacts: Dict[str, str] = field(default_factory=dict)  # artifact_name -> path
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'experiment_id': self.experiment_id,
            'config': self.config.to_dict(),
            'metrics': self.metrics.to_dict(),
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'notes': self.notes,
            'tags': self.tags,
            'artifacts': self.artifacts
        }


class ExperimentTracker:
    """Track and manage ML experiments"""
    
    def __init__(self):
        """Initialize experiment tracker"""
        self.experiments: Dict[str, Experiment] = {}
        self.experiment_history: List[str] = []
        self.best_experiments: Dict[str, str] = {}  # metric_name -> experiment_id
    
    def get_tracking_code(self) -> str:
        """Generate experiment tracking code"""
        return """
import json
from datetime import datetime
import logging

# Experiment tracking setup
experiment_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
experiment_log = {
    'id': experiment_id,
    'timestamp': datetime.now().isoformat(),
    'config': {
        'model': 'random_forest',
        'hyperparameters': {
            'n_estimators': 100,
            'max_depth': 10,
            'random_state': 42
        },
        'cv_strategy': 'stratified_kfold',
        'n_splits': 5
    },
    'metrics': {}
}

# Log configuration
logging.basicConfig(
    filename=f'experiments/{experiment_id}.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info(f"Starting experiment: {experiment_id}")

# Train model and track metrics
from sklearn.model_selection import StratifiedKFold
fold_scores = []

skf = StratifiedKFold(n_splits=5)
for fold, (train_idx, test_idx) in enumerate(skf.split(X, y), 1):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    fold_scores.append(score)
    
    logger.info(f"Fold {fold} score: {score:.4f}")

# Record final metrics
import numpy as np
experiment_log['metrics'] = {
    'cv_mean': float(np.mean(fold_scores)),
    'cv_std': float(np.std(fold_scores)),
    'cv_min': float(np.min(fold_scores)),
    'cv_max': float(np.max(fold_scores))
}

# Save experiment log
with open(f'experiments/{experiment_id}.json', 'w') as f:
    json.dump(experiment_log, f, indent=2)

logger.info(f"Experiment completed: {experiment_log['metrics']}")
"""
    
    def get_comparison_code(self) -> str:
        """Generate experiment comparison code"""
        return """
import pandas as pd
import json
import os
from datetime import datetime

# Load all experiments
experiments = []
for filename in os.listdir('experiments'):
    if filename.endswith('.json'):
        with open(f'experiments/{filename}') as f:
            exp = json.load(f)
            experiments.append(exp)

# Create comparison dataframe
df = pd.DataFrame([
    {
        'experiment_id': exp['id'],
        'model': exp['config']['model'],
        'cv_mean': exp['metrics']['cv_mean'],
        'cv_std': exp['metrics']['cv_std'],
        'timestamp': exp['timestamp']
    }
    for exp in experiments
])

# Sort by performance
df_sorted = df.sort_values('cv_mean', ascending=False)
print("Top 5 experiments by CV score:")
print(df_sorted[['experiment_id', 'model', 'cv_mean', 'cv_std']].head())

# Find best experiment
best_exp = df_sorted.iloc[0]
print(f"\\nBest experiment: {best_exp['experiment_id']}")
print(f"Score: {best_exp['cv_mean']:.4f} (+/- {best_exp['cv_std']:.4f})")

# Plot comparison
import matplotlib.pyplot as plt
plt.figure(figsize=(12, 6))
plt.errorbar(range(len(df_sorted)), df_sorted['cv_mean'], 
             yerr=df_sorted['cv_std'], fmt='o-')
plt.xlabel('Experiment')
plt.ylabel('CV Score')
plt.title('Experiment Comparison')
plt.xticks(range(len(df_sorted)), df_sorted['experiment_id'], rotation=45)
plt.tight_layout()
plt.savefig('experiments/comparison.png')
"""
    
    def get_hyperparameter_tuning_code(self) -> str:
        """Generate hyperparameter tuning code"""
        return """
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from skopt import BayesSearchCV
import numpy as np

# Grid Search
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15, 20],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

grid_search = GridSearchCV(
    RandomForestClassifier(random_state=42),
    param_grid,
    cv=5,
    scoring='f1_weighted',
    n_jobs=-1,
    verbose=1
)

grid_search.fit(X_train, y_train)

print(f"Best parameters: {grid_search.best_params_}")
print(f"Best CV score: {grid_search.best_score_:.4f}")
print(f"Test score: {grid_search.score(X_test, y_test):.4f}")

# Results
results_df = pd.DataFrame(grid_search.cv_results_)
results_df.to_csv('tuning_results.csv')

# Random Search (faster)
param_dist = {
    'n_estimators': [50, 100, 200, 500],
    'max_depth': [5, 10, 15, 20, None],
    'min_samples_split': [2, 5, 10, 20],
    'min_samples_leaf': [1, 2, 4, 8]
}

random_search = RandomizedSearchCV(
    RandomForestClassifier(random_state=42),
    param_dist,
    n_iter=20,
    cv=5,
    scoring='f1_weighted',
    n_jobs=-1,
    verbose=1,
    random_state=42
)

random_search.fit(X_train, y_train)
print(f"Best params (Random): {random_search.best_params_}")

# Bayesian Optimization (most efficient)
bayes_search = BayesSearchCV(
    RandomForestClassifier(random_state=42),
    {
        'n_estimators': (50, 500),
        'max_depth': (5, 50),
        'min_samples_split': (2, 20),
        'min_samples_leaf': (1, 20)
    },
    n_iter=20,
    cv=5,
    scoring='f1_weighted',
    n_jobs=-1,
    random_state=42
)

bayes_search.fit(X_train, y_train)
print(f"Best params (Bayesian): {bayes_search.best_params_}")
"""
    
    def create_experiment(
        self,
        experiment_id: str,
        config: ExperimentConfig,
        metrics: ExperimentMetrics,
        notes: str = ""
    ) -> Experiment:
        """Create new experiment"""
        experiment = Experiment(
            experiment_id=experiment_id,
            config=config,
            metrics=metrics,
            status=ExperimentStatus.PENDING,
            created_at=datetime.now(),
            notes=notes
        )
        
        self.experiments[experiment_id] = experiment
        self.experiment_history.append(experiment_id)
        
        logger.info(f"Created experiment: {experiment_id}")
        
        return experiment
    
    def update_experiment_status(
        self,
        experiment_id: str,
        status: ExperimentStatus,
        completed_at: Optional[datetime] = None
    ) -> bool:
        """Update experiment status"""
        if experiment_id not in self.experiments:
            logger.error(f"Experiment not found: {experiment_id}")
            return False
        
        experiment = self.experiments[experiment_id]
        experiment.status = status
        
        if status == ExperimentStatus.COMPLETED and completed_at:
            experiment.completed_at = completed_at
        
        return True
    
    def record_artifact(
        self,
        experiment_id: str,
        artifact_name: str,
        artifact_path: str
    ) -> bool:
        """Record experiment artifact (model, plot, etc)"""
        if experiment_id not in self.experiments:
            logger.error(f"Experiment not found: {experiment_id}")
            return False
        
        experiment = self.experiments[experiment_id]
        experiment.artifacts[artifact_name] = artifact_path
        
        return True
    
    def tag_experiment(
        self,
        experiment_id: str,
        tags: List[str]
    ) -> bool:
        """Add tags to experiment"""
        if experiment_id not in self.experiments:
            logger.error(f"Experiment not found: {experiment_id}")
            return False
        
        experiment = self.experiments[experiment_id]
        experiment.tags.extend(tags)
        
        return True
    
    def get_best_experiment(self, metric_name: str) -> Optional[str]:
        """Get best experiment by metric"""
        return self.best_experiments.get(metric_name)
    
    def compare_experiments(self, experiment_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple experiments"""
        comparisons = []
        
        for exp_id in experiment_ids:
            if exp_id in self.experiments:
                exp = self.experiments[exp_id]
                comparisons.append({
                    'id': exp_id,
                    'model': exp.config.model_name,
                    'primary_metric': exp.metrics.primary_metric_value,
                    'cv_mean': exp.metrics.cv_mean,
                    'training_time': exp.metrics.training_time
                })
        
        return {'comparisons': comparisons}
    
    def get_experiment_by_tag(self, tag: str) -> List[Experiment]:
        """Get experiments by tag"""
        return [
            exp for exp in self.experiments.values()
            if tag in exp.tags
        ]
    
    def export_experiments(self, output_path: str) -> bool:
        """Export all experiments to JSON"""
        try:
            data = {
                'experiments': [
                    exp.to_dict() for exp in self.experiments.values()
                ],
                'total': len(self.experiments),
                'exported_at': datetime.now().isoformat()
            }
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Exported {len(self.experiments)} experiments to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export experiments: {str(e)}")
            return False


# Singleton factory
_tracker_instance: Optional[ExperimentTracker] = None


def get_experiment_tracker() -> ExperimentTracker:
    """Get ExperimentTracker singleton"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = ExperimentTracker()
        logger.info("ExperimentTracker initialized")
    return _tracker_instance
