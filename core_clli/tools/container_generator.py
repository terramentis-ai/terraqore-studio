"""
ContainerGenerator - Multi-framework Docker & Container Orchestration Code Generation

Generates Dockerfiles, docker-compose configurations, and container optimization
strategies for various application frameworks and architectures.
"""

import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import uuid


class Framework(Enum):
    """Supported application frameworks"""
    FASTAPI = "fastapi"
    FLASK = "flask"
    DJANGO = "django"
    NODEJS = "nodejs"
    JAVA_SPRING = "java_spring"
    RUST_ACTIX = "rust_actix"
    GO_GIN = "go_gin"
    PYTHON_GENERAL = "python_general"


class DockerBaseImage(Enum):
    """Docker base images"""
    PYTHON_311_SLIM = "python:3.11-slim"
    PYTHON_311_FULL = "python:3.11"
    PYTHON_310_SLIM = "python:3.10-slim"
    NODEJS_20_SLIM = "node:20-slim"
    NODEJS_20_FULL = "node:20"
    JAVA_21 = "eclipse-temurin:21-jre-slim"
    RUST_1_75 = "rust:1.75-slim"
    GO_1_21 = "golang:1.21-alpine"
    UBUNTU_22 = "ubuntu:22.04"
    ALPINE_3 = "alpine:3.19"


class OptimizationStrategy(Enum):
    """Container optimization strategies"""
    MULTI_STAGE = "multi_stage"
    LAYER_CACHING = "layer_caching"
    MINIMAL_SIZE = "minimal_size"
    SECURITY_HARDENED = "security_hardened"
    DEVELOPMENT = "development"
    PRODUCTION = "production"


@dataclass
class ContainerConfig:
    """Container configuration"""
    container_id: str
    framework: Framework
    base_image: DockerBaseImage
    app_port: int = 8000
    workers: int = 4
    environment: str = "production"
    enable_health_check: bool = True
    enable_metrics: bool = True
    optimization_strategy: OptimizationStrategy = OptimizationStrategy.PRODUCTION
    registry: Optional[str] = None
    image_name: Optional[str] = None
    image_tag: str = "latest"
    dependencies: List[str] = field(default_factory=list)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    volumes: Dict[str, str] = field(default_factory=dict)
    exposed_ports: List[int] = field(default_factory=lambda: [8000])
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ContainerGenerator:
    """
    Container Code Generator
    
    Generates optimized Dockerfiles and container configurations
    for multiple frameworks and deployment strategies.
    """
    
    def __init__(self):
        """Initialize Container Generator"""
        self.configs: Dict[str, ContainerConfig] = {}
    
    def create_config(
        self,
        framework: Framework,
        base_image: DockerBaseImage,
        app_port: int = 8000,
        workers: int = 4,
        environment: str = "production",
        optimization_strategy: OptimizationStrategy = OptimizationStrategy.PRODUCTION
    ) -> ContainerConfig:
        """
        Create container configuration
        
        Args:
            framework: Application framework
            base_image: Docker base image
            app_port: Application port
            workers: Number of worker processes
            environment: Deployment environment
            optimization_strategy: Optimization strategy
            
        Returns:
            ContainerConfig
        """
        container_id = f"container_{uuid.uuid4().hex[:8]}"
        
        config = ContainerConfig(
            container_id=container_id,
            framework=framework,
            base_image=base_image,
            app_port=app_port,
            workers=workers,
            environment=environment,
            optimization_strategy=optimization_strategy
        )
        
        self.configs[container_id] = config
        return config
    
    def get_dockerfile_fastapi(
        self,
        optimization_strategy: OptimizationStrategy = OptimizationStrategy.PRODUCTION,
        app_port: int = 8000,
        workers: int = 4
    ) -> str:
        """
        Generate Dockerfile for FastAPI application
        
        Args:
            optimization_strategy: Optimization strategy
            app_port: Application port
            workers: Number of workers
            
        Returns:
            Dockerfile content
        """
        if optimization_strategy == OptimizationStrategy.MULTI_STAGE:
            return f"""# Multi-stage build for FastAPI
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH \\
    PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE {app_port}

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{app_port}/health || exit 1

CMD ["gunicorn", "--workers", "{workers}", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:{app_port}", "main:app"]
"""
        
        elif optimization_strategy == OptimizationStrategy.MINIMAL_SIZE:
            return f"""# Minimal size FastAPI Dockerfile
FROM python:3.11-alpine

WORKDIR /app

RUN apk add --no-cache curl gcc musl-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {app_port}

HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:{app_port}/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{app_port}"]
"""
        
        elif optimization_strategy == OptimizationStrategy.SECURITY_HARDENED:
            return f"""# Security-hardened FastAPI Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl \\
    ca-certificates \\
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --no-deps -r requirements.txt

COPY . .

# Set permissions
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE {app_port}

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{app_port}/health || exit 1

CMD ["gunicorn", "--workers", "{workers}", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:{app_port}", "--access-logfile", "-", "--error-logfile", "-", "main:app"]
"""
        
        else:  # PRODUCTION or DEVELOPMENT
            return f"""# Production FastAPI Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {app_port}

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{app_port}/health || exit 1

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

CMD ["gunicorn", "--workers", "{workers}", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:{app_port}", "main:app"]
"""
    
    def get_dockerfile_flask(
        self,
        optimization_strategy: OptimizationStrategy = OptimizationStrategy.PRODUCTION,
        app_port: int = 8000,
        workers: int = 4
    ) -> str:
        """
        Generate Dockerfile for Flask application
        
        Args:
            optimization_strategy: Optimization strategy
            app_port: Application port
            workers: Number of workers
            
        Returns:
            Dockerfile content
        """
        if optimization_strategy == OptimizationStrategy.MULTI_STAGE:
            return f"""# Multi-stage Flask Dockerfile
FROM python:3.11-slim as builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH \\
    FLASK_APP=app.py \\
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE {app_port}

HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:{app_port}/health || exit 1

CMD ["gunicorn", "--workers", "{workers}", "--bind", "0.0.0.0:{app_port}", "app:app"]
"""
        
        else:
            return f"""# Flask Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {app_port}

HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:{app_port}/health || exit 1

ENV FLASK_APP=app.py PYTHONUNBUFFERED=1

CMD ["gunicorn", "--workers", "{workers}", "--bind", "0.0.0.0:{app_port}", "app:app"]
"""
    
    def get_dockerfile_django(
        self,
        optimization_strategy: OptimizationStrategy = OptimizationStrategy.PRODUCTION,
        app_port: int = 8000,
        workers: int = 4
    ) -> str:
        """
        Generate Dockerfile for Django application
        
        Args:
            optimization_strategy: Optimization strategy
            app_port: Application port
            workers: Number of workers
            
        Returns:
            Dockerfile content
        """
        if optimization_strategy == OptimizationStrategy.MULTI_STAGE:
            return f"""# Multi-stage Django Dockerfile
FROM python:3.11-slim as builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH \\
    PYTHONUNBUFFERED=1 \\
    DJANGO_SETTINGS_MODULE=config.settings

RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE {app_port}

HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:{app_port}/health/ || exit 1

CMD ["gunicorn", "--workers", "{workers}", "--bind", "0.0.0.0:{app_port}", "config.wsgi:application"]
"""
        
        else:
            return f"""# Django Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl \\
    build-essential \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 DJANGO_SETTINGS_MODULE=config.settings

RUN python manage.py collectstatic --noinput

EXPOSE {app_port}

HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:{app_port}/health/ || exit 1

CMD ["gunicorn", "--workers", "{workers}", "--bind", "0.0.0.0:{app_port}", "config.wsgi:application"]
"""
    
    def get_dockerfile_nodejs(
        self,
        optimization_strategy: OptimizationStrategy = OptimizationStrategy.PRODUCTION,
        app_port: int = 3000
    ) -> str:
        """
        Generate Dockerfile for Node.js application
        
        Args:
            optimization_strategy: Optimization strategy
            app_port: Application port
            
        Returns:
            Dockerfile content
        """
        if optimization_strategy == OptimizationStrategy.MULTI_STAGE:
            return f"""# Multi-stage Node.js Dockerfile
FROM node:20-slim as builder

WORKDIR /build

COPY package*.json ./
RUN npm ci --only=production

FROM node:20-slim

WORKDIR /app

COPY --from=builder /build/node_modules ./node_modules
COPY . .

EXPOSE {app_port}

HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:{app_port}/health || exit 1

CMD ["node", "server.js"]
"""
        
        elif optimization_strategy == OptimizationStrategy.MINIMAL_SIZE:
            return f"""# Minimal Node.js Dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

COPY . .

EXPOSE {app_port}

HEALTHCHECK --interval=30s --timeout=10s CMD wget --quiet --tries=1 --spider http://localhost:{app_port}/health || exit 1

CMD ["node", "server.js"]
"""
        
        else:
            return f"""# Node.js Dockerfile
FROM node:20-slim

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE {app_port}

HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:{app_port}/health || exit 1

CMD ["node", "server.js"]
"""
    
    def get_dockerfile_java(
        self,
        optimization_strategy: OptimizationStrategy = OptimizationStrategy.PRODUCTION,
        app_port: int = 8080
    ) -> str:
        """
        Generate Dockerfile for Java Spring application
        
        Args:
            optimization_strategy: Optimization strategy
            app_port: Application port
            
        Returns:
            Dockerfile content
        """
        if optimization_strategy == OptimizationStrategy.MULTI_STAGE:
            return f"""# Multi-stage Java Spring Dockerfile
FROM eclipse-temurin:21-jdk-slim as builder

WORKDIR /build

COPY . .
RUN ./mvnw clean package -DskipTests

FROM eclipse-temurin:21-jre-slim

WORKDIR /app

COPY --from=builder /build/target/*.jar app.jar

EXPOSE {app_port}

HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:{app_port}/actuator/health || exit 1

ENTRYPOINT ["java", "-Xmx512m", "-jar", "app.jar"]
"""
        
        else:
            return f"""# Java Spring Dockerfile
FROM eclipse-temurin:21-jdk-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY . .
RUN ./mvnw clean package -DskipTests

EXPOSE {app_port}

HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:{app_port}/actuator/health || exit 1

ENTRYPOINT ["java", "-Xmx512m", "-jar", "target/*.jar"]
"""
    
    def get_dockerfile(
        self,
        container_id: str
    ) -> str:
        """
        Get Dockerfile for specific container
        
        Args:
            container_id: Container ID
            
        Returns:
            Dockerfile content
        """
        if container_id not in self.configs:
            return ""
        
        config = self.configs[container_id]
        
        if config.framework == Framework.FASTAPI:
            return self.get_dockerfile_fastapi(config.optimization_strategy, config.app_port, config.workers)
        elif config.framework == Framework.FLASK:
            return self.get_dockerfile_flask(config.optimization_strategy, config.app_port, config.workers)
        elif config.framework == Framework.DJANGO:
            return self.get_dockerfile_django(config.optimization_strategy, config.app_port, config.workers)
        elif config.framework == Framework.NODEJS:
            return self.get_dockerfile_nodejs(config.optimization_strategy, config.app_port)
        elif config.framework == Framework.JAVA_SPRING:
            return self.get_dockerfile_java(config.optimization_strategy, config.app_port)
        
        return self.get_dockerfile_fastapi(config.optimization_strategy, config.app_port, config.workers)
    
    def get_docker_ignore(self) -> str:
        """
        Generate .dockerignore file
        
        Returns:
            .dockerignore content
        """
        return """# Python
__pycache__
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.pytest_cache/
*.egg-info/
dist/
build/

# Git
.git
.gitignore
.gitattributes

# IDE
.vscode
.idea
*.swp
*.swo
*~
.DS_Store

# Node
node_modules/
npm-debug.log
yarn-error.log

# Environment
.env
.env.local
.env.*.local

# OS
.DS_Store
Thumbs.db

# Docker
Dockerfile
docker-compose*.yml
.dockerignore

# CI/CD
.github
.gitlab-ci.yml
.circleci
Jenkins

# Documentation
docs/
README.md
CONTRIBUTING.md
LICENSE
"""
    
    def get_docker_compose_stack(
        self,
        services: Dict[str, Dict[str, any]],
        version: str = "3.8",
        network_name: str = "app_network"
    ) -> str:
        """
        Generate docker-compose.yml for service stack
        
        Args:
            services: Dictionary of services
            version: Docker Compose version
            network_name: Network name
            
        Returns:
            docker-compose.yml content
        """
        compose = f"""version: '{version}'

services:
"""
        
        for service_name, service_config in services.items():
            compose += f"""
  {service_name}:
    image: {service_config.get('image', 'python:3.11')}
    container_name: {service_config.get('container_name', service_name)}
    ports:
      - "{service_config.get('port', '8000')}:{service_config.get('internal_port', '8000')}"
    environment:
"""
            for env_key, env_val in service_config.get('environment', {}).items():
                compose += f"      {env_key}: {env_val}\n"
            
            if service_config.get('volumes'):
                compose += "    volumes:\n"
                for volume in service_config.get('volumes', []):
                    compose += f"      - {volume}\n"
            
            if service_config.get('command'):
                compose += f"    command: {service_config.get('command')}\n"
            
            if service_config.get('depends_on'):
                compose += "    depends_on:\n"
                for dep in service_config.get('depends_on', []):
                    compose += f"      - {dep}\n"
            
            compose += f"""    networks:
      - {network_name}
    healthcheck:
      test: {service_config.get('healthcheck', '["CMD", "curl", "-f", "http://localhost:8000/health"]')}
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
"""
        
        compose += f"""
networks:
  {network_name}:
    driver: bridge
"""
        return compose


# Singleton instance
_container_generator = None

def get_container_generator() -> ContainerGenerator:
    """Get Container Generator singleton"""
    global _container_generator
    if _container_generator is None:
        _container_generator = ContainerGenerator()
    return _container_generator
