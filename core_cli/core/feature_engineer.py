"""
Feature Engineering Utilities - Phase 5.3 Data Science Agent

Generates and processes features for ML models
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FeatureType(Enum):
    """Feature types"""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    TEXT = "text"
    IMAGE = "image"


class EncodingStrategy(Enum):
    """Categorical encoding strategies"""
    ONEHOT = "onehot"
    LABEL = "label"
    TARGET = "target_encoding"
    FREQUENCY = "frequency"
    ORDINAL = "ordinal"


class ScalingStrategy(Enum):
    """Numeric scaling strategies"""
    STANDARD = "standard"  # z-score
    MINMAX = "minmax"
    ROBUST = "robust"      # IQR-based
    LOG = "log"
    YEOJONSON = "yeo_johnson"


@dataclass
class FeatureStatistics:
    """Feature statistics and metadata"""
    name: str
    feature_type: FeatureType
    data_type: str  # "int64", "float64", "object", etc.
    missing_count: int
    missing_percent: float
    cardinality: int  # Number of unique values
    dtype_inferred: str
    
    # Numeric stats
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    median: Optional[float] = None
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None
    
    # Categorical stats
    top_categories: List[Tuple[str, int]] = field(default_factory=list)
    
    # Correlations
    correlations: Dict[str, float] = field(default_factory=dict)
    mutual_information: Dict[str, float] = field(default_factory=dict)


@dataclass
class FeatureEngineering:
    """Feature engineering configuration"""
    name: str
    features: List[str]
    feature_types: Dict[str, FeatureType]
    scaling_strategy: Optional[ScalingStrategy] = None
    encoding_strategy: EncodingStrategy = EncodingStrategy.ONEHOT
    
    # Feature operations
    create_interactions: bool = False
    create_polynomials: bool = False
    polynomial_degree: int = 2
    create_aggregations: bool = False
    create_lags: bool = False
    lag_periods: List[int] = field(default_factory=list)
    
    # Feature selection
    feature_selection: bool = False
    selection_method: str = "correlation"  # "correlation", "mutual_info", "rfe"
    n_features_to_select: Optional[int] = None
    
    created_at: datetime = field(default_factory=datetime.now)


class FeatureEngineer:
    """Feature engineering utilities"""
    
    def __init__(self):
        """Initialize feature engineer"""
        self.features: Dict[str, FeatureEngineering] = {}
        self.statistics: Dict[str, FeatureStatistics] = {}
    
    def analyze_features(self, data: Dict[str, List[Any]]) -> Dict[str, FeatureStatistics]:
        """Analyze feature statistics from data"""
        statistics = {}
        
        for col_name, col_data in data.items():
            # Infer type
            feature_type = self._infer_feature_type(col_data)
            
            # Calculate statistics
            stats = FeatureStatistics(
                name=col_name,
                feature_type=feature_type,
                data_type=str(type(col_data[0]).__name__),
                missing_count=sum(1 for v in col_data if v is None),
                missing_percent=sum(1 for v in col_data if v is None) / len(col_data) * 100,
                cardinality=len(set(v for v in col_data if v is not None)),
                dtype_inferred=feature_type.value
            )
            
            # Calculate numeric statistics
            if feature_type == FeatureType.NUMERIC:
                numeric_vals = [v for v in col_data if v is not None and isinstance(v, (int, float))]
                if numeric_vals:
                    stats.mean = sum(numeric_vals) / len(numeric_vals)
                    stats.min = min(numeric_vals)
                    stats.max = max(numeric_vals)
                    stats.median = sorted(numeric_vals)[len(numeric_vals) // 2]
            
            # Calculate categorical statistics
            elif feature_type == FeatureType.CATEGORICAL:
                value_counts = {}
                for v in col_data:
                    if v is not None:
                        value_counts[v] = value_counts.get(v, 0) + 1
                stats.top_categories = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            statistics[col_name] = stats
        
        self.statistics.update(statistics)
        logger.info(f"Analyzed {len(statistics)} features")
        
        return statistics
    
    def _infer_feature_type(self, data: List[Any]) -> FeatureType:
        """Infer feature type from data"""
        sample = [v for v in data if v is not None][:100]
        
        if not sample:
            return FeatureType.NUMERIC
        
        # Check numeric
        if all(isinstance(v, (int, float)) for v in sample):
            return FeatureType.NUMERIC
        
        # Check categorical
        if all(isinstance(v, str) for v in sample) and len(set(sample)) < 100:
            return FeatureType.CATEGORICAL
        
        # Check datetime
        if all(isinstance(v, str) for v in sample):
            # Simple check for datetime format
            date_indicators = ["2020", "2021", "2022", "2023", "2024", "-", "/"]
            if any(ind in str(sample[0]) for ind in date_indicators):
                return FeatureType.DATETIME
        
        # Check text
        if all(isinstance(v, str) for v in sample):
            avg_length = sum(len(str(v)) for v in sample) / len(sample)
            if avg_length > 50:
                return FeatureType.TEXT
        
        return FeatureType.CATEGORICAL
    
    def create_feature_engineering_plan(
        self,
        name: str,
        feature_types: Dict[str, FeatureType],
        scaling_strategy: Optional[ScalingStrategy] = None,
        encoding_strategy: EncodingStrategy = EncodingStrategy.ONEHOT,
        create_interactions: bool = False,
        create_polynomials: bool = False,
        feature_selection: bool = False
    ) -> FeatureEngineering:
        """Create feature engineering plan"""
        
        plan = FeatureEngineering(
            name=name,
            features=list(feature_types.keys()),
            feature_types=feature_types,
            scaling_strategy=scaling_strategy,
            encoding_strategy=encoding_strategy,
            create_interactions=create_interactions,
            create_polynomials=create_polynomials,
            create_aggregations=False,
            feature_selection=feature_selection,
            selection_method="correlation"
        )
        
        self.features[name] = plan
        logger.info(f"Created feature engineering plan: {name}")
        
        return plan
    
    def get_scaling_code(self, strategy: ScalingStrategy) -> str:
        """Generate scaling code"""
        templates = {
            ScalingStrategy.STANDARD: """from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)""",
            
            ScalingStrategy.MINMAX: """from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)""",
            
            ScalingStrategy.ROBUST: """from sklearn.preprocessing import RobustScaler
scaler = RobustScaler()
X_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)""",
            
            ScalingStrategy.LOG: """import numpy as np
X_scaled = np.log1p(X_train)
X_test_scaled = np.log1p(X_test)""",
            
            ScalingStrategy.YEOJONSON: """from sklearn.preprocessing import PowerTransformer
pt = PowerTransformer(method='yeo-johnson')
X_scaled = pt.fit_transform(X_train)
X_test_scaled = pt.transform(X_test)"""
        }
        
        return templates.get(strategy, "")
    
    def get_encoding_code(self, strategy: EncodingStrategy) -> str:
        """Generate encoding code"""
        templates = {
            EncodingStrategy.ONEHOT: """from sklearn.preprocessing import OneHotEncoder
encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
X_cat_encoded = encoder.fit_transform(X_train[categorical_features])
X_test_encoded = encoder.transform(X_test[categorical_features])""",
            
            EncodingStrategy.LABEL: """from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()
X_encoded = X_train.copy()
for col in categorical_features:
    X_encoded[col] = le.fit_transform(X_train[col].astype(str))""",
            
            EncodingStrategy.TARGET: """# Target encoding requires target variable
target_stats = df.groupby(cat_col)[target].agg(['mean', 'count'])
target_encoding = target_stats['mean'].to_dict()
X_encoded[cat_col] = X_train[cat_col].map(target_encoding)""",
            
            EncodingStrategy.FREQUENCY: """# Frequency encoding
freq_encoding = X_train[cat_col].value_counts(normalize=True).to_dict()
X_encoded[cat_col] = X_train[cat_col].map(freq_encoding)""",
            
            EncodingStrategy.ORDINAL: """from sklearn.preprocessing import OrdinalEncoder
encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
X_encoded = encoder.fit_transform(X_train[categorical_features])"""
        }
        
        return templates.get(strategy, "")
    
    def get_interaction_code(self) -> str:
        """Generate interaction feature code"""
        return """from sklearn.preprocessing import PolynomialFeatures
poly = PolynomialFeatures(degree=2, include_bias=False, interaction_only=True)
X_interactions = poly.fit_transform(X_train[numeric_features])
X_test_interactions = poly.transform(X_test[numeric_features])
interaction_features = poly.get_feature_names_out(numeric_features)"""
    
    def get_polynomial_code(self, degree: int = 2) -> str:
        """Generate polynomial feature code"""
        return f"""from sklearn.preprocessing import PolynomialFeatures
poly = PolynomialFeatures(degree={degree}, include_bias=False)
X_poly = poly.fit_transform(X_train[numeric_features])
X_test_poly = poly.transform(X_test[numeric_features])
poly_features = poly.get_feature_names_out(numeric_features)"""
    
    def get_selection_code(self, method: str = "correlation") -> str:
        """Generate feature selection code"""
        templates = {
            "correlation": """# Remove features with low correlation to target
correlation_threshold = 0.1
selected_features = [f for f in features 
                     if abs(X_train[f].corr(y_train)) > correlation_threshold]""",
            
            "mutual_info": """from sklearn.feature_selection import mutual_info_classif
scores = mutual_info_classif(X_train, y_train)
selected_features = [f for f, s in zip(features, scores) if s > score_threshold]""",
            
            "rfe": """from sklearn.feature_selection import RFE
from sklearn.ensemble import RandomForestClassifier
selector = RFE(RandomForestClassifier(), n_features_to_select=20)
X_selected = selector.fit_transform(X_train, y_train)
selected_features = [f for f, s in zip(features, selector.support_) if s]"""
        }
        
        return templates.get(method, "")
    
    def generate_feature_engineering_script(self, name: str) -> str:
        """Generate complete feature engineering script"""
        plan = self.features.get(name)
        if not plan:
            return ""
        
        script = f"""\"\"\"
Feature Engineering Script - {name}
Generated: {datetime.now()}
\"\"\"

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split

# Load data
df = pd.read_csv('data/raw/data.csv')

# Split data
X = df.drop('target', axis=1)
y = df['target']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Numeric features
numeric_features = {[f for f, t in plan.feature_types.items() if t == FeatureType.NUMERIC]}
categorical_features = {[f for f, t in plan.feature_types.items() if t == FeatureType.CATEGORICAL]}

"""
        
        if plan.scaling_strategy:
            script += f"# Scaling: {plan.scaling_strategy.value}\n"
            script += self.get_scaling_code(plan.scaling_strategy) + "\n\n"
        
        if plan.encoding_strategy:
            script += f"# Encoding: {plan.encoding_strategy.value}\n"
            script += self.get_encoding_code(plan.encoding_strategy) + "\n\n"
        
        if plan.create_interactions:
            script += "# Interaction features\n"
            script += self.get_interaction_code() + "\n\n"
        
        if plan.create_polynomials:
            script += f"# Polynomial features (degree={plan.polynomial_degree})\n"
            script += self.get_polynomial_code(plan.polynomial_degree) + "\n\n"
        
        if plan.feature_selection:
            script += f"# Feature selection ({plan.selection_method})\n"
            script += self.get_selection_code(plan.selection_method) + "\n\n"
        
        script += """# Save processed data
X_train.to_csv('data/processed/X_train.csv', index=False)
X_test.to_csv('data/processed/X_test.csv', index=False)
y_train.to_csv('data/processed/y_train.csv', index=False)
y_test.to_csv('data/processed/y_test.csv', index=False)

print("Feature engineering complete!")
"""
        
        return script
    
    def get_plan(self, name: str) -> Optional[FeatureEngineering]:
        """Retrieve feature engineering plan"""
        return self.features.get(name)
    
    def list_plans(self) -> List[str]:
        """List all feature engineering plans"""
        return list(self.features.keys())


# Singleton factory
_engineer_instance: Optional[FeatureEngineer] = None


def get_feature_engineer() -> FeatureEngineer:
    """Get FeatureEngineer singleton"""
    global _engineer_instance
    if _engineer_instance is None:
        _engineer_instance = FeatureEngineer()
        logger.info("FeatureEngineer initialized")
    return _engineer_instance
