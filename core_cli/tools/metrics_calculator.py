"""
Model Evaluation & Metrics - Phase 5.3 Week 2

Advanced evaluation metrics and performance analysis
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MetricCategory(Enum):
    """Metric categories"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    NLP = "nlp"
    COMPUTER_VISION = "computer_vision"
    TIME_SERIES = "time_series"
    CLUSTERING = "clustering"


@dataclass
class ConfusionMatrix:
    """Confusion matrix data"""
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    
    @property
    def accuracy(self) -> float:
        """Calculate accuracy"""
        total = self.true_positives + self.true_negatives + self.false_positives + self.false_negatives
        return (self.true_positives + self.true_negatives) / total if total > 0 else 0.0
    
    @property
    def precision(self) -> float:
        """Calculate precision"""
        denominator = self.true_positives + self.false_positives
        return self.true_positives / denominator if denominator > 0 else 0.0
    
    @property
    def recall(self) -> float:
        """Calculate recall/sensitivity"""
        denominator = self.true_positives + self.false_negatives
        return self.true_positives / denominator if denominator > 0 else 0.0
    
    @property
    def f1_score(self) -> float:
        """Calculate F1 score"""
        p = self.precision
        r = self.recall
        denominator = p + r
        return 2 * (p * r) / denominator if denominator > 0 else 0.0
    
    @property
    def specificity(self) -> float:
        """Calculate specificity"""
        denominator = self.true_negatives + self.false_positives
        return self.true_negatives / denominator if denominator > 0 else 0.0


@dataclass
class RegressionMetrics:
    """Regression metrics"""
    mae: float  # Mean Absolute Error
    mse: float  # Mean Squared Error
    rmse: float  # Root Mean Squared Error
    mape: float  # Mean Absolute Percentage Error
    r2_score: float  # R² Score
    adjusted_r2: float
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            'mae': self.mae,
            'mse': self.mse,
            'rmse': self.rmse,
            'mape': self.mape,
            'r2_score': self.r2_score,
            'adjusted_r2': self.adjusted_r2
        }


@dataclass
class ClassificationMetrics:
    """Classification metrics"""
    accuracy: float
    precision: float
    recall: float
    f1: float
    auc_roc: Optional[float] = None
    specificity: float = 0.0
    sensitivity: float = 0.0  # Same as recall
    balanced_accuracy: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1': self.f1,
            'auc_roc': self.auc_roc,
            'specificity': self.specificity,
            'balanced_accuracy': self.balanced_accuracy
        }


@dataclass
class ClusteringMetrics:
    """Clustering metrics"""
    silhouette_score: float  # [-1, 1] - higher is better
    davies_bouldin_index: float  # Lower is better
    calinski_harabasz_index: float  # Higher is better
    inertia: float  # Within-cluster sum of squares
    num_clusters: int
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            'silhouette_score': self.silhouette_score,
            'davies_bouldin_index': self.davies_bouldin_index,
            'calinski_harabasz_index': self.calinski_harabasz_index,
            'inertia': self.inertia,
            'num_clusters': self.num_clusters
        }


@dataclass
class ModelComparison:
    """Model comparison results"""
    model_names: List[str]
    metric_name: str
    scores: Dict[str, float]
    rankings: List[Tuple[str, float]]
    best_model: str
    worst_model: str
    mean_score: float
    std_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'models': self.model_names,
            'metric': self.metric_name,
            'scores': self.scores,
            'rankings': self.rankings,
            'best_model': self.best_model,
            'worst_model': self.worst_model,
            'mean_score': self.mean_score,
            'std_score': self.std_score
        }


class MetricCalculator:
    """Calculate and track evaluation metrics"""
    
    def __init__(self):
        """Initialize metric calculator"""
        self.metrics_history: Dict[str, List[Dict[str, Any]]] = {}
        self.model_comparisons: Dict[str, ModelComparison] = {}
    
    def get_classification_metrics_code(self) -> str:
        """Generate classification metrics code"""
        return """
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.metrics import confusion_matrix, classification_report, roc_curve, auc
import numpy as np

# Calculate metrics
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, average='weighted')
recall = recall_score(y_test, y_pred, average='weighted')
f1 = f1_score(y_test, y_pred, average='weighted')

# ROC-AUC (for binary classification)
if len(np.unique(y_test)) == 2:
    auc_score = roc_auc_score(y_test, y_pred_proba[:, 1])
else:
    auc_score = roc_auc_score(y_test, y_pred_proba, multi_class='ovr')

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
print("Confusion Matrix:\\n", cm)

# Classification report
print("\\nClassification Report:\\n", classification_report(y_test, y_pred))

# Plot ROC curve
fpr, tpr, _ = roc_curve(y_test, y_pred_proba[:, 1])
plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, label=f'ROC curve (AUC = {auc_score:.3f})')
plt.plot([0, 1], [0, 1], 'k--')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve')
plt.legend()
plt.savefig('models/roc_curve.png')

metrics = {
    'accuracy': accuracy,
    'precision': precision,
    'recall': recall,
    'f1': f1,
    'auc': auc_score
}
"""
    
    def get_regression_metrics_code(self) -> str:
        """Generate regression metrics code"""
        return """
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np

# Calculate metrics
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)

# MAPE
mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100

# Adjusted R²
n = len(y_test)
p = X_test.shape[1]
adj_r2 = 1 - (1 - r2) * (n - 1) / (n - p - 1)

# Plot predictions
plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred, alpha=0.6)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
plt.xlabel('Actual')
plt.ylabel('Predicted')
plt.title('Prediction vs Actual')
plt.savefig('models/predictions.png')

# Residuals plot
residuals = y_test - y_pred
plt.figure(figsize=(10, 6))
plt.scatter(y_pred, residuals, alpha=0.6)
plt.axhline(y=0, color='r', linestyle='--')
plt.xlabel('Predicted')
plt.ylabel('Residuals')
plt.title('Residuals Plot')
plt.savefig('models/residuals.png')

metrics = {
    'mae': mae,
    'mse': mse,
    'rmse': rmse,
    'mape': mape,
    'r2': r2,
    'adj_r2': adj_r2
}
"""
    
    def get_nlp_metrics_code(self) -> str:
        """Generate NLP metrics code"""
        return """
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from seqeval.metrics import precision_score as seqeval_precision
from seqeval.metrics import recall_score as seqeval_recall
from seqeval.metrics import f1_score as seqeval_f1

# For sequence labeling (NER, POS tagging)
# Input: y_true, y_pred as list of lists (sequences)
precision = seqeval_precision(y_true, y_pred)
recall = seqeval_recall(y_true, y_pred)
f1 = seqeval_f1(y_true, y_pred)

# For text classification
# Flatten sequences
y_true_flat = [item for seq in y_true for item in seq]
y_pred_flat = [item for seq in y_pred for item in seq]

accuracy = accuracy_score(y_true_flat, y_pred_flat)

metrics = {
    'accuracy': accuracy,
    'precision': precision,
    'recall': recall,
    'f1': f1
}
"""
    
    def get_cv_metrics_code(self) -> str:
        """Generate Computer Vision metrics code"""
        return """
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import confusion_matrix, jaccard_score
import numpy as np

# Image classification
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, average='weighted')
recall = recall_score(y_test, y_pred, average='weighted')
f1 = f1_score(y_test, y_pred, average='weighted')

# Object detection (IoU)
# Intersection over Union
def calculate_iou(box1, box2):
    inter_area = max(0, min(box1[2], box2[2]) - max(box1[0], box2[0])) * \
                 max(0, min(box1[3], box2[3]) - max(box1[1], box2[1]))
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union_area = box1_area + box2_area - inter_area
    iou = inter_area / union_area if union_area > 0 else 0
    return iou

# Semantic segmentation (mIoU)
miou = jaccard_score(y_test.ravel(), y_pred.ravel(), average='weighted')

metrics = {
    'accuracy': accuracy,
    'precision': precision,
    'recall': recall,
    'f1': f1,
    'miou': miou
}
"""
    
    def get_clustering_metrics_code(self) -> str:
        """Generate clustering metrics code"""
        return """
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
import numpy as np

# Silhouette score [-1, 1] - higher is better
silhouette = silhouette_score(X, labels)

# Davies-Bouldin index - lower is better
davies_bouldin = davies_bouldin_score(X, labels)

# Calinski-Harabasz index - higher is better
calinski_harabasz = calinski_harabasz_score(X, labels)

# Inertia (within-cluster sum of squares)
from sklearn.cluster import KMeans
kmeans = KMeans(n_clusters=k)
kmeans.fit(X)
inertia = kmeans.inertia_

# Elbow method plot
inertias = []
for k in range(1, 11):
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(X)
    inertias.append(kmeans.inertia_)

import matplotlib.pyplot as plt
plt.figure(figsize=(8, 6))
plt.plot(range(1, 11), inertias, 'bo-')
plt.xlabel('Number of Clusters')
plt.ylabel('Inertia')
plt.title('Elbow Method')
plt.savefig('models/elbow_curve.png')

metrics = {
    'silhouette': silhouette,
    'davies_bouldin': davies_bouldin,
    'calinski_harabasz': calinski_harabasz,
    'inertia': inertia
}
"""
    
    def get_feature_importance_code(self) -> str:
        """Generate feature importance analysis code"""
        return """
import pandas as pd
import matplotlib.pyplot as plt

# For tree-based models
feature_importance = model.feature_importances_
feature_names = X_train.columns
importance_df = pd.DataFrame({
    'feature': feature_names,
    'importance': feature_importance
}).sort_values('importance', ascending=False)

# Plot feature importance
plt.figure(figsize=(10, 6))
plt.barh(importance_df['feature'][:15], importance_df['importance'][:15])
plt.xlabel('Importance')
plt.title('Feature Importance')
plt.tight_layout()
plt.savefig('models/feature_importance.png')

# SHAP analysis (advanced)
import shap
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)
shap.summary_plot(shap_values, X_test, plot_type='bar', show=False)
plt.savefig('models/shap_summary.png')

# Permutation importance
from sklearn.inspection import permutation_importance
result = permutation_importance(model, X_test, y_test, n_repeats=10)
perm_importance_df = pd.DataFrame({
    'feature': feature_names,
    'importance': result.importances_mean
}).sort_values('importance', ascending=False)
"""
    
    def record_metrics(
        self,
        model_name: str,
        metric_category: MetricCategory,
        metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Record metrics for model"""
        if model_name not in self.metrics_history:
            self.metrics_history[model_name] = []
        
        record = {
            'timestamp': datetime.now(),
            'category': metric_category.value,
            'metrics': metrics
        }
        
        self.metrics_history[model_name].append(record)
        
        return record
    
    def compare_models(
        self,
        model_names: List[str],
        metric_scores: Dict[str, float],
        metric_name: str
    ) -> ModelComparison:
        """Compare models on a metric"""
        rankings = sorted(metric_scores.items(), key=lambda x: x[1], reverse=True)
        scores = [v for k, v in rankings]
        
        import statistics
        mean_score = statistics.mean(scores)
        std_score = statistics.stdev(scores) if len(scores) > 1 else 0.0
        
        comparison = ModelComparison(
            model_names=model_names,
            metric_name=metric_name,
            scores=metric_scores,
            rankings=rankings,
            best_model=rankings[0][0],
            worst_model=rankings[-1][0],
            mean_score=mean_score,
            std_score=std_score
        )
        
        self.model_comparisons[metric_name] = comparison
        
        return comparison
    
    def get_metrics_history(self, model_name: str) -> List[Dict[str, Any]]:
        """Get metrics history for model"""
        return self.metrics_history.get(model_name, [])
    
    def get_comparison(self, metric_name: str) -> Optional[ModelComparison]:
        """Get model comparison"""
        return self.model_comparisons.get(metric_name)


# Singleton factory
_calculator_instance: Optional[MetricCalculator] = None


def get_metric_calculator() -> MetricCalculator:
    """Get MetricCalculator singleton"""
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = MetricCalculator()
        logger.info("MetricCalculator initialized")
    return _calculator_instance
