"""
ML Pipeline Builder - Phase 5.3 Week 3

Data transformation pipelines and workflow orchestration
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Pipeline stages"""
    DATA_LOADING = "data_loading"
    DATA_VALIDATION = "data_validation"
    DATA_CLEANING = "data_cleaning"
    FEATURE_ENGINEERING = "feature_engineering"
    FEATURE_SCALING = "feature_scaling"
    FEATURE_SELECTION = "feature_selection"
    TRAIN_TEST_SPLIT = "train_test_split"
    MODEL_TRAINING = "model_training"
    MODEL_EVALUATION = "model_evaluation"
    MODEL_EXPORT = "model_export"


@dataclass
class PipelineStep:
    """Single pipeline step"""
    name: str
    stage: PipelineStage
    input_type: str  # 'dataframe', 'array', 'model', etc.
    output_type: str
    handler: Optional[Callable] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    
    def execute(self, data: Any) -> Any:
        """Execute pipeline step"""
        if self.handler:
            return self.handler(data, **self.parameters)
        return data


@dataclass
class PipelineConfig:
    """Pipeline configuration"""
    name: str
    version: str
    steps: List[PipelineStep]
    description: str = ""
    tags: List[str] = field(default_factory=list)
    error_handling: str = "stop"  # 'stop', 'skip', 'fallback'
    logging_level: str = "info"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'version': self.version,
            'steps': [
                {
                    'name': step.name,
                    'stage': step.stage.value,
                    'input_type': step.input_type,
                    'output_type': step.output_type,
                    'description': step.description
                }
                for step in self.steps
            ],
            'description': self.description,
            'tags': self.tags,
            'error_handling': self.error_handling
        }


class MLPipelineBuilder:
    """Build and manage ML pipelines"""
    
    def __init__(self):
        """Initialize pipeline builder"""
        self.pipelines: Dict[str, PipelineConfig] = {}
        self.execution_logs: Dict[str, List[Dict[str, Any]]] = {}
    
    def get_sklearn_pipeline_code(self) -> str:
        """Generate scikit-learn pipeline code"""
        return """
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

# Create preprocessing pipeline
preprocessing = Pipeline([
    ('scaler', StandardScaler()),
    ('selector', SelectKBest(f_classif, k=10))
])

# Create full pipeline
ml_pipeline = Pipeline([
    ('preprocessing', preprocessing),
    ('model', RandomForestClassifier(n_estimators=100, random_state=42))
])

# Fit pipeline
ml_pipeline.fit(X_train, y_train)

# Make predictions
predictions = ml_pipeline.predict(X_test)

# Get predictions from intermediate step
scaled_data = ml_pipeline.named_steps['preprocessing'].transform(X_test)

# Save pipeline
import joblib
joblib.dump(ml_pipeline, 'models/pipeline.joblib')

# Load and use
loaded_pipeline = joblib.load('models/pipeline.joblib')
new_predictions = loaded_pipeline.predict(new_data)
"""
    
    def get_custom_pipeline_code(self) -> str:
        """Generate custom pipeline code"""
        return """
import pandas as pd
import numpy as np
from typing import Dict, Any

class DataPipeline:
    \"\"\"Custom data processing pipeline\"\"\"
    
    def __init__(self, name: str):
        self.name = name
        self.steps = []
        self.state = {}
    
    def add_step(self, name: str, func, **kwargs):
        \"\"\"Add processing step\"\"\"
        self.steps.append({
            'name': name,
            'func': func,
            'kwargs': kwargs
        })
        return self
    
    def execute(self, data):
        \"\"\"Execute pipeline\"\"\"
        print(f"Starting pipeline: {self.name}")
        
        current_data = data.copy() if isinstance(data, pd.DataFrame) else data
        
        for i, step in enumerate(self.steps):
            print(f"  Step {i+1}: {step['name']}")
            try:
                current_data = step['func'](current_data, **step['kwargs'])
                self.state[step['name']] = current_data
                print(f"    ✓ Shape: {current_data.shape if hasattr(current_data, 'shape') else 'N/A'}")
            except Exception as e:
                print(f"    ✗ Error: {str(e)}")
                raise
        
        return current_data
    
    def get_step_output(self, step_name: str):
        \"\"\"Get output from specific step\"\"\"
        return self.state.get(step_name)


# Define custom functions
def load_data(path: str, **kwargs):
    return pd.read_csv(path)

def clean_data(df: pd.DataFrame, **kwargs):
    df = df.dropna()
    df = df[df.duplicated() == False]
    return df

def engineer_features(df: pd.DataFrame, **kwargs):
    df['feature1_squared'] = df['feature1'] ** 2
    df['feature1_feature2'] = df['feature1'] * df['feature2']
    return df

def scale_features(df: pd.DataFrame, **kwargs):
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    scaled_cols = scaler.fit_transform(df.select_dtypes(include=[np.number]))
    return pd.DataFrame(scaled_cols, columns=df.select_dtypes(include=[np.number]).columns)

# Build pipeline
pipeline = DataPipeline('data_processing')
pipeline.add_step('load', load_data, path='data/raw.csv')
pipeline.add_step('clean', clean_data)
pipeline.add_step('engineer', engineer_features)
pipeline.add_step('scale', scale_features)

# Execute
processed_data = pipeline.execute('data/raw.csv')
print(f"Final shape: {processed_data.shape}")
"""
    
    def get_dask_pipeline_code(self) -> str:
        """Generate distributed Dask pipeline code"""
        return """
import dask.dataframe as dd
import pandas as pd
from dask import delayed

# Load large dataset with Dask
df = dd.read_csv('data/large_*.csv')

# Distributed preprocessing
df['new_feature'] = df['feature1'] * df['feature2']
df = df[df['target'].notna()]

# Partition for parallel processing
partitioned = df.to_delayed()

# Process each partition
@delayed
def process_partition(partition):
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    numeric_cols = partition.select_dtypes(include=['number']).columns
    partition[numeric_cols] = scaler.fit_transform(partition[numeric_cols])
    return partition

# Apply to all partitions
processed = [process_partition(p) for p in partitioned]

# Combine results
result = dd.from_delayed(processed, meta=df._meta)

# Compute final result
final_data = result.compute()
"""
    
    def get_feature_pipeline_code(self) -> str:
        """Generate feature engineering pipeline code"""
        return """
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.decomposition import PCA
import pandas as pd

# Numeric feature pipeline
numeric_pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('poly', PolynomialFeatures(degree=2))
])

# Categorical feature pipeline
from sklearn.preprocessing import OneHotEncoder
categorical_pipeline = Pipeline([
    ('onehot', OneHotEncoder(sparse_output=False, handle_unknown='ignore'))
])

# Combine pipelines
feature_union = FeatureUnion([
    ('numeric', numeric_pipeline),
    ('categorical', categorical_pipeline)
])

# Full pipeline
full_pipeline = Pipeline([
    ('features', feature_union),
    ('pca', PCA(n_components=20)),
    ('scale_final', StandardScaler())
])

# Fit and transform
X_transformed = full_pipeline.fit_transform(X_train)

# Save
import joblib
joblib.dump(full_pipeline, 'models/feature_pipeline.joblib')
"""
    
    def create_pipeline(
        self,
        name: str,
        version: str,
        steps: List[PipelineStep],
        description: str = ""
    ) -> PipelineConfig:
        """Create pipeline configuration"""
        config = PipelineConfig(
            name=name,
            version=version,
            steps=steps,
            description=description
        )
        
        self.pipelines[name] = config
        self.execution_logs[name] = []
        
        logger.info(f"Created pipeline: {name} v{version} with {len(steps)} steps")
        
        return config
    
    def get_pipeline(self, name: str) -> Optional[PipelineConfig]:
        """Get pipeline configuration"""
        return self.pipelines.get(name)
    
    def execute_pipeline(
        self,
        pipeline_name: str,
        data: Any
    ) -> Dict[str, Any]:
        """Execute pipeline"""
        pipeline = self.get_pipeline(pipeline_name)
        if not pipeline:
            logger.error(f"Pipeline not found: {pipeline_name}")
            return {'success': False, 'error': 'Pipeline not found'}
        
        try:
            current_data = data
            execution_log = {
                'pipeline': pipeline_name,
                'status': 'running',
                'steps': []
            }
            
            for step in pipeline.steps:
                step_result = {
                    'name': step.name,
                    'stage': step.stage.value,
                    'status': 'completed'
                }
                
                try:
                    current_data = step.execute(current_data)
                    step_result['output_shape'] = (
                        current_data.shape if hasattr(current_data, 'shape') else 'N/A'
                    )
                except Exception as e:
                    step_result['status'] = 'failed'
                    step_result['error'] = str(e)
                    
                    if pipeline.error_handling == 'stop':
                        raise
                
                execution_log['steps'].append(step_result)
            
            execution_log['status'] = 'completed'
            self.execution_logs[pipeline_name].append(execution_log)
            
            return {
                'success': True,
                'data': current_data,
                'log': execution_log
            }
        
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_execution_history(self, pipeline_name: str) -> List[Dict[str, Any]]:
        """Get pipeline execution history"""
        return self.execution_logs.get(pipeline_name, [])


# Singleton factory
_builder_instance: Optional[MLPipelineBuilder] = None


def get_pipeline_builder() -> MLPipelineBuilder:
    """Get MLPipelineBuilder singleton"""
    global _builder_instance
    if _builder_instance is None:
        _builder_instance = MLPipelineBuilder()
        logger.info("MLPipelineBuilder initialized")
    return _builder_instance
