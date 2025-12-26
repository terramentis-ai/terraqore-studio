"""
CIPipelineBuilder - CI/CD Pipeline Generation

Generates complete CI/CD pipeline configurations for GitHub Actions, GitLab CI,
Jenkins, and other platforms with testing, building, and deployment stages.
"""

import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class PipelinePlatform(Enum):
    """Supported CI/CD platforms"""
    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    CIRCLECI = "circleci"
    AZURE_PIPELINES = "azure_pipelines"


class JobStatus(Enum):
    """Job status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    SKIPPED = "skipped"


@dataclass
class Stage:
    """Pipeline stage"""
    name: str
    description: str = ""
    jobs: List[str] = field(default_factory=list)
    run_when: str = "always"  # always, on_success, on_failure


@dataclass
class Job:
    """Pipeline job"""
    name: str
    stage: str
    script: List[str] = field(default_factory=list)
    before_script: List[str] = field(default_factory=list)
    after_script: List[str] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    cache: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    timeout: str = "30m"
    retry: int = 1
    allow_failure: bool = False


@dataclass
class PipelineConfig:
    """CI/CD pipeline configuration"""
    config_id: str
    project_name: str
    platform: PipelinePlatform
    stages: List[Stage] = field(default_factory=list)
    jobs: List[Job] = field(default_factory=list)
    variables: Dict[str, str] = field(default_factory=dict)
    enable_docker: bool = True
    docker_image: str = "python:3.11"
    enable_caching: bool = True
    enable_notifications: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class CIPipelineBuilder:
    """
    CI/CD Pipeline Builder
    
    Generates complete CI/CD pipeline configurations for multiple platforms
    with testing, building, deployment, and notification stages.
    """
    
    def __init__(self):
        """Initialize CI Pipeline Builder"""
        self.configs: Dict[str, PipelineConfig] = {}
    
    def create_config(
        self,
        project_name: str,
        platform: PipelinePlatform
    ) -> PipelineConfig:
        """Create pipeline configuration"""
        config_id = f"ci_{uuid.uuid4().hex[:8]}"
        config = PipelineConfig(
            config_id=config_id,
            project_name=project_name,
            platform=platform
        )
        self.configs[config_id] = config
        return config
    
    def get_github_actions_workflow(self, config_id: str) -> str:
        """Generate GitHub Actions workflow"""
        if config_id not in self.configs:
            return ""
        config = self.configs[config_id]
        
        workflow = f"""name: CI/CD Pipeline

on:
  push:
    branches: [main, develop, staging]
  pull_request:
    branches: [main, develop]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{{{ github.repository }}}}
  PYTHON_VERSION: '3.11'

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python ${{{{ matrix.python-version }}}}
        uses: actions/setup-python@v4
        with:
          python-version: ${{{{ matrix.python-version }}}}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt
      
      - name: Run linting
        run: |
          flake8 . --count --select=E9,F63,F7,F82
          black --check .
          isort --check-only .
      
      - name: Run type checking
        run: mypy . --ignore-missing-imports
      
      - name: Run tests
        run: |
          pytest tests/ \\
            --cov=appshell \\
            --cov-report=xml \\
            --cov-report=html \\
            --junitxml=test-results.xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          fail_ci_if_error: true
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results-${{{{ matrix.python-version }}}}
          path: test-results.xml

  security:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Run Bandit security scan
        run: |
          pip install bandit
          bandit -r appshell -f json -o bandit-report.json || true
      
      - name: Upload security report
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: bandit-report.json

  build:
    needs: [test, security]
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
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
            type=semver,pattern={{{{version}}}}
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

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop' && github.event_name == 'push'
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Deploy to staging
        env:
          DEPLOY_KEY: ${{{{ secrets.STAGING_DEPLOY_KEY }}}}
        run: |
          mkdir -p ~/.ssh
          echo "${{{{ env.DEPLOY_KEY }}}}" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          ssh-keyscan -H staging.example.com >> ~/.ssh/known_hosts
          
          ssh -i ~/.ssh/deploy_key deploy@staging.example.com "cd /app && git pull origin develop && docker-compose up -d"

  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment:
      name: production
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Deploy to production
        env:
          DEPLOY_KEY: ${{{{ secrets.PROD_DEPLOY_KEY }}}}
        run: |
          mkdir -p ~/.ssh
          echo "${{{{ env.DEPLOY_KEY }}}}" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          ssh-keyscan -H prod.example.com >> ~/.ssh/known_hosts
          
          ssh -i ~/.ssh/deploy_key deploy@prod.example.com "cd /app && git pull origin main && docker-compose up -d"

  notify:
    needs: [test, security, build]
    runs-on: ubuntu-latest
    if: always()
    steps:
      - name: Slack notification
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{{{ secrets.SLACK_WEBHOOK }}}}
          payload: |
            {{
              "text": "Workflow: ${{{{ github.workflow }}}}",
              "blocks": [
                {{
                  "type": "section",
                  "text": {{
                    "type": "mrkdwn",
                    "text": "*Pipeline Status*\\n*Repository*: ${{{{ github.repository }}}}\\n*Branch*: ${{{{ github.ref_name }}}}\\n*Commit*: ${{{{ github.sha }}}}\\n*Status*: ${{{{ job.status }}}}"
                  }}
                }}
              ]
            }}
"""
        return workflow
    
    def get_gitlab_ci_pipeline(self, config_id: str) -> str:
        """Generate GitLab CI pipeline"""
        if config_id not in self.configs:
            return ""
        
        pipeline = """image: python:3.11

stages:
  - test
  - security
  - build
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"

cache:
  paths:
    - .cache/pip
    - venv/

before_script:
  - python -V
  - pip install virtualenv
  - virtualenv venv
  - source venv/bin/activate
  - pip install -r requirements-dev.txt

unit_tests:
  stage: test
  script:
    - pytest tests/ --cov=appshell --cov-report=xml --junitxml=test-results.xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    when: always
    reports:
      junit: test-results.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

lint:
  stage: test
  script:
    - flake8 appshell --count --select=E9,F63,F7,F82
    - black --check appshell
    - isort --check-only appshell

type_check:
  stage: test
  script:
    - mypy appshell --ignore-missing-imports

security_scan:
  stage: security
  script:
    - bandit -r appshell -f json -o bandit-report.json || true
  artifacts:
    paths:
      - bandit-report.json

dependency_scan:
  stage: security
  script:
    - pip install safety
    - safety check --json > safety-report.json || true
  artifacts:
    paths:
      - safety-report.json

build_image:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA -t $CI_REGISTRY_IMAGE:latest .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - docker push $CI_REGISTRY_IMAGE:latest
  only:
    - main
    - develop

deploy_staging:
  stage: deploy
  script:
    - apt-get update && apt-get install -y openssh-client
    - mkdir -p ~/.ssh
    - echo "$STAGING_DEPLOY_KEY" | base64 -d > ~/.ssh/deploy_key
    - chmod 600 ~/.ssh/deploy_key
    - ssh-keyscan -H staging.example.com >> ~/.ssh/known_hosts
    - ssh -i ~/.ssh/deploy_key deploy@staging.example.com "cd /app && git pull origin develop && docker-compose up -d"
  environment:
    name: staging
    url: https://staging.example.com
  only:
    - develop

deploy_production:
  stage: deploy
  script:
    - apt-get update && apt-get install -y openssh-client
    - mkdir -p ~/.ssh
    - echo "$PROD_DEPLOY_KEY" | base64 -d > ~/.ssh/deploy_key
    - chmod 600 ~/.ssh/deploy_key
    - ssh-keyscan -H prod.example.com >> ~/.ssh/known_hosts
    - ssh -i ~/.ssh/deploy_key deploy@prod.example.com "cd /app && git pull origin main && docker-compose up -d"
  environment:
    name: production
    url: https://example.com
  only:
    - main
  when: manual
"""
        return pipeline
    
    def get_jenkinsfile(self, config_id: str) -> str:
        """Generate Jenkinsfile"""
        if config_id not in self.configs:
            return ""
        config = self.configs[config_id]
        
        jenkinsfile = f"""pipeline {{
    agent any
    
    options {{
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 1, unit: 'HOURS')
        timestamps()
    }}
    
    environment {{
        PYTHON_VERSION = '3.11'
        DOCKER_REGISTRY = 'ghcr.io'
        IMAGE_NAME = '{config.project_name.lower()}'
    }}
    
    stages {{
        stage('Checkout') {{
            steps {{
                checkout scm
            }}
        }}
        
        stage('Setup') {{
            steps {{
                script {{
                    sh '''
                        python -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements-dev.txt
                    '''
                }}
            }}
        }}
        
        stage('Test') {{
            parallel {{
                stage('Unit Tests') {{
                    steps {{
                        script {{
                            sh '''
                                . venv/bin/activate
                                pytest tests/ \\
                                    --cov=appshell \\
                                    --cov-report=xml \\
                                    --junitxml=test-results.xml
                            '''
                        }}
                    }}
                }}
                
                stage('Linting') {{
                    steps {{
                        script {{
                            sh '''
                                . venv/bin/activate
                                flake8 appshell
                                black --check appshell
                                isort --check-only appshell
                            '''
                        }}
                    }}
                }}
                
                stage('Type Checking') {{
                    steps {{
                        script {{
                            sh '''
                                . venv/bin/activate
                                mypy appshell --ignore-missing-imports
                            '''
                        }}
                    }}
                }}
            }}
        }}
        
        stage('Security') {{
            steps {{
                script {{
                    sh '''
                        . venv/bin/activate
                        bandit -r appshell -f json -o bandit-report.json || true
                        safety check --json > safety-report.json || true
                    '''
                }}
            }}
        }}
        
        stage('Build') {{
            when {{
                branch 'main'
            }}
            steps {{
                script {{
                    sh '''
                        docker build -t ${{DOCKER_REGISTRY}}/${{IMAGE_NAME}}:${{BUILD_NUMBER}} \\
                                     -t ${{DOCKER_REGISTRY}}/${{IMAGE_NAME}}:latest .
                        docker push ${{DOCKER_REGISTRY}}/${{IMAGE_NAME}}:${{BUILD_NUMBER}}
                        docker push ${{DOCKER_REGISTRY}}/${{IMAGE_NAME}}:latest
                    '''
                }}
            }}
        }}
        
        stage('Deploy Staging') {{
            when {{
                branch 'develop'
            }}
            steps {{
                script {{
                    sh '''
                        ssh -i ~/.ssh/deploy_key deploy@staging.example.com \\
                            "cd /app && git pull origin develop && docker-compose up -d"
                    '''
                }}
            }}
        }}
        
        stage('Deploy Production') {{
            when {{
                branch 'main'
            }}
            input {{
                message "Deploy to production?"
                ok "Deploy"
            }}
            steps {{
                script {{
                    sh '''
                        ssh -i ~/.ssh/deploy_key deploy@prod.example.com \\
                            "cd /app && git pull origin main && docker-compose up -d"
                    '''
                }}
            }}
        }}
    }}
    
    post {{
        always {{
            junit '**/test-results.xml'
            publishHTML([
                reportDir: 'htmlcov',
                reportFiles: 'index.html',
                reportName: 'Code Coverage Report'
            ])
            archiveArtifacts artifacts: 'bandit-report.json,safety-report.json', allowEmptyArchive: true
        }}
        failure {{
            mail to: 'devops@example.com',
                 subject: "Pipeline Failed: ${{env.JOB_NAME}} #${{env.BUILD_NUMBER}}",
                 body: "See console output at ${{env.BUILD_URL}}"
        }}
    }}
}}
"""
        return jenkinsfile


# Singleton instance
_ci_pipeline_builder = None

def get_ci_pipeline_builder() -> CIPipelineBuilder:
    """Get CI Pipeline Builder singleton"""
    global _ci_pipeline_builder
    if _ci_pipeline_builder is None:
        _ci_pipeline_builder = CIPipelineBuilder()
    return _ci_pipeline_builder
