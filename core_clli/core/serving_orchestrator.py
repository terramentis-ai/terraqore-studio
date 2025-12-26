"""
Model Serving Orchestrator - Phase 5.3 Week 4

Manage model serving, inference endpoints, and production workflows
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class InferenceMode(Enum):
    """Inference modes"""
    BATCH = "batch"
    STREAMING = "streaming"
    REAL_TIME = "real_time"
    ASYNC = "async"


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    RESPONSE_TIME = "response_time"
    RANDOM = "random"


@dataclass
class InferenceConfig:
    """Inference configuration"""
    model_id: str
    model_version: str
    mode: InferenceMode
    batch_size: int = 32
    timeout: int = 60
    max_retries: int = 3
    cache_enabled: bool = True
    cache_ttl: int = 3600  # seconds
    monitoring_enabled: bool = True
    logging_enabled: bool = True


@dataclass
class InferenceRequest:
    """Inference request"""
    request_id: str
    model_id: str
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 0  # 0-10, higher = more important
    timeout: Optional[int] = None


@dataclass
class InferenceResult:
    """Inference result"""
    request_id: str
    model_id: str
    prediction: Any
    confidence: Optional[float] = None
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelEndpoint:
    """Model serving endpoint"""
    endpoint_id: str
    model_id: str
    model_version: str
    url: str
    port: int
    platform: str  # fastapi, flask, streamlit, etc
    created_at: datetime
    active: bool = True
    request_count: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0


class ModelServingOrchestrator:
    """Orchestrate model serving and inference"""
    
    def __init__(self):
        """Initialize orchestrator"""
        self.configs: Dict[str, InferenceConfig] = {}
        self.endpoints: Dict[str, ModelEndpoint] = {}
        self.inference_cache: Dict[str, Any] = {}
        self.request_queue: List[InferenceRequest] = []
        self.results_history: List[InferenceResult] = []
    
    def get_serving_code(self, platform: str) -> str:
        """Generate model serving code"""
        if platform == "fastapi":
            return self.get_fastapi_serving_code()
        elif platform == "flask":
            return self.get_flask_serving_code()
        elif platform == "asyncio":
            return self.get_asyncio_serving_code()
        elif platform == "celery":
            return self.get_celery_serving_code()
        return ""
    
    def get_fastapi_serving_code(self) -> str:
        """Generate FastAPI serving code"""
        return """
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import joblib
import numpy as np
from datetime import datetime
from typing import List, Dict, Any

app = FastAPI()

# Load model
model = joblib.load('models/model.joblib')
preprocessor = joblib.load('models/preprocessor.joblib')

# Request/response models
class PredictionInput(BaseModel):
    features: List[float]

class BatchPredictionInput(BaseModel):
    batch_data: List[Dict[str, float]]

class PredictionOutput(BaseModel):
    prediction: Any
    confidence: float = None
    latency_ms: float

# Metrics tracking
inference_count = 0
total_latency = 0
errors = 0

@app.post("/inference", response_model=PredictionOutput)
async def inference(input_data: PredictionInput):
    global inference_count, total_latency
    import time
    start_time = time.time()
    
    try:
        X = np.array(input_data.features).reshape(1, -1)
        X_processed = preprocessor.transform(X)
        prediction = model.predict(X_processed)[0]
        
        try:
            proba = model.predict_proba(X_processed)[0]
            confidence = float(np.max(proba))
        except:
            confidence = None
        
        latency = (time.time() - start_time) * 1000
        inference_count += 1
        total_latency += latency
        
        return PredictionOutput(
            prediction=float(prediction),
            confidence=confidence,
            latency_ms=latency
        )
    except Exception as e:
        global errors
        errors += 1
        raise

@app.post("/batch_inference")
async def batch_inference(input_data: BatchPredictionInput, background_tasks: BackgroundTasks):
    import time
    start_time = time.time()
    
    try:
        df = pd.DataFrame(input_data.batch_data)
        X_processed = preprocessor.transform(df)
        predictions = model.predict(X_processed)
        
        latency = (time.time() - start_time) * 1000
        
        return {
            'predictions': predictions.tolist(),
            'count': len(predictions),
            'latency_ms': latency
        }
    except Exception as e:
        raise

@app.get("/metrics")
async def metrics():
    return {
        'inference_count': inference_count,
        'avg_latency_ms': total_latency / inference_count if inference_count > 0 else 0,
        'error_count': errors,
        'error_rate': errors / inference_count if inference_count > 0 else 0
    }

@app.get("/health")
async def health():
    return {'status': 'healthy', 'ready': True}
"""
    
    def get_asyncio_serving_code(self) -> str:
        """Generate asyncio serving code"""
        return """
import asyncio
import joblib
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class InferenceRequest:
    request_id: str
    data: List[float]
    timestamp: datetime

class AsyncModelServer:
    def __init__(self, model_path: str):
        self.model = joblib.load(model_path)
        self.request_queue = asyncio.Queue()
        self.results = {}
        self.metrics = {
            'total': 0,
            'errors': 0,
            'latencies': []
        }
    
    async def process_request(self, request: InferenceRequest):
        import time
        start = time.time()
        
        try:
            X = np.array(request.data).reshape(1, -1)
            prediction = self.model.predict(X)[0]
            
            latency = time.time() - start
            self.metrics['latencies'].append(latency * 1000)
            self.metrics['total'] += 1
            
            self.results[request.request_id] = {
                'prediction': float(prediction),
                'latency_ms': latency * 1000
            }
        except Exception as e:
            self.metrics['errors'] += 1
            self.results[request.request_id] = {'error': str(e)}
    
    async def request_handler(self):
        while True:
            request = await self.request_queue.get()
            await self.process_request(request)
            self.request_queue.task_done()
    
    async def infer(self, request_id: str, data: List[float]):
        request = InferenceRequest(
            request_id=request_id,
            data=data,
            timestamp=datetime.now()
        )
        await self.request_queue.put(request)
        
        # Wait for result
        while request_id not in self.results:
            await asyncio.sleep(0.01)
        
        return self.results.pop(request_id)
    
    def get_metrics(self):
        if self.metrics['total'] == 0:
            return {'status': 'no_data'}
        
        return {
            'total_requests': self.metrics['total'],
            'errors': self.metrics['errors'],
            'error_rate': self.metrics['errors'] / self.metrics['total'],
            'avg_latency_ms': np.mean(self.metrics['latencies']),
            'p95_latency_ms': np.percentile(self.metrics['latencies'], 95)
        }

# Usage
async def main():
    server = AsyncModelServer('models/model.joblib')
    
    # Start background handler
    task = asyncio.create_task(server.request_handler())
    
    # Send inference requests
    results = []
    for i in range(100):
        result = await server.infer(f'req_{i}', [1.0, 2.0, 3.0])
        results.append(result)
    
    print(server.get_metrics())
    
    task.cancel()

if __name__ == '__main__':
    asyncio.run(main())
"""
    
    def get_celery_serving_code(self) -> str:
        """Generate Celery async serving code"""
        return """
from celery import Celery, group
import joblib
import numpy as np
from datetime import datetime

# Initialize Celery
app = Celery('model_serving')
app.config_from_object('celery_config')

# Load model
model = joblib.load('models/model.joblib')
preprocessor = joblib.load('models/preprocessor.joblib')

@app.task(name='infer.single')
def infer_single(features: list):
    try:
        X = np.array(features).reshape(1, -1)
        X_processed = preprocessor.transform(X)
        prediction = model.predict(X_processed)[0]
        return {'prediction': float(prediction), 'status': 'success'}
    except Exception as e:
        return {'error': str(e), 'status': 'failed'}

@app.task(name='infer.batch')
def infer_batch(batch_data: list):
    try:
        predictions = []
        for features in batch_data:
            result = infer_single(features)
            predictions.append(result)
        return {'predictions': predictions, 'count': len(predictions)}
    except Exception as e:
        return {'error': str(e)}

@app.task(name='infer.parallel')
def infer_parallel(batch_data: list, num_workers: int = 4):
    '''Parallel inference with Celery'''
    # Create parallel tasks
    job = group(infer_single.s(features) for features in batch_data)
    results = job.apply_async()
    
    # Get results
    return {'predictions': results.get(), 'count': len(results)}

# Monitoring
@app.task
def monitor_performance():
    from celery.app.control import Inspect
    insp = Inspect()
    
    stats = insp.stats()
    active = insp.active()
    
    return {
        'stats': stats,
        'active_tasks': active
    }

# Usage
if __name__ == '__main__':
    # Single inference
    result = infer_single.delay([1.0, 2.0, 3.0])
    print(result.get())
    
    # Batch inference
    batch = [[1.0, 2.0, 3.0], [2.0, 3.0, 4.0], [3.0, 4.0, 5.0]]
    result = infer_batch.delay(batch)
    print(result.get())
    
    # Parallel inference
    result = infer_parallel.delay(batch, num_workers=4)
    print(result.get())
"""
    
    def get_flask_serving_code(self) -> str:
        """Generate Flask serving code"""
        return """
from flask import Flask, request, jsonify
import joblib
import numpy as np
from datetime import datetime
import time

app = Flask(__name__)

# Load model
model = joblib.load('models/model.joblib')
preprocessor = joblib.load('models/preprocessor.joblib')

# Metrics
metrics = {
    'total_requests': 0,
    'successful': 0,
    'failed': 0,
    'total_latency': 0
}

@app.route('/infer', methods=['POST'])
def infer():
    start_time = time.time()
    
    try:
        data = request.json
        features = np.array(data['features']).reshape(1, -1)
        
        X_processed = preprocessor.transform(features)
        prediction = model.predict(X_processed)[0]
        
        try:
            proba = model.predict_proba(X_processed)[0]
            confidence = float(np.max(proba))
        except:
            confidence = None
        
        latency = time.time() - start_time
        
        metrics['total_requests'] += 1
        metrics['successful'] += 1
        metrics['total_latency'] += latency
        
        return jsonify({
            'prediction': float(prediction),
            'confidence': confidence,
            'latency_ms': latency * 1000
        })
    
    except Exception as e:
        metrics['total_requests'] += 1
        metrics['failed'] += 1
        return jsonify({'error': str(e)}), 400

@app.route('/metrics', methods=['GET'])
def get_metrics():
    avg_latency = (metrics['total_latency'] / metrics['successful']) * 1000 if metrics['successful'] > 0 else 0
    
    return jsonify({
        'total_requests': metrics['total_requests'],
        'successful': metrics['successful'],
        'failed': metrics['failed'],
        'error_rate': metrics['failed'] / metrics['total_requests'] if metrics['total_requests'] > 0 else 0,
        'avg_latency_ms': avg_latency
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
"""
    
    def create_inference_config(
        self,
        model_id: str,
        model_version: str,
        mode: InferenceMode
    ) -> InferenceConfig:
        """Create inference configuration"""
        config = InferenceConfig(
            model_id=model_id,
            model_version=model_version,
            mode=mode
        )
        
        self.configs[model_id] = config
        
        logger.info(f"Created inference config for {model_id}")
        
        return config
    
    def register_endpoint(
        self,
        endpoint_id: str,
        model_id: str,
        model_version: str,
        url: str,
        port: int,
        platform: str
    ) -> ModelEndpoint:
        """Register serving endpoint"""
        endpoint = ModelEndpoint(
            endpoint_id=endpoint_id,
            model_id=model_id,
            model_version=model_version,
            url=url,
            port=port,
            platform=platform,
            created_at=datetime.now()
        )
        
        self.endpoints[endpoint_id] = endpoint
        
        logger.info(f"Registered endpoint: {endpoint_id}")
        
        return endpoint
    
    def submit_inference_request(
        self,
        request_id: str,
        model_id: str,
        data: Any,
        priority: int = 0
    ) -> InferenceRequest:
        """Submit inference request"""
        request = InferenceRequest(
            request_id=request_id,
            model_id=model_id,
            data=data,
            priority=priority
        )
        
        self.request_queue.append(request)
        
        return request
    
    def record_result(
        self,
        request_id: str,
        model_id: str,
        prediction: Any,
        latency_ms: float,
        confidence: Optional[float] = None
    ) -> InferenceResult:
        """Record inference result"""
        result = InferenceResult(
            request_id=request_id,
            model_id=model_id,
            prediction=prediction,
            confidence=confidence,
            latency_ms=latency_ms
        )
        
        self.results_history.append(result)
        
        return result
    
    def get_inference_metrics(self) -> Dict[str, Any]:
        """Get inference metrics"""
        if not self.results_history:
            return {'status': 'no_data'}
        
        import statistics
        
        latencies = [r.latency_ms for r in self.results_history]
        
        return {
            'total_inferences': len(self.results_history),
            'avg_latency_ms': statistics.mean(latencies),
            'median_latency_ms': statistics.median(latencies),
            'min_latency_ms': min(latencies),
            'max_latency_ms': max(latencies),
            'stdev_latency_ms': statistics.stdev(latencies) if len(latencies) > 1 else 0
        }


# Singleton factory
_orchestrator_instance: Optional[ModelServingOrchestrator] = None


def get_serving_orchestrator() -> ModelServingOrchestrator:
    """Get ModelServingOrchestrator singleton"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = ModelServingOrchestrator()
        logger.info("ModelServingOrchestrator initialized")
    return _orchestrator_instance
