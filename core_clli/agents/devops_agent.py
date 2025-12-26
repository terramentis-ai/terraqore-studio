"""
DevOpsAgent - Infrastructure & Deployment Automation

Generates infrastructure-as-code, containerization, CI/CD pipelines,
and deployment configurations for multiple cloud providers.
"""

import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class InfrastructureType(Enum):
    """Types of infrastructure to generate"""
    DOCKER = "docker"
    DOCKER_COMPOSE = "docker_compose"
    KUBERNETES = "kubernetes"
    TERRAFORM = "terraform"
    CLOUDFORMATION = "cloudformation"
    ANSIBLE = "ansible"


class CloudProvider(Enum):
    """Supported cloud providers"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ONPREMISE = "onpremise"


class CIPlatform(Enum):
    """Supported CI/CD platforms"""
    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    CIRCLECI = "circleci"
    AZURE_PIPELINES = "azure_pipelines"


class MonitoringStack(Enum):
    """Monitoring & logging stacks"""
    PROMETHEUS_GRAFANA = "prometheus_grafana"
    DATADOG = "datadog"
    ELK_STACK = "elk_stack"
    CLOUDWATCH = "cloudwatch"


@dataclass
class DeploymentTarget:
    """Deployment target configuration"""
    name: str
    infrastructure_type: InfrastructureType
    cloud_provider: CloudProvider
    region: Optional[str] = None
    environment: str = "production"
    replicas: int = 3
    resource_requests: Dict[str, str] = field(default_factory=lambda: {
        "cpu": "500m",
        "memory": "512Mi"
    })
    resource_limits: Dict[str, str] = field(default_factory=lambda: {
        "cpu": "1000m",
        "memory": "1Gi"
    })


@dataclass
class DeploymentConfig:
    """Complete deployment configuration"""
    deployment_id: str
    project_name: str
    targets: List[DeploymentTarget]
    ci_platform: CIPlatform
    monitoring_stack: MonitoringStack
    docker_image: str
    docker_registry: Optional[str] = None
    enable_auto_scaling: bool = True
    enable_monitoring: bool = True
    enable_logging: bool = True
    secrets: Dict[str, str] = field(default_factory=dict)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class DevOpsAgent:
    """
    Infrastructure & Deployment Automation Agent
    
    Generates containerization, orchestration, CI/CD pipelines,
    and infrastructure-as-code for multiple platforms.
    """
    
    def __init__(self):
        """Initialize DevOps Agent"""
        self.deployments: Dict[str, DeploymentConfig] = {}
        self.templates: Dict[str, str] = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load infrastructure templates"""
        self.templates = {
            "docker": self._get_dockerfile_template(),
            "docker_compose": self._get_docker_compose_template(),
            "kubernetes": self._get_k8s_manifest_template(),
            "terraform_aws": self._get_terraform_aws_template(),
            "github_actions": self._get_github_actions_template(),
        }
    
    def create_deployment(
        self,
        project_name: str,
        docker_image: str,
        targets: List[DeploymentTarget],
        ci_platform: CIPlatform,
        monitoring_stack: MonitoringStack,
        docker_registry: Optional[str] = None,
        enable_auto_scaling: bool = True,
        enable_monitoring: bool = True
    ) -> DeploymentConfig:
        """
        Create deployment configuration
        
        Args:
            project_name: Name of project
            docker_image: Docker image name
            targets: List of deployment targets
            ci_platform: CI/CD platform to use
            monitoring_stack: Monitoring solution
            docker_registry: Docker registry URL
            enable_auto_scaling: Enable auto-scaling
            enable_monitoring: Enable monitoring stack
            
        Returns:
            DeploymentConfig with all settings
        """
        deployment_id = f"deploy_{uuid.uuid4().hex[:8]}"
        
        config = DeploymentConfig(
            deployment_id=deployment_id,
            project_name=project_name,
            targets=targets,
            ci_platform=ci_platform,
            monitoring_stack=monitoring_stack,
            docker_image=docker_image,
            docker_registry=docker_registry,
            enable_auto_scaling=enable_auto_scaling,
            enable_monitoring=enable_monitoring
        )
        
        self.deployments[deployment_id] = config
        return config
    
    def get_dockerfile(
        self,
        base_image: str = "python:3.11-slim",
        app_port: int = 8000,
        app_command: str = "python app.py"
    ) -> str:
        """
        Generate Dockerfile
        
        Args:
            base_image: Base Docker image
            app_port: Application port
            app_command: Command to run application
            
        Returns:
            Dockerfile content
        """
        dockerfile = f"""FROM {base_image}

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE {app_port}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{app_port}/health || exit 1

# Run application
CMD [{app_command!r}]
"""
        return dockerfile
    
    def get_docker_compose(
        self,
        services: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Generate docker-compose.yml
        
        Args:
            services: Dictionary of services with configurations
            
        Returns:
            docker-compose.yml content
        """
        compose = """version: '3.8'

services:
"""
        for service_name, service_config in services.items():
            compose += f"""
  {service_name}:
    image: {service_config.get('image', 'python:3.11')}
    ports:
      - "{service_config.get('port', '8000')}:8000"
    environment:
"""
            for env_key, env_val in service_config.get('environment', {}).items():
                compose += f"      - {env_key}={env_val}\n"
            
            compose += f"""    volumes:
      - {service_config.get('volume_path', '.')}:/app
    command: {service_config.get('command', 'python app.py')}
    networks:
      - app_network
"""
        
        compose += """
networks:
  app_network:
    driver: bridge
"""
        return compose
    
    def get_kubernetes_manifest(
        self,
        deployment_id: str,
        namespace: str = "default"
    ) -> str:
        """
        Generate Kubernetes manifest
        
        Args:
            deployment_id: Deployment ID
            namespace: Kubernetes namespace
            
        Returns:
            Kubernetes YAML manifest
        """
        if deployment_id not in self.deployments:
            return ""
        
        config = self.deployments[deployment_id]
        primary_target = config.targets[0]
        
        manifest = f"""apiVersion: v1
kind: Namespace
metadata:
  name: {namespace}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {config.project_name}-deployment
  namespace: {namespace}
  labels:
    app: {config.project_name}
spec:
  replicas: {primary_target.replicas}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: {config.project_name}
  template:
    metadata:
      labels:
        app: {config.project_name}
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
    spec:
      serviceAccountName: {config.project_name}-sa
      containers:
      - name: app
        image: {config.docker_image}
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
        resources:
          requests:
            cpu: {primary_target.resource_requests['cpu']}
            memory: {primary_target.resource_requests['memory']}
          limits:
            cpu: {primary_target.resource_limits['cpu']}
            memory: {primary_target.resource_limits['memory']}
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        env:
"""
        for key, value in config.environment_vars.items():
            manifest += f"""        - name: {key}
          value: "{value}"
"""
        
        manifest += f"""---
apiVersion: v1
kind: Service
metadata:
  name: {config.project_name}-service
  namespace: {namespace}
spec:
  type: LoadBalancer
  selector:
    app: {config.project_name}
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
    name: http
"""
        
        if config.enable_auto_scaling:
            manifest += f"""---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {config.project_name}-hpa
  namespace: {namespace}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {config.project_name}-deployment
  minReplicas: {primary_target.replicas}
  maxReplicas: {primary_target.replicas * 3}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
"""
        
        manifest += f"""---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {config.project_name}-sa
  namespace: {namespace}
"""
        return manifest
    
    def get_terraform_aws(
        self,
        deployment_id: str,
        region: str = "us-east-1"
    ) -> str:
        """
        Generate Terraform code for AWS
        
        Args:
            deployment_id: Deployment ID
            region: AWS region
            
        Returns:
            Terraform HCL code
        """
        if deployment_id not in self.deployments:
            return ""
        
        config = self.deployments[deployment_id]
        
        terraform = f"""terraform {{
  required_version = ">= 1.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = "{region}"
}}

# ECR Repository
resource "aws_ecr_repository" "{config.project_name}_repo" {{
  name                 = "{config.project_name.lower()}"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {{
    scan_on_push = true
  }}
  
  tags = {{
    Name        = "{config.project_name}"
    Environment = "production"
    ManagedBy   = "Terraform"
  }}
}}

# ECS Cluster
resource "aws_ecs_cluster" "{config.project_name}_cluster" {{
  name = "{config.project_name}-cluster"
  
  setting {{
    name  = "containerInsights"
    value = "enabled"
  }}
  
  tags = {{
    Name        = "{config.project_name}"
    Environment = "production"
  }}
}}

# ECS Task Definition
resource "aws_ecs_task_definition" "{config.project_name}_task" {{
  family                   = "{config.project_name}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  
  container_definitions = jsonencode([{{
    name      = "{config.project_name}"
    image     = "{config.docker_image}"
    essential = true
    portMappings = [{{
      containerPort = 8000
      hostPort      = 8000
      protocol      = "tcp"
    }}]
    logConfiguration = {{
      logDriver = "awslogs"
      options = {{
        awslogs-group         = aws_cloudwatch_log_group.ecs_logs.name
        awslogs-region        = "{region}"
        awslogs-stream-prefix = "ecs"
      }}
    }}
    environment = [
"""
        
        for key, value in config.environment_vars.items():
            terraform += f"""      {{
        name  = "{key}"
        value = "{value}"
      }},
"""
        
        terraform += f"""    ]
  }}])
  
  tags = {{
    Name        = "{config.project_name}"
    Environment = "production"
  }}
}}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs_logs" {{
  name              = "/ecs/{config.project_name}"
  retention_in_days = 30
  
  tags = {{
    Name = "{config.project_name}"
  }}
}}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_task_execution_role" {{
  name = "{config.project_name}-ecs-task-execution-role"
  
  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [{{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {{
        Service = "ecs-tasks.amazonaws.com"
      }}
    }}]
  }})
}}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {{
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}}

# ALB for load balancing
resource "aws_lb" "{config.project_name}_alb" {{
  name               = "{config.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  
  enable_deletion_protection = false
  enable_http2              = true
  enable_cross_zone_load_balancing = true
  
  tags = {{
    Name = "{config.project_name}"
  }}
}}

# Output
output "ecr_repository_url" {{
  value = aws_ecr_repository.{config.project_name}_repo.repository_url
}}

output "alb_dns_name" {{
  value = aws_lb.{config.project_name}_alb.dns_name
}}
"""
        return terraform
    
    def get_github_actions_workflow(
        self,
        deployment_id: str
    ) -> str:
        """
        Generate GitHub Actions workflow
        
        Args:
            deployment_id: Deployment ID
            
        Returns:
            GitHub Actions YAML workflow
        """
        if deployment_id not in self.deployments:
            return ""
        
        config = self.deployments[deployment_id]
        
        workflow = f"""name: Deploy {config.project_name}

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{{{ github.repository }}}}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt
      
      - name: Run linting
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
      
      - name: Run tests
        run: pytest tests/ --cov --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{{{ env.REGISTRY }}}}
          username: ${{{{ github.actor }}}}
          password: ${{{{ secrets.GITHUB_TOKEN }}}}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{{{version}}}}
            type=semver,pattern={{{{major}}}}.{{{{minor}}}}
            type=sha
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: ${{{{ github.event_name != 'pull_request' }}}}
          tags: ${{{{ steps.meta.outputs.tags }}}}
          labels: ${{{{ steps.meta.outputs.labels }}}}
          cache-from: type=registry,ref=${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:buildcache
          cache-to: type=registry,ref=${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:buildcache,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Kubernetes
        env:
          KUBE_CONFIG: ${{{{ secrets.KUBE_CONFIG }}}}
          NAMESPACE: production
        run: |
          mkdir -p ~/.kube
          echo "$KUBE_CONFIG" | base64 -d > ~/.kube/config
          
          kubectl apply -f kubernetes/
          kubectl rollout status deployment/{config.project_name}-deployment -n ${{{{ env.NAMESPACE }}}} --timeout=5m
"""
        return workflow
    
    def get_deployment_guide(
        self,
        deployment_id: str
    ) -> str:
        """
        Generate deployment guide
        
        Args:
            deployment_id: Deployment ID
            
        Returns:
            Deployment guide content
        """
        if deployment_id not in self.deployments:
            return ""
        
        config = self.deployments[deployment_id]
        
        guide = f"""# {config.project_name} - Deployment Guide

## Overview
This guide covers deployment of {config.project_name} across multiple environments.

## Prerequisites
- Docker installed (version 20.10+)
- kubectl installed (for Kubernetes deployments)
- Terraform installed (for IaC deployments)
- Cloud provider credentials configured

## Quick Start

### 1. Build Docker Image
```bash
docker build -t {config.docker_image}:latest .
docker tag {config.docker_image}:latest {config.docker_image}:${{VERSION}}
```

### 2. Push to Registry
```bash
docker push {config.docker_image}:${{VERSION}}
```

### 3. Deploy to Kubernetes
```bash
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml

# Verify deployment
kubectl get pods -n default
kubectl logs -f deployment/{config.project_name}-deployment
```

### 4. Deploy with Terraform
```bash
cd terraform/
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

## Environment Variables
- `APP_ENV`: Application environment (development, staging, production)
- `LOG_LEVEL`: Logging level (debug, info, warning, error)
- `WORKERS`: Number of worker processes

## Scaling

### Manual Scaling
```bash
kubectl scale deployment/{config.project_name}-deployment --replicas=5
```

### Auto-scaling
Configuration is automatically set up in Kubernetes manifests with HPA.

## Monitoring

### Prometheus Metrics
Metrics are exposed at `/metrics` endpoint in Prometheus format.

### View Logs
```bash
kubectl logs -f deployment/{config.project_name}-deployment -n default --tail=100
```

## Rollback

### Kubernetes Rollback
```bash
kubectl rollout history deployment/{config.project_name}-deployment
kubectl rollout undo deployment/{config.project_name}-deployment --to-revision=<N>
```

### Terraform Rollback
```bash
terraform plan -out=tfplan
terraform apply tfplan
```

## Troubleshooting

### Pod CrashLoopBackOff
```bash
kubectl describe pod <pod-name> -n default
kubectl logs <pod-name> -n default
```

### Service Not Accessible
```bash
kubectl get svc
kubectl get endpoints
```

## Security

- All secrets stored in cloud provider secret manager
- RBAC enabled for Kubernetes access
- Network policies enforced
- Regular security updates applied

## Support
For issues, check logs and contact ops team.
"""
        return guide
    
    def _get_dockerfile_template(self) -> str:
        """Get Dockerfile template"""
        return self.get_dockerfile()
    
    def _get_docker_compose_template(self) -> str:
        """Get docker-compose template"""
        return self.get_docker_compose({"app": {"image": "python:3.11"}})
    
    def _get_k8s_manifest_template(self) -> str:
        """Get Kubernetes manifest template"""
        return "# Kubernetes manifest template"
    
    def _get_terraform_aws_template(self) -> str:
        """Get Terraform AWS template"""
        return "# Terraform AWS template"
    
    def _get_github_actions_template(self) -> str:
        """Get GitHub Actions template"""
        return "# GitHub Actions template"


# Singleton instance
_devops_agent = None

def get_devops_agent() -> DevOpsAgent:
    """Get DevOps Agent singleton"""
    global _devops_agent
    if _devops_agent is None:
        _devops_agent = DevOpsAgent()
    return _devops_agent
