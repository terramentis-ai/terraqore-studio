#!/usr/bin/env python3
"""
MLOps Agent Test Suite
Tests the newly implemented MLOps agent functionality
"""

import sys
from datetime import datetime

# Add appshell to path
sys.path.insert(0, '.')

from agents.mlops_agent import (
    MLOpsAgent, ModelMetadata, ExperimentTracking, DeploymentConfig,
    DeploymentEnvironment, ModelStrategy, MonitoringMetricType, ExperimentStatus
)

def test_mlops_agent_initialization():
    """Test 1: MLOps Agent Initialization"""
    print('TEST 1: MLOps Agent - Initialization')
    mlops = MLOpsAgent()
    assert mlops.name == "MLOpsAgent"
    assert len(mlops.capabilities) > 0
    print(f'  ✅ Agent initialized: {mlops.name}')
    print(f'  ✅ Capabilities loaded: {len(mlops.capabilities)} features')
    print()
    return mlops

def test_model_registration(mlops):
    """Test 2: Model Registry - Registration"""
    print('TEST 2: Model Registry - Registration')
    
    metadata = ModelMetadata(
        model_name="test_model",
        version="1.0.0",
        framework="pytorch",
        input_schema={"feature1": "float32", "feature2": "float32"},
        output_schema={"prediction": "float32"},
        created_by="test_user",
        description="Test model for MLOps agent",
        tags=["test", "prototype"],
        hyperparameters={"layers": 3, "units": 128},
        performance_metrics={"accuracy": 0.95, "auc": 0.92}
    )
    
    registry = mlops.register_model(metadata, description="Test model registration")
    assert registry.model_id is not None
    assert registry.model_name == "test_model"
    assert registry.current_version == "1.0.0"
    
    print(f'  ✅ Model registered: {registry.model_id}')
    print(f'  ✅ Version: {registry.current_version}')
    print(f'  ✅ Model registry entries: {len(mlops.models_registry)}')
    print()
    return registry.model_id

def test_experiment_tracking(mlops):
    """Test 3: Experiment Tracking - Start and Log"""
    print('TEST 3: Experiment Tracking - Start and Log')
    
    experiment = mlops.start_experiment(
        experiment_name="test_experiment",
        project_id="test_project",
        parameters={"learning_rate": 0.001, "batch_size": 32},
        tags=["test", "prototype"]
    )
    
    assert experiment.experiment_id is not None
    assert experiment.status == ExperimentStatus.RUNNING
    
    print(f'  ✅ Experiment started: {experiment.experiment_id}')
    print(f'  ✅ Status: {experiment.status.value}')
    
    # Log metrics
    metrics = {"loss": 0.05, "accuracy": 0.95, "val_accuracy": 0.93}
    success = mlops.log_experiment_metrics(experiment.experiment_id, metrics)
    assert success is True
    
    print(f'  ✅ Metrics logged successfully')
    print(f'  ✅ Metrics: {metrics}')
    
    # End experiment
    mlops.end_experiment(experiment.experiment_id, ExperimentStatus.COMPLETED)
    exp_summary = mlops.get_experiment_summary(experiment.experiment_id)
    assert exp_summary['status'] == 'completed'
    assert exp_summary['duration_seconds'] > 0
    
    print(f'  ✅ Experiment completed')
    print(f'  ✅ Duration: {exp_summary["duration_seconds"]:.2f} seconds')
    print(f'  ✅ Total experiments: {len(mlops.experiments)}')
    print()
    return experiment.experiment_id

def test_deployment_creation(mlops, model_id):
    """Test 4: Deployment Management - Create Deployment"""
    print('TEST 4: Deployment Management - Create Deployment')
    
    deployment = mlops.create_deployment(
        model_id=model_id,
        version="1.0.0",
        environment=DeploymentEnvironment.STAGING,
        serving_strategy=ModelStrategy.DIRECT_SERVING,
        replicas=3
    )
    
    assert deployment.model_id == model_id
    assert deployment.environment == DeploymentEnvironment.STAGING
    assert deployment.replicas == 3
    
    print(f'  ✅ Deployment created for model: {model_id}')
    print(f'  ✅ Environment: {deployment.environment.value}')
    print(f'  ✅ Replicas: {deployment.replicas}')
    print(f'  ✅ Serving strategy: {deployment.serving_strategy.value}')
    print(f'  ✅ Total deployments: {len(mlops.deployments)}')
    print()

def test_monitoring_configuration(mlops, model_id):
    """Test 5: Monitoring Configuration"""
    print('TEST 5: Monitoring Configuration')
    
    monitoring = mlops.configure_monitoring(
        model_id=model_id,
        version="1.0.0",
        metrics=[
            MonitoringMetricType.MODEL_PERFORMANCE,
            MonitoringMetricType.DATA_DRIFT,
            MonitoringMetricType.LATENCY
        ],
        alert_thresholds={
            "accuracy_drop": 0.05,
            "latency_threshold": 1000.0
        }
    )
    
    assert monitoring.model_id == model_id
    assert len(monitoring.metrics_to_track) == 3
    assert monitoring.alert_thresholds["accuracy_drop"] == 0.05
    
    print(f'  ✅ Monitoring configured for: {model_id}')
    print(f'  ✅ Metrics tracked: {len(monitoring.metrics_to_track)}')
    print(f'  ✅ Alert thresholds: {len(monitoring.alert_thresholds)}')
    print(f'  ✅ Total monitoring configs: {len(mlops.monitoring_configs)}')
    print()

def test_model_promotion(mlops, model_id):
    """Test 6: Model Promotion - Staging to Production"""
    print('TEST 6: Model Promotion - Staging to Production')
    
    success = mlops.promote_model(
        model_id=model_id,
        version="1.0.0",
        target_environment=DeploymentEnvironment.PRODUCTION,
        approval_status="approved"
    )
    
    assert success is True
    
    model_info = mlops.get_model_info(model_id)
    assert model_info['production_version'] == "1.0.0"
    
    print(f'  ✅ Model promoted to production')
    print(f'  ✅ Model ID: {model_id}')
    print(f'  ✅ Production version: {model_info["production_version"]}')
    print()

def test_batch_prediction_job(mlops, model_id):
    """Test 7: Batch Prediction Job Submission"""
    print('TEST 7: Batch Prediction Job Submission')
    
    job = mlops.submit_batch_job(
        model_id=model_id,
        model_version="1.0.0",
        input_path="s3://bucket/input/data.parquet",
        output_path="s3://bucket/output/predictions.parquet",
        batch_size=5000
    )
    
    assert job.job_id is not None
    assert job.model_id == model_id
    assert job.job_status == "pending"
    
    print(f'  ✅ Batch job submitted: {job.job_id}')
    print(f'  ✅ Job status: {job.job_status}')
    print(f'  ✅ Batch size: {job.batch_size}')
    print(f'  ✅ Total batch jobs: {len(mlops.batch_jobs)}')
    print()

def test_model_rollback(mlops, model_id):
    """Test 8: Model Rollback"""
    print('TEST 8: Model Rollback')
    
    success = mlops.rollback_model(
        model_id=model_id,
        environment=DeploymentEnvironment.PRODUCTION,
        previous_version="0.9.0"
    )
    
    assert success is True
    
    model_info = mlops.get_model_info(model_id)
    assert model_info['production_version'] == "0.9.0"
    
    print(f'  ✅ Model rolled back successfully')
    print(f'  ✅ Rollback to version: 0.9.0')
    print(f'  ✅ Environment: production')
    print()

def test_execute_operations(mlops):
    """Test 9: Execute Method - Operations Dispatcher"""
    print('TEST 9: Execute Method - Operations Dispatcher')
    
    # Test start_experiment operation
    context = {
        "operation": "start_experiment",
        "experiment_name": "test_exp",
        "project_id": "test_project",
        "parameters": {"lr": 0.001}
    }
    
    result = mlops.execute(context)
    assert result["status"] == "success"
    assert result["operation"] == "start_experiment"
    
    print(f'  ✅ Execute method working')
    print(f'  ✅ Operation: {result["operation"]}')
    print(f'  ✅ Status: {result["status"]}')
    print(f'  ✅ Experiment created: {result["data"].get("experiment_id")}')
    print()

def main():
    print("=" * 70)
    print("MLOps AGENT TEST SUITE")
    print("=" * 70)
    print()
    
    try:
        # Run all tests
        mlops = test_mlops_agent_initialization()
        model_id = test_model_registration(mlops)
        experiment_id = test_experiment_tracking(mlops)
        test_deployment_creation(mlops, model_id)
        test_monitoring_configuration(mlops, model_id)
        test_model_promotion(mlops, model_id)
        test_batch_prediction_job(mlops, model_id)
        test_model_rollback(mlops, model_id)
        test_execute_operations(mlops)
        
        # Print summary
        print("=" * 70)
        print("✅ ALL MLOps AGENT TESTS PASSED")
        print("=" * 70)
        print()
        print("SUMMARY:")
        print(f"  • Agent initialized: ✅ Operational")
        print(f"  • Model registry: ✅ {len(mlops.models_registry)} models")
        print(f"  • Experiments: ✅ {len(mlops.experiments)} tracked")
        print(f"  • Deployments: ✅ {len(mlops.deployments)} configured")
        print(f"  • Monitoring: ✅ {len(mlops.monitoring_configs)} configs")
        print(f"  • Batch jobs: ✅ {len(mlops.batch_jobs)} submitted")
        print()
        print("MLOps Agent is ready for production use!")
        print()
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
