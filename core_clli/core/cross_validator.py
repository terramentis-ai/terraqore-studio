"""
Cross-Validation Framework - Phase 5.3 Week 2

Advanced cross-validation strategies and time series specific validation
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Dict, Any, Optional, Generator
import logging

logger = logging.getLogger(__name__)


class CVStrategy(Enum):
    """Cross-validation strategies"""
    KFOLD = "kfold"
    STRATIFIED_KFOLD = "stratified_kfold"
    TIME_SERIES_SPLIT = "time_series_split"
    SHUFFLE_SPLIT = "shuffle_split"
    GROUP_KFOLD = "group_kfold"
    LEAVE_ONE_OUT = "leave_one_out"


@dataclass
class CVFold:
    """Single cross-validation fold"""
    fold_number: int
    train_indices: List[int]
    test_indices: List[int]
    train_size: int
    test_size: int
    
    def get_summary(self) -> Dict[str, Any]:
        """Get fold summary"""
        return {
            'fold': self.fold_number,
            'train_size': self.train_size,
            'test_size': self.test_size,
            'split_ratio': self.test_size / (self.train_size + self.test_size)
        }


@dataclass
class CVResults:
    """Cross-validation results"""
    strategy: str
    n_splits: int
    folds: List[CVFold]
    metric_name: str
    scores: List[float]
    mean_score: float
    std_score: float
    min_score: float
    max_score: float
    
    def get_summary(self) -> Dict[str, Any]:
        """Get results summary"""
        return {
            'strategy': self.strategy,
            'n_splits': self.n_splits,
            'metric': self.metric_name,
            'mean': self.mean_score,
            'std': self.std_score,
            'min': self.min_score,
            'max': self.max_score
        }


class CrossValidator:
    """Advanced cross-validation framework"""
    
    def __init__(self):
        """Initialize cross-validator"""
        self.cv_results: Dict[str, CVResults] = {}
        self.fold_history: List[CVFold] = []
    
    def get_kfold_code(self, n_splits: int = 5) -> str:
        """Generate K-Fold cross-validation code"""
        return f"""
from sklearn.model_selection import KFold, cross_validate
import numpy as np

# K-Fold Cross-Validation (n_splits={n_splits})
kf = KFold(n_splits={n_splits}, shuffle=True, random_state=42)

# For classification/regression with different metrics
scoring = {{
    'accuracy': 'accuracy',  # for classification
    'f1': 'f1_weighted',     # for multi-class
    'precision': 'precision_weighted',
    'recall': 'recall_weighted'
}}

# Or for regression
scoring_reg = {{
    'r2': 'r2',
    'mae': 'neg_mean_absolute_error',
    'mse': 'neg_mean_squared_error',
    'rmse': 'neg_root_mean_squared_error'
}}

# Run cross-validation
cv_results = cross_validate(model, X, y, cv=kf, scoring=scoring, return_train_score=True)

# Extract results
train_scores = cv_results['train_accuracy']
test_scores = cv_results['test_accuracy']

print(f"Train scores: {{train_scores}}")
print(f"Test scores: {{test_scores}}")
print(f"Mean CV score: {{test_scores.mean():.4f}} (+/- {{test_scores.std():.4f}})")

# Manual fold iteration
fold_results = []
for fold, (train_idx, test_idx) in enumerate(kf.split(X), 1):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    fold_results.append({{'fold': fold, 'score': score}})
    print(f"Fold {{fold}}: {{score:.4f}}")
"""
    
    def get_stratified_kfold_code(self, n_splits: int = 5) -> str:
        """Generate Stratified K-Fold code"""
        return f"""
from sklearn.model_selection import StratifiedKFold, cross_validate
import numpy as np

# Stratified K-Fold (preserves class distribution)
skf = StratifiedKFold(n_splits={n_splits}, shuffle=True, random_state=42)

# For imbalanced classification
cv_results = cross_validate(model, X, y, cv=skf, scoring='f1_weighted', return_train_score=True)

test_scores = cv_results['test_score']
print(f"Stratified CV scores: {{test_scores}}")
print(f"Mean score: {{test_scores.mean():.4f}} (+/- {{test_scores.std():.4f}})")

# Fold-by-fold with stratification verification
for fold, (train_idx, test_idx) in enumerate(skf.split(X, y), 1):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    # Check class balance
    train_dist = np.bincount(y_train) / len(y_train)
    test_dist = np.bincount(y_test) / len(y_test)
    
    print(f"Fold {{fold}}:")
    print(f"  Train class distribution: {{train_dist}}")
    print(f"  Test class distribution: {{test_dist}}")
    
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    print(f"  Score: {{score:.4f}}")
"""
    
    def get_timeseries_cv_code(self) -> str:
        """Generate time series cross-validation code"""
        return """
from sklearn.model_selection import TimeSeriesSplit
import numpy as np

# Time Series Cross-Validation (expanding window)
tscv = TimeSeriesSplit(n_splits=5)

# Visualization of splits
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
    ax.scatter(range(len(train_idx)), [fold] * len(train_idx), c='blue', marker='_', s=100)
    ax.scatter(range(len(train_idx), len(train_idx) + len(test_idx)), 
               [fold] * len(test_idx), c='red', marker='_', s=100)

ax.set_xlabel('Sample Index')
ax.set_ylabel('CV Fold')
ax.set_title('Time Series Cross-Validation')
plt.savefig('models/timeseries_cv.png')

# Train and evaluate
fold_results = []
for fold, (train_idx, test_idx) in enumerate(tscv.split(X), 1):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    print(f"Fold {fold}:")
    print(f"  Train: {train_idx.min()}-{train_idx.max()}, size: {len(train_idx)}")
    print(f"  Test:  {test_idx.min()}-{test_idx.max()}, size: {len(test_idx)}")
    
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    fold_results.append(score)
    print(f"  Score: {score:.4f}")

print(f"\\nMean score: {np.mean(fold_results):.4f}")
"""
    
    def get_nested_cv_code(self) -> str:
        """Generate nested cross-validation code"""
        return """
from sklearn.model_selection import KFold, GridSearchCV, cross_validate

# Nested CV: Outer for evaluation, Inner for hyperparameter tuning

# Outer CV
outer_cv = KFold(n_splits=5, shuffle=True, random_state=42)
nested_scores = []

# Hyperparameter grid for inner CV
param_grid = {
    'C': [0.1, 1, 10, 100],
    'kernel': ['linear', 'rbf'],
    'gamma': ['scale', 'auto']
}

for fold, (train_idx, test_idx) in enumerate(outer_cv.split(X), 1):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    # Inner CV for hyperparameter tuning
    inner_cv = KFold(n_splits=3, shuffle=True, random_state=42)
    
    from sklearn.svm import SVC
    grid_search = GridSearchCV(
        SVC(),
        param_grid,
        cv=inner_cv,
        scoring='accuracy'
    )
    
    # Fit with inner CV hyperparameter search
    grid_search.fit(X_train, y_train)
    
    # Evaluate on outer CV test set
    score = grid_search.score(X_test, y_test)
    nested_scores.append(score)
    
    print(f"Fold {fold}:")
    print(f"  Best params: {grid_search.best_params_}")
    print(f"  Best CV score: {grid_search.best_score_:.4f}")
    print(f"  Test score: {score:.4f}")

print(f"\\nNested CV score: {np.mean(nested_scores):.4f} (+/- {np.std(nested_scores):.4f})")
"""
    
    def get_group_kfold_code(self) -> str:
        """Generate Group K-Fold code"""
        return """
from sklearn.model_selection import GroupKFold
import numpy as np

# Group K-Fold (for grouped data - e.g., patient data with multiple samples)
gkf = GroupKFold(n_splits=5)

# groups: array indicating group membership
# Example: groups = [0, 0, 0, 1, 1, 1, 2, 2, 2, ...]

fold_results = []
for fold, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups=groups), 1):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    print(f"Fold {fold}:")
    print(f"  Train groups: {np.unique(groups[train_idx])}")
    print(f"  Test groups: {np.unique(groups[test_idx])}")
    print(f"  Train size: {len(train_idx)}, Test size: {len(test_idx)}")
    
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    fold_results.append(score)
    print(f"  Score: {score:.4f}")

print(f"\\nMean score: {np.mean(fold_results):.4f}")
"""
    
    def get_custom_cv_code(self) -> str:
        """Generate custom cross-validation code"""
        return """
from sklearn.model_selection import BaseCrossValidator
import numpy as np

class CustomCV(BaseCrossValidator):
    \"\"\"Custom cross-validator with domain-specific logic\"\"\"
    
    def __init__(self, n_splits=5, test_size=0.2):
        self.n_splits = n_splits
        self.test_size = test_size
    
    def split(self, X, y=None, groups=None):
        \"\"\"Generate train/test indices\"\"\"
        n_samples = X.shape[0]
        indices = np.arange(n_samples)
        
        for fold in range(self.n_splits):
            # Custom logic: e.g., date-based, stratified by group
            test_start = int(fold * n_samples * self.test_size)
            test_end = int((fold + 1) * n_samples * self.test_size)
            
            test_idx = np.arange(test_start, test_end)
            train_idx = np.setdiff1d(indices, test_idx)
            
            yield train_idx, test_idx
    
    def get_n_splits(self, X=None, y=None, groups=None):
        return self.n_splits


# Usage
custom_cv = CustomCV(n_splits=5, test_size=0.2)

from sklearn.model_selection import cross_validate
cv_results = cross_validate(model, X, y, cv=custom_cv, scoring='accuracy')
print(f"Custom CV score: {cv_results['test_score'].mean():.4f}")
"""
    
    def create_folds(
        self,
        n_samples: int,
        n_splits: int,
        strategy: CVStrategy
    ) -> List[CVFold]:
        """Create CV folds"""
        folds = []
        
        if strategy == CVStrategy.KFOLD:
            fold_size = n_samples // n_splits
            for i in range(n_splits):
                test_start = i * fold_size
                test_end = test_start + fold_size if i < n_splits - 1 else n_samples
                
                test_indices = list(range(test_start, test_end))
                train_indices = list(range(0, test_start)) + list(range(test_end, n_samples))
                
                fold = CVFold(
                    fold_number=i + 1,
                    train_indices=train_indices,
                    test_indices=test_indices,
                    train_size=len(train_indices),
                    test_size=len(test_indices)
                )
                folds.append(fold)
        
        elif strategy == CVStrategy.TIME_SERIES_SPLIT:
            for i in range(1, n_splits + 1):
                train_end = int(n_samples * (i / (n_splits + 1)))
                test_end = int(n_samples * ((i + 1) / (n_splits + 1)))
                
                train_indices = list(range(0, train_end))
                test_indices = list(range(train_end, test_end))
                
                fold = CVFold(
                    fold_number=i,
                    train_indices=train_indices,
                    test_indices=test_indices,
                    train_size=len(train_indices),
                    test_size=len(test_indices)
                )
                folds.append(fold)
        
        self.fold_history.extend(folds)
        return folds
    
    def record_cv_results(
        self,
        strategy: CVStrategy,
        n_splits: int,
        folds: List[CVFold],
        metric_name: str,
        scores: List[float]
    ) -> CVResults:
        """Record CV results"""
        import statistics
        
        results = CVResults(
            strategy=strategy.value,
            n_splits=n_splits,
            folds=folds,
            metric_name=metric_name,
            scores=scores,
            mean_score=statistics.mean(scores),
            std_score=statistics.stdev(scores) if len(scores) > 1 else 0.0,
            min_score=min(scores),
            max_score=max(scores)
        )
        
        key = f"{strategy.value}_{metric_name}"
        self.cv_results[key] = results
        
        return results
    
    def get_cv_results(self, strategy: str, metric: str) -> Optional[CVResults]:
        """Get CV results"""
        key = f"{strategy}_{metric}"
        return self.cv_results.get(key)


# Singleton factory
_validator_instance: Optional[CrossValidator] = None


def get_cross_validator() -> CrossValidator:
    """Get CrossValidator singleton"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = CrossValidator()
        logger.info("CrossValidator initialized")
    return _validator_instance
