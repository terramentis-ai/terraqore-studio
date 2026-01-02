"""
Test script for specialized agents: DSAgent, MLOAgent, DOAgent
Tests ML, MLOps, and DevOps workflow capabilities.
"""

import sys
import time
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add core_cli to path
sys.path.insert(0, str(Path(__file__).parent / "core_cli"))

from agents.ds_agent import DSAgent
from agents.mlo_agent import MLOAgent
from agents.do_agent import DOAgent
from agents.base import AgentContext
from core.llm_client import create_llm_client_from_config
from core.config import ConfigManager

def print_section(title):
    print("\n" + "=" * 70)
    print(title.center(70))
    print("=" * 70)

def print_subsection(title):
    print("\n" + "-" * 70)
    print(title)
    print("-" * 70)

def test_ds_agent(llm_client):
    """Test Data Science Agent with ML project."""
    print_section("TEST 1: DATA SCIENCE AGENT (DSAgent)")
    
    agent = DSAgent(llm_client=llm_client)
    
    print("\n📊 Project: Sentiment Analysis for Customer Reviews")
    print("   Task: Design ML architecture and pipeline")
    
    context = AgentContext(
        project_id=100,
        project_name="Customer Sentiment Analysis",
        project_description="ML system to analyze customer reviews and predict sentiment (positive/negative/neutral)",
        user_input="""Design a machine learning architecture for sentiment analysis on customer reviews.
        
Requirements:
- Handle text preprocessing and feature extraction
- Support multiple ML models (traditional ML + deep learning)
- Scale to 100K+ reviews
- Provide confidence scores
- Real-time prediction API

Dataset: Customer reviews (text), ratings (1-5 stars)
Deployment: Cloud-based API (AWS/GCP)
Performance: <200ms prediction latency""",
        metadata={
            "domain": "NLP",
            "task_type": "classification",
            "data_type": "text",
            "scale": "medium"
        }
    )
    
    print("\n🔍 Running DSAgent...")
    start = time.time()
    result = agent.execute(context)
    elapsed = time.time() - start
    
    print(f"\n✅ Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"⏱️  Execution Time: {elapsed:.2f}s")
    
    if result.output:
        print(f"\n📋 Architecture Plan:\n")
        # Show first 1000 chars
        output_preview = result.output[:1500] + ("..." if len(result.output) > 1500 else "")
        print(output_preview)
    
    if result.metadata:
        print(f"\n📈 Recommendations:")
        recommendations = result.metadata.get('recommendations', [])
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"   {i}. {rec}")
    
    return result.success

def test_mlo_agent(llm_client):
    """Test MLOps Agent with model deployment project."""
    print_section("TEST 2: MLOPS AGENT (MLOAgent)")
    
    agent = MLOAgent(llm_client=llm_client)
    
    print("\n🚀 Project: Deploy Fraud Detection Model")
    print("   Task: Design MLOps pipeline for production deployment")
    
    context = AgentContext(
        project_id=101,
        project_name="Fraud Detection MLOps",
        project_description="Deploy and monitor fraud detection model in production with CI/CD, monitoring, and retraining",
        user_input="""Design MLOps infrastructure for fraud detection model deployment.

Current State:
- Trained XGBoost model (accuracy: 94%)
- Model file: fraud_model.pkl (50MB)
- Features: 25 transaction features
- Inference: Real-time scoring required

Requirements:
- Automated model deployment pipeline
- A/B testing capability for model versions
- Real-time monitoring (latency, drift, performance)
- Automated retraining when drift detected
- Model versioning and rollback
- Scale: 10K predictions/second

Infrastructure: Kubernetes cluster, MLflow for tracking
Cloud: AWS (SageMaker optional)""",
        metadata={
            "model_type": "XGBoost",
            "deployment_type": "real-time",
            "scale": "high_throughput",
            "monitoring": "required"
        }
    )
    
    print("\n🔍 Running MLOAgent...")
    start = time.time()
    result = agent.execute(context)
    elapsed = time.time() - start
    
    print(f"\n✅ Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"⏱️  Execution Time: {elapsed:.2f}s")
    
    if result.output:
        print(f"\n📋 MLOps Strategy:\n")
        output_preview = result.output[:1500] + ("..." if len(result.output) > 1500 else "")
        print(output_preview)
    
    if result.metadata:
        print(f"\n🛠️  Key Components:")
        components = result.metadata.get('components', [])
        for comp in components[:5]:
            print(f"   • {comp}")
    
    return result.success

def test_do_agent(llm_client):
    """Test DevOps Agent with infrastructure project."""
    print_section("TEST 3: DEVOPS AGENT (DOAgent)")
    
    agent = DOAgent(llm_client=llm_client)
    
    print("\n🏗️  Project: Microservices Infrastructure")
    print("   Task: Design IaC and CI/CD for microservices platform")
    
    context = AgentContext(
        project_id=102,
        project_name="E-commerce Microservices Platform",
        project_description="Infrastructure-as-Code for scalable microservices architecture with automated CI/CD",
        user_input="""Design infrastructure and CI/CD pipeline for e-commerce microservices platform.

Architecture:
- 8 microservices (user, product, cart, order, payment, inventory, notification, analytics)
- API Gateway (Kong or similar)
- Service mesh for inter-service communication
- PostgreSQL (user, product, order), Redis (cache, session), MongoDB (analytics)

Requirements:
- Infrastructure as Code (Terraform preferred)
- Kubernetes cluster setup (EKS or GKE)
- Auto-scaling based on load
- Blue-green deployments
- CI/CD pipeline (GitHub Actions or GitLab CI)
- Monitoring stack (Prometheus + Grafana)
- Logging aggregation (ELK stack)
- Secret management (Vault or AWS Secrets Manager)

Scale: 
- 50K concurrent users
- 1000 requests/second peak
- Multi-region (US-East, EU-West, APAC-SG)

Cloud: AWS (primary), multi-cloud optional""",
        metadata={
            "infrastructure_type": "microservices",
            "orchestration": "kubernetes",
            "cloud_provider": "aws",
            "scale": "high_availability"
        }
    )
    
    print("\n🔍 Running DOAgent...")
    start = time.time()
    result = agent.execute(context)
    elapsed = time.time() - start
    
    print(f"\n✅ Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"⏱️  Execution Time: {elapsed:.2f}s")
    
    if result.output:
        print(f"\n📋 Infrastructure Plan:\n")
        output_preview = result.output[:1500] + ("..." if len(result.output) > 1500 else "")
        print(output_preview)
    
    if result.metadata:
        print(f"\n🔧 Infrastructure Components:")
        components = result.metadata.get('infrastructure_components', [])
        for comp in components[:5]:
            print(f"   • {comp}")
    
    return result.success

def main():
    print("=" * 70)
    print("SPECIALIZED AGENTS TEST SUITE".center(70))
    print("Testing: DSAgent, MLOAgent, DOAgent".center(70))
    print("=" * 70)
    
    # Load configuration
    config_mgr = ConfigManager()
    config = config_mgr.load()
    
    # Initialize LLM client
    print("\n⚙️  Initializing LLM client...")
    llm_client = create_llm_client_from_config(config)
    print("✅ LLM client ready")
    
    # Track results
    results = {
        "DSAgent": False,
        "MLOAgent": False,
        "DOAgent": False
    }
    
    # Test each agent
    try:
        results["DSAgent"] = test_ds_agent(llm_client)
    except Exception as e:
        print(f"\n❌ DSAgent failed: {str(e)}")
    
    time.sleep(1)  # Brief pause between tests
    
    try:
        results["MLOAgent"] = test_mlo_agent(llm_client)
    except Exception as e:
        print(f"\n❌ MLOAgent failed: {str(e)}")
    
    time.sleep(1)
    
    try:
        results["DOAgent"] = test_do_agent(llm_client)
    except Exception as e:
        print(f"\n❌ DOAgent failed: {str(e)}")
    
    # Final summary
    print_section("TEST SUMMARY")
    
    print("\n📊 Results:")
    for agent_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {agent_name}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL SPECIALIZED AGENTS OPERATIONAL!")
    elif passed > 0:
        print(f"\n⚠️  {total - passed} agent(s) need attention")
    else:
        print("\n❌ All agents failed - check configuration")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE".center(70))
    print("=" * 70)

if __name__ == "__main__":
    main()
