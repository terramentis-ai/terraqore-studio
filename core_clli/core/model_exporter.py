"""
Model Export & Versioning - Phase 5.3 Week 3

Model persistence, versioning, and metadata management
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class ModelFormat(Enum):
    """Model serialization formats"""
    PICKLE = "pickle"
    JOBLIB = "joblib"
    ONNX = "onnx"
    TENSORFLOW = "tensorflow"
    PYTORCH = "pytorch"
    HUGGINGFACE = "huggingface"
    PMML = "pmml"


class ModelFramework(Enum):
    """Model frameworks"""
    SCIKIT_LEARN = "scikit_learn"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    HUGGINGFACE = "huggingface"


@dataclass
class ModelMetadata:
    """Model metadata"""
    model_name: str
    version: str
    framework: ModelFramework
    created_at: datetime
    trained_by: str  # agent/user
    training_duration: float  # seconds
    training_samples: int
    input_shape: Dict[str, Any]
    output_shape: Dict[str, Any]
    performance_metrics: Dict[str, float]
    hyperparameters: Dict[str, Any]
    feature_names: List[str]
    preprocessing_steps: List[str] = field(default_factory=list)
    description: str = ""
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'model_name': self.model_name,
            'version': self.version,
            'framework': self.framework.value,
            'created_at': self.created_at.isoformat(),
            'trained_by': self.trained_by,
            'training_duration': self.training_duration,
            'training_samples': self.training_samples,
            'input_shape': self.input_shape,
            'output_shape': self.output_shape,
            'performance_metrics': self.performance_metrics,
            'hyperparameters': self.hyperparameters,
            'preprocessing_steps': self.preprocessing_steps,
            'feature_names': self.feature_names,
            'description': self.description,
            'tags': self.tags
        }


@dataclass
class ModelArtifact:
    """Model artifact storage"""
    model_id: str
    metadata: ModelMetadata
    model_path: str
    preprocessor_path: Optional[str] = None
    scaler_path: Optional[str] = None
    encoder_path: Optional[str] = None
    feature_selector_path: Optional[str] = None
    config_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'model_id': self.model_id,
            'metadata': self.metadata.to_dict(),
            'model_path': self.model_path,
            'preprocessor_path': self.preprocessor_path,
            'scaler_path': self.scaler_path,
            'encoder_path': self.encoder_path,
            'feature_selector_path': self.feature_selector_path,
            'config_path': self.config_path,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'access_count': self.access_count
        }


class ModelExporter:
    """Export and manage model versions"""
    
    def __init__(self):
        """Initialize model exporter"""
        self.model_registry: Dict[str, ModelArtifact] = {}
        self.version_history: Dict[str, List[str]] = {}  # model_name -> [versions]
    
    def get_sklearn_export_code(self) -> str:
        """Generate scikit-learn model export code"""
        return """
import joblib
import pickle
import json
from datetime import datetime

# Save scikit-learn model
model_name = 'random_forest_v1'
model_dir = f'models/{model_name}'

# Method 1: Joblib (recommended for sklearn)
joblib.dump(model, f'{model_dir}/model.joblib')
joblib.dump(preprocessor, f'{model_dir}/preprocessor.joblib')
joblib.dump(scaler, f'{model_dir}/scaler.joblib')

# Method 2: Pickle (smaller file size)
with open(f'{model_dir}/model.pkl', 'wb') as f:
    pickle.dump(model, f)

# Save metadata
metadata = {
    'model_name': model_name,
    'framework': 'scikit_learn',
    'created_at': datetime.now().isoformat(),
    'performance': {
        'accuracy': 0.94,
        'precision': 0.93,
        'recall': 0.92,
        'f1': 0.92
    },
    'hyperparameters': {
        'n_estimators': 100,
        'max_depth': 10,
        'random_state': 42
    },
    'feature_names': list(X_train.columns),
    'input_shape': [X_train.shape[0], X_train.shape[1]],
    'output_shape': [1]
}

with open(f'{model_dir}/metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

# Load model
loaded_model = joblib.load(f'{model_dir}/model.joblib')
loaded_prep = joblib.load(f'{model_dir}/preprocessor.joblib')

# Make predictions
predictions = loaded_model.predict(X_test)
"""
    
    def get_xgboost_export_code(self) -> str:
        """Generate XGBoost model export code"""
        return """
import json
from datetime import datetime

# Save XGBoost model
model_name = 'xgboost_v1'
model_dir = f'models/{model_name}'

# Method 1: Native XGBoost format
model.save_model(f'{model_dir}/model.json')

# Method 2: Binary format (faster loading)
model.save_model(f'{model_dir}/model.ubj')

# Method 3: Convert to ONNX
import skl2onnx
from skl2onnx.common.data_types import FloatTensorType

initial_type = [('float_input', FloatTensorType([None, X_train.shape[1]]))]
onnx_model = skl2onnx.convert_model(model, initial_types=initial_type)

with open(f'{model_dir}/model.onnx', 'wb') as f:
    f.write(onnx_model.SerializeToString())

# Save metadata with feature importance
metadata = {
    'model_name': model_name,
    'framework': 'xgboost',
    'created_at': datetime.now().isoformat(),
    'performance': {
        'auc': 0.96,
        'logloss': 0.15
    },
    'hyperparameters': {
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 100
    },
    'feature_names': feature_names,
    'feature_importance': dict(zip(
        feature_names,
        model.feature_importances_
    ))
}

with open(f'{model_dir}/metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

# Load and use model
loaded_model = xgb.Booster(model_file=f'{model_dir}/model.json')
dmatrix = xgb.DMatrix(X_test)
predictions = loaded_model.predict(dmatrix)
"""
    
    def get_pytorch_export_code(self) -> str:
        """Generate PyTorch model export code"""
        return """
import torch
import torch.onnx
import json
from datetime import datetime

model_name = 'pytorch_classifier_v1'
model_dir = f'models/{model_name}'

# Method 1: State dict (recommended)
torch.save(model.state_dict(), f'{model_dir}/model_state.pth')
torch.save(optimizer.state_dict(), f'{model_dir}/optimizer_state.pth')

# Method 2: Full model
torch.save(model, f'{model_dir}/model_full.pth')

# Method 3: TorchScript
scripted_model = torch.jit.script(model)
scripted_model.save(f'{model_dir}/model_scripted.pt')

# Method 4: ONNX format
dummy_input = torch.randn(1, input_size)
torch.onnx.export(
    model,
    dummy_input,
    f'{model_dir}/model.onnx',
    input_names=['input'],
    output_names=['output'],
    opset_version=12
)

# Save metadata
metadata = {
    'model_name': model_name,
    'framework': 'pytorch',
    'architecture': str(model),
    'created_at': datetime.now().isoformat(),
    'device': str(next(model.parameters()).device),
    'performance': {
        'accuracy': 0.95,
        'loss': 0.12
    },
    'input_shape': [1, input_size],
    'output_shape': [1, num_classes],
    'hyperparameters': {
        'learning_rate': 0.001,
        'batch_size': 32,
        'epochs': 50
    }
}

with open(f'{model_dir}/metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

# Load model
model = ModelClass()
model.load_state_dict(torch.load(f'{model_dir}/model_state.pth'))
model.eval()

# Inference
with torch.no_grad():
    inputs = torch.randn(batch_size, input_size)
    outputs = model(inputs)
"""
    
    def get_tensorflow_export_code(self) -> str:
        """Generate TensorFlow model export code"""
        return """
import tensorflow as tf
import json
from datetime import datetime

model_name = 'tensorflow_model_v1'
model_dir = f'models/{model_name}'

# Method 1: SavedModel format (recommended)
model.save(f'{model_dir}/saved_model')

# Method 2: HDF5 format
model.save(f'{model_dir}/model.h5')

# Method 3: TFLite (mobile/edge)
converter = tf.lite.TFLiteConverter.from_saved_model(f'{model_dir}/saved_model')
tflite_model = converter.convert()
with open(f'{model_dir}/model.tflite', 'wb') as f:
    f.write(tflite_model)

# Method 4: ONNX
import tf2onnx
spec = (tf.TensorSpec((None, input_shape), tf.float32, name='input'))
output_path = f'{model_dir}/model.onnx'
tf2onnx.convert.from_keras(model, input_signature=spec, output_path=output_path)

# Save metadata
metadata = {
    'model_name': model_name,
    'framework': 'tensorflow',
    'created_at': datetime.now().isoformat(),
    'input_shape': model.input_shape,
    'output_shape': model.output_shape,
    'performance': {
        'accuracy': 0.94,
        'loss': 0.18,
        'val_accuracy': 0.92
    },
    'hyperparameters': {
        'optimizer': 'adam',
        'loss': 'categorical_crossentropy',
        'metrics': ['accuracy'],
        'epochs': 50,
        'batch_size': 32
    }
}

with open(f'{model_dir}/metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

# Load model
loaded_model = tf.keras.models.load_model(f'{model_dir}/saved_model')

# Inference
predictions = loaded_model.predict(X_test)
"""
    
    def get_huggingface_export_code(self) -> str:
        """Generate Hugging Face model export code"""
        return """
from transformers import AutoModel, AutoTokenizer
import json
from datetime import datetime

model_name = 'huggingface_bert_v1'
model_dir = f'models/{model_name}'

# Save model and tokenizer
model.save_pretrained(f'{model_dir}/model')
tokenizer.save_pretrained(f'{model_dir}/tokenizer')

# Save training config
config = {
    'model_name': model_name,
    'base_model': 'bert-base-uncased',
    'created_at': datetime.now().isoformat(),
    'training_config': {
        'learning_rate': 2e-5,
        'batch_size': 32,
        'num_epochs': 3,
        'max_length': 128
    },
    'performance': {
        'accuracy': 0.93,
        'f1': 0.92,
        'loss': 0.19
    },
    'task': 'text_classification',
    'num_labels': 2
}

with open(f'{model_dir}/config.json', 'w') as f:
    json.dump(config, f, indent=2)

# Load and use
from transformers import AutoModelForSequenceClassification, pipeline

loaded_model = AutoModelForSequenceClassification.from_pretrained(
    f'{model_dir}/model'
)
loaded_tokenizer = AutoTokenizer.from_pretrained(f'{model_dir}/tokenizer')

# Pipeline for easy inference
classifier = pipeline(
    'text-classification',
    model=loaded_model,
    tokenizer=loaded_tokenizer
)

result = classifier('This is a great product!')
"""
    
    def register_model(
        self,
        model_id: str,
        metadata: ModelMetadata,
        model_path: str,
        preprocessor_path: Optional[str] = None,
        scaler_path: Optional[str] = None,
        encoder_path: Optional[str] = None
    ) -> ModelArtifact:
        """Register model artifact"""
        artifact = ModelArtifact(
            model_id=model_id,
            metadata=metadata,
            model_path=model_path,
            preprocessor_path=preprocessor_path,
            scaler_path=scaler_path,
            encoder_path=encoder_path
        )
        
        self.model_registry[model_id] = artifact
        
        model_name = metadata.model_name
        if model_name not in self.version_history:
            self.version_history[model_name] = []
        self.version_history[model_name].append(metadata.version)
        
        logger.info(f"Registered model: {model_id}")
        
        return artifact
    
    def get_model(self, model_id: str) -> Optional[ModelArtifact]:
        """Get model artifact"""
        if model_id in self.model_registry:
            artifact = self.model_registry[model_id]
            artifact.access_count += 1
            artifact.last_accessed = datetime.now()
            return artifact
        return None
    
    def get_latest_version(self, model_name: str) -> Optional[str]:
        """Get latest model version"""
        if model_name in self.version_history:
            versions = self.version_history[model_name]
            return versions[-1] if versions else None
        return None
    
    def list_versions(self, model_name: str) -> List[str]:
        """List all versions of model"""
        return self.version_history.get(model_name, [])
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get model information"""
        artifact = self.get_model(model_id)
        if artifact:
            return artifact.to_dict()
        return None


# Singleton factory
_exporter_instance: Optional[ModelExporter] = None


def get_model_exporter() -> ModelExporter:
    """Get ModelExporter singleton"""
    global _exporter_instance
    if _exporter_instance is None:
        _exporter_instance = ModelExporter()
        logger.info("ModelExporter initialized")
    return _exporter_instance
