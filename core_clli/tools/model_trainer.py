"""
Model training, validation, fine-tuning, and evaluation utilities
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ValidationStrategy(Enum):
    """Cross-validation strategies"""
    KFOLD = "kfold"
    STRATIFIED_KFOLD = "stratified_kfold"
    TIME_SERIES_SPLIT = "time_series_split"
    LEAVE_ONE_OUT = "leave_one_out"
    SHUFFLE_SPLIT = "shuffle_split"


class TrainingPhase(Enum):
    """Training phases"""
    DATA_PREPARATION = "data_preparation"
    MODEL_INITIALIZATION = "model_initialization"
    TRAINING = "training"
    VALIDATION = "validation"
    EVALUATION = "evaluation"
    HYPERPARAMETER_TUNING = "hyperparameter_tuning"


@dataclass
class TrainingMetrics:
    """Training metrics"""
    epoch: int
    loss: float
    train_metric: float
    val_metric: float
    learning_rate: float
    batch_size: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EvaluationResults:
    """Model evaluation results"""
    model_name: str
    primary_metric_value: float
    secondary_metrics: Dict[str, float]
    confusion_matrix: Optional[List[List[int]]] = None
    feature_importance: Optional[Dict[str, float]] = None
    cross_validation_scores: List[float] = field(default_factory=list)
    cross_validation_mean: float = 0.0
    cross_validation_std: float = 0.0
    training_time_seconds: float = 0.0
    inference_time_ms: float = 0.0
    model_size_mb: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class HyperparameterTuningConfig:
    """Hyperparameter tuning configuration"""
    strategy: str  # "grid_search", "random_search", "bayesian"
    param_grid: Dict[str, List[Any]]
    cv_folds: int = 5
    n_iter: int = 20  # For random/bayesian search
    scoring_metric: str = "accuracy"
    n_jobs: int = -1  # Parallel jobs


class ModelTrainer:
    """Model training and evaluation"""
    
    def __init__(self):
        """Initialize model trainer"""
        self.trained_models: Dict[str, Dict[str, Any]] = {}
        self.training_history: Dict[str, List[TrainingMetrics]] = {}
        self.evaluation_results: Dict[str, EvaluationResults] = {}
    
    def get_training_script(self, model_type: str, framework: str) -> str:
        """Generate training script for model"""
        
        scripts = {
            ("logistic_regression", "scikit_learn"): self._sklearn_classification_script("LogisticRegression"),
            ("random_forest", "scikit_learn"): self._sklearn_classification_script("RandomForestClassifier"),
            ("gradient_boosting", "scikit_learn"): self._sklearn_classification_script("GradientBoostingClassifier"),
            ("xgboost", "xgboost"): self._xgboost_script(),
            ("neural_network", "pytorch"): self._pytorch_nn_script(),
            ("lstm", "pytorch"): self._pytorch_lstm_script(),
            ("bert", "huggingface"): self._huggingface_bert_script(),
            ("resnet50", "pytorch"): self._pytorch_vision_script("resnet50"),
        }
        
        return scripts.get((model_type, framework), "")
    
    def _sklearn_classification_script(self, model_class: str) -> str:
        """Generate scikit-learn classification training script"""
        return f"""
from sklearn.ensemble import {model_class}
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import numpy as np

# Load data
X_train = pd.read_csv('data/processed/X_train.csv')
y_train = pd.read_csv('data/processed/y_train.csv').squeeze()
X_test = pd.read_csv('data/processed/X_test.csv')
y_test = pd.read_csv('data/processed/y_test.csv').squeeze()

# Initialize model
model = {model_class}(random_state=42, n_jobs=-1)

# Training
print("Training model...")
model.fit(X_train, y_train)

# Cross-validation
cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
print(f"CV Score: {{cv_scores.mean():.4f}} (+/- {{cv_scores.std():.4f}})")

# Evaluation
y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None

results = {{
    'accuracy': accuracy_score(y_test, y_pred),
    'precision': precision_score(y_test, y_pred, average='weighted'),
    'recall': recall_score(y_test, y_pred, average='weighted'),
    'f1': f1_score(y_test, y_pred, average='weighted'),
    'cv_mean': cv_scores.mean()
}}

if y_pred_proba is not None:
    results['auc'] = roc_auc_score(y_test, y_pred_proba)

print("Results:", results)

# Save model
import joblib
joblib.dump(model, 'models/{model_class.lower()}.pkl')
print("Model saved!")
"""
    
    def _xgboost_script(self) -> str:
        """Generate XGBoost training script"""
        return """
import xgboost as xgb
from sklearn.metrics import accuracy_score, roc_auc_score
import pandas as pd

# Load data
X_train = pd.read_csv('data/processed/X_train.csv')
y_train = pd.read_csv('data/processed/y_train.csv').squeeze()
X_val = X_train.sample(frac=0.2, random_state=42)
y_val = y_train.loc[X_val.index]
X_train = X_train.drop(X_val.index)
y_train = y_train.drop(y_val.index)

# Create datasets
dtrain = xgb.DMatrix(X_train, label=y_train)
dval = xgb.DMatrix(X_val, label=y_val)

# Parameters
params = {
    'objective': 'binary:logistic',
    'max_depth': 6,
    'learning_rate': 0.1,
    'eval_metric': 'auc'
}

# Training
evals = [(dtrain, 'train'), (dval, 'val')]
evals_result = {}
model = xgb.train(params, dtrain, num_boost_round=100, 
                   evals=evals, evals_result=evals_result, 
                   early_stopping_rounds=10, verbose_eval=10)

# Evaluation
X_test = pd.read_csv('data/processed/X_test.csv')
y_test = pd.read_csv('data/processed/y_test.csv').squeeze()
dtest = xgb.DMatrix(X_test, label=y_test)

y_pred = model.predict(dtest)
results = {
    'accuracy': accuracy_score(y_test, (y_pred > 0.5).astype(int)),
    'auc': roc_auc_score(y_test, y_pred)
}

print("Results:", results)

# Save model
model.save_model('models/xgboost_model.bin')
print("Model saved!")
"""
    
    def _pytorch_nn_script(self) -> str:
        """Generate PyTorch neural network training script"""
        return """
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import pandas as pd

# Load data
X_train = torch.FloatTensor(pd.read_csv('data/processed/X_train.csv').values)
y_train = torch.LongTensor(pd.read_csv('data/processed/y_train.csv').values.ravel())
X_test = torch.FloatTensor(pd.read_csv('data/processed/X_test.csv').values)
y_test = torch.LongTensor(pd.read_csv('data/processed/y_test.csv').values.ravel())

# Create data loaders
train_dataset = TensorDataset(X_train, y_train)
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

# Model
class NeuralNet(nn.Module):
    def __init__(self, input_size):
        super().__init__()
        self.fc1 = nn.Linear(input_size, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 2)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.2)
    
    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return x

model = NeuralNet(X_train.shape[1])
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=1e-3)

# Training loop
for epoch in range(100):
    for batch_x, batch_y in train_loader:
        outputs = model(batch_x)
        loss = criterion(outputs, batch_y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

# Evaluation
model.eval()
with torch.no_grad():
    predictions = torch.argmax(model(X_test), dim=1)
    accuracy = (predictions == y_test).float().mean().item()

print(f"Test Accuracy: {accuracy:.4f}")

# Save model
torch.save(model.state_dict(), 'models/neural_net.pt')
print("Model saved!")
"""
    
    def _pytorch_lstm_script(self) -> str:
        """Generate PyTorch LSTM training script"""
        return """
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd

# Load time series data
X_train = torch.FloatTensor(pd.read_csv('data/processed/X_train.csv').values)
y_train = torch.FloatTensor(pd.read_csv('data/processed/y_train.csv').values)

# Reshape for LSTM (batch_size, seq_length, features)
X_train = X_train.unsqueeze(1)

# Model
class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size=64, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)
    
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        output = self.fc(lstm_out[:, -1, :])
        return output

model = LSTMModel(X_train.shape[2])
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=1e-3)

# Training loop
for epoch in range(100):
    outputs = model(X_train)
    loss = criterion(outputs.squeeze(), y_train)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

print(f"Training loss: {loss.item():.4f}")

# Save model
torch.save(model.state_dict(), 'models/lstm_model.pt')
print("Model saved!")
"""
    
    def _huggingface_bert_script(self) -> str:
        """Generate HuggingFace BERT training script"""
        return """
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
from datasets import load_dataset
import pandas as pd

# Load data
df = pd.read_csv('data/raw/data.csv')
dataset = load_dataset('csv', data_files='data/raw/data.csv')
dataset = dataset['train'].train_test_split(test_size=0.2)

# Tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

def tokenize_function(examples):
    return tokenizer(examples['text'], padding='max_length', truncation=True, max_length=128)

dataset = dataset.map(tokenize_function, batched=True)

# Model
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)

# Training
training_args = TrainingArguments(
    output_dir='models/bert_checkpoint',
    num_train_epochs=3,
    per_device_train_batch_size=32,
    per_device_eval_batch_size=32,
    learning_rate=2e-5,
    evaluation_strategy='epoch',
    save_strategy='epoch',
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset['train'],
    eval_dataset=dataset['test'],
)

trainer.train()
trainer.save_model('models/bert_model')
print("Model saved!")
"""
    
    def _pytorch_vision_script(self, model_name: str = "resnet50") -> str:
        """Generate PyTorch vision model training script"""
        return f"""
import torch
import torchvision.models as models
import torch.nn as nn
import torch.optim as optim
from torchvision import transforms
from torch.utils.data import DataLoader, ImageFolder

# Data transforms
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225])
])

# Load data
train_dataset = ImageFolder('data/train', transform=transform)
test_dataset = ImageFolder('data/test', transform=transform)
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32)

# Model
model = models.{model_name}(pretrained=True)
num_classes = len(train_dataset.classes)
model.fc = nn.Linear(model.fc.in_features, num_classes)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=1e-4)

# Training
for epoch in range(10):
    for batch_x, batch_y in train_loader:
        outputs = model(batch_x)
        loss = criterion(outputs, batch_y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

# Evaluation
correct = 0
total = 0
with torch.no_grad():
    for batch_x, batch_y in test_loader:
        outputs = model(batch_x)
        _, predicted = torch.max(outputs, 1)
        total += batch_y.size(0)
        correct += (predicted == batch_y).sum().item()

accuracy = 100 * correct / total
print(f"Accuracy: {{accuracy:.2f}}%")

# Save model
torch.save(model.state_dict(), 'models/{model_name}_model.pt')
print("Model saved!")
"""
    
    def get_hyperparameter_tuning_code(self, strategy: str = "grid_search") -> str:
        """Generate hyperparameter tuning code"""
        templates = {
            "grid_search": """
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier

param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15],
    'min_samples_split': [2, 5, 10]
}

base_model = RandomForestClassifier()
grid_search = GridSearchCV(base_model, param_grid, cv=5, n_jobs=-1, verbose=1)
grid_search.fit(X_train, y_train)

print(f"Best params: {grid_search.best_params_}")
print(f"Best CV score: {grid_search.best_score_:.4f}")

best_model = grid_search.best_estimator_
""",
            
            "random_search": """
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import randint
import numpy as np

param_dist = {
    'n_estimators': randint(50, 200),
    'max_depth': randint(5, 20),
    'min_samples_split': randint(2, 10)
}

base_model = RandomForestClassifier()
random_search = RandomizedSearchCV(base_model, param_dist, n_iter=20, cv=5, n_jobs=-1)
random_search.fit(X_train, y_train)

print(f"Best params: {random_search.best_params_}")
print(f"Best CV score: {random_search.best_score_:.4f}")

best_model = random_search.best_estimator_
""",
            
            "bayesian": """
from skopt import BayesSearchCV
from skopt.space import Integer

param_space = {
    'n_estimators': Integer(50, 200),
    'max_depth': Integer(5, 20),
    'min_samples_split': Integer(2, 10)
}

base_model = RandomForestClassifier()
bayes_search = BayesSearchCV(base_model, param_space, n_iter=20, cv=5, n_jobs=-1)
bayes_search.fit(X_train, y_train)

print(f"Best params: {bayes_search.best_params_}")
print(f"Best CV score: {bayes_search.best_score_:.4f}")

best_model = bayes_search.best_estimator_
"""
        }
        
        return templates.get(strategy, "")
    
    def record_training_metrics(
        self,
        model_name: str,
        epoch: int,
        loss: float,
        train_metric: float,
        val_metric: float,
        learning_rate: float = 0.001,
        batch_size: int = 32
    ) -> TrainingMetrics:
        """Record training metrics"""
        metrics = TrainingMetrics(
            epoch=epoch,
            loss=loss,
            train_metric=train_metric,
            val_metric=val_metric,
            learning_rate=learning_rate,
            batch_size=batch_size
        )
        
        if model_name not in self.training_history:
            self.training_history[model_name] = []
        
        self.training_history[model_name].append(metrics)
        
        return metrics
    
    def record_evaluation(
        self,
        model_name: str,
        primary_metric_value: float,
        secondary_metrics: Dict[str, float],
        confusion_matrix: Optional[List[List[int]]] = None,
        feature_importance: Optional[Dict[str, float]] = None,
        training_time_seconds: float = 0.0,
        inference_time_ms: float = 0.0
    ) -> EvaluationResults:
        """Record model evaluation results"""
        results = EvaluationResults(
            model_name=model_name,
            primary_metric_value=primary_metric_value,
            secondary_metrics=secondary_metrics,
            confusion_matrix=confusion_matrix,
            feature_importance=feature_importance,
            training_time_seconds=training_time_seconds,
            inference_time_ms=inference_time_ms
        )
        
        self.evaluation_results[model_name] = results
        
        return results
    
    def get_training_history(self, model_name: str) -> List[TrainingMetrics]:
        """Get training history for model"""
        return self.training_history.get(model_name, [])
    
    def get_evaluation_results(self, model_name: str) -> Optional[EvaluationResults]:
        """Get evaluation results for model"""
        return self.evaluation_results.get(model_name)


# Singleton factory
_trainer_instance: Optional[ModelTrainer] = None


def get_model_trainer() -> ModelTrainer:
    """Get ModelTrainer singleton"""
    global _trainer_instance
    if _trainer_instance is None:
        _trainer_instance = ModelTrainer()
        logger.info("ModelTrainer initialized")
    return _trainer_instance
