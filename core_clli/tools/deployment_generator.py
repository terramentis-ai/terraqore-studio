"""
Model Deployment Generator - Phase 5.3 Week 3

Generate deployment configurations for various serving platforms
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DeploymentPlatform(Enum):
    """Deployment platforms"""
    FASTAPI = "fastapi"
    FLASK = "flask"
    STREAMLIT = "streamlit"
    DJANGO = "django"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    AWS_LAMBDA = "aws_lambda"
    HUGGINGFACE_SPACES = "huggingface_spaces"


@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    model_name: str
    platform: DeploymentPlatform
    model_path: str
    port: int = 8000
    workers: int = 4
    timeout: int = 60
    memory_limit: Optional[str] = None
    environment_vars: Dict[str, str] = None
    
    def __post_init__(self):
        if self.environment_vars is None:
            self.environment_vars = {}


class ModelDeploymentGenerator:
    """Generate deployment configurations"""
    
    def __init__(self):
        """Initialize deployment generator"""
        self.deployments: Dict[str, DeploymentConfig] = {}
    
    def get_fastapi_deployment_code(self, model_name: str) -> str:
        """Generate FastAPI deployment code"""
        return f"""
from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
import joblib
import numpy as np
import pandas as pd
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="{model_name}",
    description="ML Model Serving API",
    version="1.0.0"
)

# Load model
MODEL_PATH = 'models/{model_name}/model.joblib'
PREPROCESSOR_PATH = 'models/{model_name}/preprocessor.joblib'

try:
    model = joblib.load(MODEL_PATH)
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    logger.info(f"Model loaded from {{MODEL_PATH}}")
except Exception as e:
    logger.error(f"Failed to load model: {{str(e)}}")
    raise

# Define request/response models
class PredictionRequest(BaseModel):
    features: List[float]
    feature_names: List[str] = None

class PredictionResponse(BaseModel):
    prediction: float
    confidence: float = None
    model_version: str = "1.0"

class BatchPredictionRequest(BaseModel):
    data: List[Dict[str, float]]

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str = "1.0"

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {{
        "status": "healthy",
        "model_loaded": True,
        "version": "1.0"
    }}

# Single prediction endpoint
@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    try:
        # Preprocess
        X = np.array(request.features).reshape(1, -1)
        X_processed = preprocessor.transform(X)
        
        # Predict
        prediction = model.predict(X_processed)[0]
        
        # Get confidence
        try:
            proba = model.predict_proba(X_processed)[0]
            confidence = float(np.max(proba))
        except:
            confidence = None
        
        return {{
            "prediction": float(prediction),
            "confidence": confidence
        }}
    except Exception as e:
        logger.error(f"Prediction error: {{str(e)}}")
        raise HTTPException(status_code=400, detail=str(e))

# Batch prediction endpoint
@app.post("/batch_predict")
async def batch_predict(request: BatchPredictionRequest):
    try:
        df = pd.DataFrame(request.data)
        X_processed = preprocessor.transform(df)
        predictions = model.predict(X_processed)
        
        return {{
            "predictions": predictions.tolist(),
            "count": len(predictions)
        }}
    except Exception as e:
        logger.error(f"Batch prediction error: {{str(e)}}")
        raise HTTPException(status_code=400, detail=str(e))

# Upload and predict
@app.post("/predict_file")
async def predict_file(file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)
        X_processed = preprocessor.transform(df)
        predictions = model.predict(X_processed)
        
        return {{
            "predictions": predictions.tolist(),
            "samples": len(predictions)
        }}
    except Exception as e:
        logger.error(f"File prediction error: {{str(e)}}")
        raise HTTPException(status_code=400, detail=str(e))

# Model info endpoint
@app.get("/model_info")
async def model_info():
    return {{
        "model_name": "{model_name}",
        "version": "1.0",
        "model_type": str(type(model).__name__),
        "input_features": getattr(model, 'n_features_in_', None)
    }}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
    
    def get_flask_deployment_code(self, model_name: str) -> str:
        """Generate Flask deployment code"""
        return f"""
from flask import Flask, request, jsonify
import joblib
import numpy as np
import pandas as pd
import logging
from functools import wraps
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Load model
MODEL_PATH = 'models/{model_name}/model.joblib'
PREPROCESSOR_PATH = 'models/{model_name}/preprocessor.joblib'

try:
    model = joblib.load(MODEL_PATH)
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    logger.info(f"Model loaded from {{MODEL_PATH}}")
except Exception as e:
    logger.error(f"Failed to load model: {{str(e)}}")
    raise

# Rate limiting decorator
def rate_limit(calls=100, period=60):
    def decorator(f):
        last_called = {{}}
        @wraps(f)
        def wrapper(*args, **kwargs):
            now = time.time()
            key = request.remote_addr
            if key not in last_called:
                last_called[key] = []
            last_called[key] = [t for t in last_called[key] if t > now - period]
            if len(last_called[key]) >= calls:
                return {{'error': 'Rate limit exceeded'}}, 429
            last_called[key].append(now)
            return f(*args, **kwargs)
        return wrapper
    return decorator

# Health check
@app.route('/health', methods=['GET'])
def health():
    return jsonify({{
        'status': 'healthy',
        'model_loaded': True,
        'timestamp': time.time()
    }})

# Single prediction
@app.route('/predict', methods=['POST'])
@rate_limit(calls=100, period=60)
def predict():
    try:
        data = request.get_json()
        features = np.array(data['features']).reshape(1, -1)
        X_processed = preprocessor.transform(features)
        prediction = model.predict(X_processed)[0]
        
        try:
            proba = model.predict_proba(X_processed)[0]
            confidence = float(np.max(proba))
        except:
            confidence = None
        
        return jsonify({{
            'prediction': float(prediction),
            'confidence': confidence,
            'status': 'success'
        }})
    except Exception as e:
        logger.error(f"Prediction error: {{str(e)}}")
        return jsonify({{'error': str(e)}}), 400

# Batch prediction
@app.route('/batch_predict', methods=['POST'])
@rate_limit(calls=50, period=60)
def batch_predict():
    try:
        data = request.get_json()
        df = pd.DataFrame(data['data'])
        X_processed = preprocessor.transform(df)
        predictions = model.predict(X_processed)
        
        return jsonify({{
            'predictions': predictions.tolist(),
            'count': len(predictions),
            'status': 'success'
        }})
    except Exception as e:
        logger.error(f"Batch prediction error: {{str(e)}}")
        return jsonify({{'error': str(e)}}), 400

# Model info
@app.route('/model_info', methods=['GET'])
def model_info():
    return jsonify({{
        'model_name': '{model_name}',
        'version': '1.0',
        'model_type': type(model).__name__,
        'input_features': getattr(model, 'n_features_in_', None)
    }})

@app.errorhandler(404)
def not_found(error):
    return jsonify({{'error': 'Endpoint not found'}}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {{str(error)}}")
    return jsonify({{'error': 'Internal server error'}}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
"""
    
    def get_streamlit_deployment_code(self, model_name: str) -> str:
        """Generate Streamlit deployment code"""
        return f"""
import streamlit as st
import joblib
import pandas as pd
import numpy as np
from datetime import datetime

# Page config
st.set_page_config(
    page_title="{model_name}",
    page_icon="🤖",
    layout="wide"
)

st.title(f"🤖 {{st.session_state.get('model_name', '{model_name}')}}")

# Load model (cached)
@st.cache_resource
def load_model():
    model = joblib.load('models/{model_name}/model.joblib')
    preprocessor = joblib.load('models/{model_name}/preprocessor.joblib')
    return model, preprocessor

try:
    model, preprocessor = load_model()
    st.success("✅ Model loaded successfully")
except Exception as e:
    st.error(f"❌ Failed to load model: {{str(e)}}")
    st.stop()

# Sidebar
with st.sidebar:
    st.header("Model Information")
    st.write(f"**Model**: {model_name}")
    st.write(f"**Type**: {{type(model).__name__}}")
    st.write(f"**Loaded at**: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
    
    st.divider()
    
    prediction_mode = st.radio(
        "Prediction Mode",
        ["Single", "Batch", "File Upload"]
    )

# Main content
if prediction_mode == "Single":
    st.header("Single Prediction")
    
    col1, col2 = st.columns(2)
    
    with col1:
        feature1 = st.number_input("Feature 1", value=0.0)
        feature2 = st.number_input("Feature 2", value=0.0)
        feature3 = st.number_input("Feature 3", value=0.0)
    
    with col2:
        feature4 = st.number_input("Feature 4", value=0.0)
        feature5 = st.number_input("Feature 5", value=0.0)
    
    if st.button("🔮 Predict"):
        try:
            X = np.array([[feature1, feature2, feature3, feature4, feature5]])
            X_processed = preprocessor.transform(X)
            prediction = model.predict(X_processed)[0]
            
            try:
                proba = model.predict_proba(X_processed)[0]
                confidence = np.max(proba)
            except:
                confidence = None
            
            st.success(f"Prediction: **{{prediction}}**")
            if confidence:
                st.info(f"Confidence: **{{confidence:.2%}}**")
        except Exception as e:
            st.error(f"Error: {{str(e)}}")

elif prediction_mode == "Batch":
    st.header("Batch Prediction")
    
    csv_input = st.text_area("Paste CSV data (comma-separated):")
    
    if st.button("📊 Predict Batch"):
        try:
            from io import StringIO
            df = pd.read_csv(StringIO(csv_input))
            X_processed = preprocessor.transform(df)
            predictions = model.predict(X_processed)
            
            results_df = df.copy()
            results_df['prediction'] = predictions
            
            st.dataframe(results_df, use_container_width=True)
            
            csv_download = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results",
                data=csv_download,
                file_name="predictions.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"Error: {{str(e)}}")

else:  # File Upload
    st.header("File Upload Prediction")
    
    uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("Preview:")
        st.dataframe(df.head())
        
        if st.button("📥 Predict from File"):
            try:
                X_processed = preprocessor.transform(df)
                predictions = model.predict(X_processed)
                
                results_df = df.copy()
                results_df['prediction'] = predictions
                
                st.dataframe(results_df, use_container_width=True)
                
                csv_download = results_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Results",
                    data=csv_download,
                    file_name="predictions.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"Error: {{str(e)}}")
"""
    
    def get_docker_deployment_code(self, model_name: str) -> str:
        """Generate Dockerfile"""
        return f"""
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy model and code
COPY models/ ./models/
COPY app.py .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["python", "app.py"]
"""
    
    def get_docker_compose_code(self, model_name: str) -> str:
        """Generate docker-compose.yml"""
        return f"""
version: '3.8'

services:
  {model_name}-api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - MODEL_PATH=models/{model_name}/
      - LOG_LEVEL=INFO
      - WORKERS=4
    volumes:
      - ./models:/app/models:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  grafana_data:

networks:
  default:
    name: {model_name}_network
"""
    
    def create_deployment(
        self,
        model_name: str,
        platform: DeploymentPlatform,
        model_path: str,
        port: int = 8000
    ) -> DeploymentConfig:
        """Create deployment configuration"""
        config = DeploymentConfig(
            model_name=model_name,
            platform=platform,
            model_path=model_path,
            port=port
        )
        
        self.deployments[model_name] = config
        
        logger.info(f"Created {platform.value} deployment for {model_name}")
        
        return config
    
    def get_deployment(self, model_name: str) -> Optional[DeploymentConfig]:
        """Get deployment configuration"""
        return self.deployments.get(model_name)


# Singleton factory
_generator_instance: Optional[ModelDeploymentGenerator] = None


def get_deployment_generator() -> ModelDeploymentGenerator:
    """Get ModelDeploymentGenerator singleton"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = ModelDeploymentGenerator()
        logger.info("ModelDeploymentGenerator initialized")
    return _generator_instance
