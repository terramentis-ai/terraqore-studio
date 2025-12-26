"""
Visualization & Dashboard - Phase 5.3 Week 2

Visualizations for metrics, training progress, and model comparison
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PlotType(Enum):
    """Plot types"""
    CONFUSION_MATRIX = "confusion_matrix"
    ROC_CURVE = "roc_curve"
    FEATURE_IMPORTANCE = "feature_importance"
    LEARNING_CURVE = "learning_curve"
    VALIDATION_CURVE = "validation_curve"
    MODEL_COMPARISON = "model_comparison"
    TRAINING_HISTORY = "training_history"


@dataclass
class PlotConfig:
    """Plot configuration"""
    title: str
    xlabel: str
    ylabel: str
    figsize: tuple = (10, 6)
    style: str = "seaborn"
    save_path: str = "plots/"


class VisualizationEngine:
    """Generate visualizations for ML workflows"""
    
    def __init__(self):
        """Initialize visualization engine"""
        self.plots: Dict[str, str] = {}
    
    def get_confusion_matrix_code(self) -> str:
        """Generate confusion matrix visualization code"""
        return """
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
import numpy as np

# Compute confusion matrix
cm = confusion_matrix(y_test, y_pred)

# Display using sklearn
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=classes)
fig, ax = plt.subplots(figsize=(10, 8))
disp.plot(ax=ax, cmap='Blues', values_format='d')
plt.title('Confusion Matrix')
plt.tight_layout()
plt.savefig('plots/confusion_matrix.png', dpi=300)

# Heatmap version
import seaborn as sns
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=classes, yticklabels=classes)
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.title('Confusion Matrix')
plt.tight_layout()
plt.savefig('plots/confusion_matrix_heatmap.png', dpi=300)

# Calculate and plot metrics from CM
tn, fp, fn, tp = cm.ravel()
accuracy = (tp + tn) / (tp + tn + fp + fn)
precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

print(f"Accuracy: {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1 Score: {f1:.4f}")
"""
    
    def get_roc_curve_code(self) -> str:
        """Generate ROC curve visualization code"""
        return """
from sklearn.metrics import roc_curve, auc, roc_auc_score
from sklearn.preprocessing import label_binarize
import matplotlib.pyplot as plt
import numpy as np

# Binary classification
if n_classes == 2:
    fpr, tpr, _ = roc_curve(y_test, y_pred_proba[:, 1])
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.3f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random Classifier')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve')
    plt.legend(loc='lower right')
    plt.savefig('plots/roc_curve.png', dpi=300)

# Multi-class classification
else:
    y_test_bin = label_binarize(y_test, classes=range(n_classes))
    fpr, tpr, roc_auc = {}, {}, {}
    
    for i in range(n_classes):
        fpr[i], tpr[i], _ = roc_curve(y_test_bin[:, i], y_pred_proba[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])
    
    # Macro average
    fpr['macro'], tpr['macro'] = np.mean(list(fpr.values())[:-1]), np.mean(list(tpr.values())[:-1])
    roc_auc['macro'] = auc(fpr['macro'], tpr['macro'])
    
    plt.figure(figsize=(10, 8))
    for i in range(n_classes):
        plt.plot(fpr[i], tpr[i], label=f'Class {i} (AUC = {roc_auc[i]:.3f})')
    plt.plot(fpr['macro'], tpr['macro'], label=f'Macro (AUC = {roc_auc["macro"]:.3f})', linewidth=2)
    plt.plot([0, 1], [0, 1], 'k--', label='Random')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curves (Multi-class)')
    plt.legend()
    plt.savefig('plots/roc_curves_multiclass.png', dpi=300)
"""
    
    def get_feature_importance_code(self) -> str:
        """Generate feature importance visualization code"""
        return """
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Extract feature importance
feature_importance = model.feature_importances_
feature_names = feature_names or [f'Feature {i}' for i in range(len(feature_importance))]

# Create dataframe
importance_df = pd.DataFrame({
    'feature': feature_names,
    'importance': feature_importance
}).sort_values('importance', ascending=True)

# Horizontal bar plot
plt.figure(figsize=(10, 8))
plt.barh(importance_df['feature'][-20:], importance_df['importance'][-20:])
plt.xlabel('Importance')
plt.ylabel('Feature')
plt.title('Top 20 Feature Importances')
plt.tight_layout()
plt.savefig('plots/feature_importance.png', dpi=300)

# Cumulative importance
cumsum = np.cumsum(sorted(feature_importance, reverse=True))
cumsum = cumsum / cumsum[-1]

plt.figure(figsize=(10, 6))
plt.plot(cumsum, 'b-')
plt.axhline(y=0.95, color='r', linestyle='--', label='95% Variance')
plt.xlabel('Number of Features')
plt.ylabel('Cumulative Importance')
plt.title('Cumulative Feature Importance')
plt.legend()
plt.grid()
plt.savefig('plots/cumulative_importance.png', dpi=300)

# SHAP values (advanced)
try:
    import shap
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    
    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_values, X_test, plot_type='bar', show=False)
    plt.savefig('plots/shap_summary.png', dpi=300)
    
    # Force plot for single prediction
    plt.figure(figsize=(12, 4))
    shap.force_plot(explainer.expected_value, shap_values[0], X_test.iloc[0], show=False)
    plt.savefig('plots/shap_force.png', dpi=300)
except:
    print("SHAP not available")
"""
    
    def get_learning_curve_code(self) -> str:
        """Generate learning curve visualization code"""
        return """
from sklearn.model_selection import learning_curve
import numpy as np
import matplotlib.pyplot as plt

# Generate learning curves
train_sizes, train_scores, val_scores = learning_curve(
    model, X_train, y_train,
    train_sizes=np.linspace(0.1, 1.0, 10),
    cv=5,
    scoring='accuracy',
    n_jobs=-1,
    verbose=1
)

train_mean = np.mean(train_scores, axis=1)
train_std = np.std(train_scores, axis=1)
val_mean = np.mean(val_scores, axis=1)
val_std = np.std(val_scores, axis=1)

# Plot learning curves
plt.figure(figsize=(10, 6))
plt.plot(train_sizes, train_mean, 'o-', label='Training score', color='blue')
plt.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.2, color='blue')
plt.plot(train_sizes, val_mean, 'o-', label='Validation score', color='red')
plt.fill_between(train_sizes, val_mean - val_std, val_mean + val_std, alpha=0.2, color='red')
plt.xlabel('Training Set Size')
plt.ylabel('Score')
plt.title('Learning Curve')
plt.legend(loc='best')
plt.grid()
plt.savefig('plots/learning_curve.png', dpi=300)

# Diagnosis
print("Learning Curve Analysis:")
if train_mean[-1] - val_mean[-1] > 0.1:
    print("⚠️  High variance: Model overfits. Collect more data or use regularization.")
elif train_mean[-1] < 0.8:
    print("⚠️  High bias: Model underfits. Increase model complexity.")
else:
    print("✓ Good generalization")
"""
    
    def get_validation_curve_code(self) -> str:
        """Generate validation curve visualization code"""
        return """
from sklearn.model_selection import validation_curve
import numpy as np
import matplotlib.pyplot as plt

# Validation curve - tune a hyperparameter
param_range = [1, 3, 5, 7, 10, 15, 20]
train_scores, val_scores = validation_curve(
    estimator=model,
    X=X_train,
    y=y_train,
    param_name='max_depth',
    param_range=param_range,
    cv=5,
    scoring='accuracy',
    n_jobs=-1,
    verbose=1
)

train_mean = np.mean(train_scores, axis=1)
train_std = np.std(train_scores, axis=1)
val_mean = np.mean(val_scores, axis=1)
val_std = np.std(val_scores, axis=1)

# Plot validation curve
plt.figure(figsize=(10, 6))
plt.plot(param_range, train_mean, 'o-', label='Training score', color='blue')
plt.fill_between(param_range, train_mean - train_std, train_mean + train_std, alpha=0.2, color='blue')
plt.plot(param_range, val_mean, 'o-', label='Validation score', color='red')
plt.fill_between(param_range, val_mean - val_std, val_mean + val_std, alpha=0.2, color='red')
plt.xlabel('max_depth')
plt.ylabel('Score')
plt.title('Validation Curve')
plt.legend(loc='best')
plt.grid()
plt.savefig('plots/validation_curve.png', dpi=300)

# Find optimal parameter
optimal_idx = np.argmax(val_mean)
optimal_param = param_range[optimal_idx]
print(f"Optimal max_depth: {optimal_param}")
"""
    
    def get_training_history_code(self) -> str:
        """Generate training history visualization code"""
        return """
import matplotlib.pyplot as plt
import numpy as np

# Training history from neural networks
history = model.history.history

# Plot loss
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Loss curves
axes[0].plot(history['loss'], label='Training Loss')
axes[0].plot(history['val_loss'], label='Validation Loss')
axes[0].set_xlabel('Epoch')
axes[0].set_ylabel('Loss')
axes[0].set_title('Model Loss')
axes[0].legend()
axes[0].grid()

# Accuracy curves
axes[1].plot(history['accuracy'], label='Training Accuracy')
axes[1].plot(history['val_accuracy'], label='Validation Accuracy')
axes[1].set_xlabel('Epoch')
axes[1].set_ylabel('Accuracy')
axes[1].set_title('Model Accuracy')
axes[1].legend()
axes[1].grid()

plt.tight_layout()
plt.savefig('plots/training_history.png', dpi=300)

# Advanced: Find optimal epoch (early stopping point)
val_loss = np.array(history['val_loss'])
optimal_epoch = np.argmin(val_loss)
print(f"Optimal epoch: {optimal_epoch + 1}")
print(f"Best validation loss: {val_loss[optimal_epoch]:.4f}")

# Plot with early stopping marker
plt.figure(figsize=(10, 6))
plt.plot(history['train_loss'], label='Training')
plt.plot(history['val_loss'], label='Validation')
plt.axvline(x=optimal_epoch, color='r', linestyle='--', label=f'Early Stop (epoch {optimal_epoch+1})')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Early Stopping Point')
plt.legend()
plt.grid()
plt.savefig('plots/early_stopping.png', dpi=300)
"""
    
    def get_model_comparison_code(self) -> str:
        """Generate model comparison visualization code"""
        return """
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Model comparison data
comparison_data = {
    'Model': ['RandomForest', 'XGBoost', 'LogisticRegression', 'SVM'],
    'Accuracy': [0.92, 0.94, 0.88, 0.89],
    'F1-Score': [0.91, 0.93, 0.87, 0.88],
    'Training Time': [2.5, 3.2, 0.5, 4.1]  # seconds
}

df = pd.DataFrame(comparison_data)

# Bar plot - metrics
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Metrics comparison
x = np.arange(len(df['Model']))
width = 0.35
axes[0].bar(x - width/2, df['Accuracy'], width, label='Accuracy')
axes[0].bar(x + width/2, df['F1-Score'], width, label='F1-Score')
axes[0].set_xlabel('Model')
axes[0].set_ylabel('Score')
axes[0].set_title('Model Performance Comparison')
axes[0].set_xticks(x)
axes[0].set_xticklabels(df['Model'])
axes[0].legend()
axes[0].set_ylim([0.8, 1.0])

# Training time
axes[1].bar(df['Model'], df['Training Time'], color='steelblue')
axes[1].set_ylabel('Time (seconds)')
axes[1].set_title('Training Time Comparison')
axes[1].set_ylim([0, max(df['Training Time']) * 1.2])

plt.tight_layout()
plt.savefig('plots/model_comparison.png', dpi=300)

# Radar plot (multi-metric comparison)
from math import pi

categories = ['Accuracy', 'F1-Score', 'Speed']
N = len(categories)

angles = [n / float(N) * 2 * pi for n in range(N)]
angles += angles[:1]

fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='polar')

for idx, model_name in enumerate(df['Model']):
    values = [df.loc[idx, 'Accuracy'], df.loc[idx, 'F1-Score'], 
              1 / df.loc[idx, 'Training Time']]  # Inverse for speed
    values += values[:1]
    ax.plot(angles, values, 'o-', linewidth=2, label=model_name)
    ax.fill(angles, values, alpha=0.15)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories)
ax.set_ylim(0, 1)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
ax.set_title('Model Comparison Radar')
ax.grid(True)

plt.tight_layout()
plt.savefig('plots/model_comparison_radar.png', dpi=300)
"""
    
    def register_plot(self, plot_name: str, plot_path: str) -> None:
        """Register generated plot"""
        self.plots[plot_name] = plot_path
        logger.info(f"Registered plot: {plot_name} -> {plot_path}")
    
    def get_all_plots(self) -> Dict[str, str]:
        """Get all registered plots"""
        return self.plots.copy()


# Singleton factory
_visualization_instance: Optional[VisualizationEngine] = None


def get_visualization_engine() -> VisualizationEngine:
    """Get VisualizationEngine singleton"""
    global _visualization_instance
    if _visualization_instance is None:
        _visualization_instance = VisualizationEngine()
        logger.info("VisualizationEngine initialized")
    return _visualization_instance
