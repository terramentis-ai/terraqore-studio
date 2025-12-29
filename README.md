# 🚀 TERRAQORE Studio

![TerraQore Studio Banner](docs/terraqore_banner.jpg)

> Enterprise agentic AI development platform — unified documentation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/) [![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)

TERRAQORE Studio (TerraQore) is a comprehensive meta-agentic system that orchestrates specialized AI agents to ideate, plan, generate, validate, and deploy production-ready AI projects.

## Key Highlights

- Multi-provider LLM support with provider fallback and cost optimizations
- Multi-agent orchestration (ideation, planning, coding, validation, MLOps, DevOps)
- Secure sandboxed execution, prompt-injection defenses, and audit logging
- Built-in ML lifecycle tools: experiment tracking, model registry, and serving
- DevOps generators: Docker, Kubernetes, CloudFormation, Terraform

## Unified Quick Start

Prerequisites:
- Python 3.10+
- Node.js 18+ (optional, for the GUI)
- Docker (optional, for sandboxed execution)

Install and prepare:

```powershell
# From repository root
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt

# copy example settings and edit API keys
copy core_cli\\config\\settings.example.yaml core_cli\\config\\settings.yaml
# edit settings.yaml to add provider keys and options
```

Run CLI help:

```powershell
cd core_cli
python -m cli.main --help
```

Run API server (development):

```powershell
cd terraqore_api
uvicorn app:app --reload --port 8000
```

Run GUI (optional):

```powershell
cd gui
npm install
npm run dev
```

## Canonical Configuration (example)

Edit `config/settings.yaml` or `core_cli/config/settings.yaml` depending on your setup. Example canonical fields:

```yaml
llm:
  primary_provider: "gemini"
  fallback_provider: "groq"

  gemini:
    model: "gemini-1.5-flash"
    temperature: 0.7
    max_tokens: 4096
    api_key: ${GEMINI_API_KEY}

  groq:
    model: "llama-3.1-70b-versatile"
    temperature: 0.7
    max_tokens: 4096
    api_key: ${GROQ_API_KEY}

system:
  max_retries: 3
  timeout: 30
  debug: false

agents:
  enable_ideas: true
  enable_planning: true
  enable_coding: true
  enable_validation: true
  enable_ml: true
  enable_devops: true

database:
  type: "sqlite"
  path: "./data/terraqore.db"

output:
  backup_existing: true
  log_level: "INFO"
```

Set API keys as environment variables (PowerShell example):

```powershell
$env:GEMINI_API_KEY = "your_key"
$env:GROQ_API_KEY = "your_key"
```

## Project Layout (summary)

```
terraqore-studio/
├── core_cli/           # Core Python backend & CLI (primary runtime)
│   ├── agents/         # Specialized AI agents
│   ├── core/           # Core services & utilities
│   └── orchestration/  # Agent orchestration
├── terraqore_api/      # FastAPI REST service
├── gui/                # React/TypeScript frontend (optional)
├── projects/           # Generated project artifacts
├── config/             # Global configuration
└── tests/              # Test suites and e2e harnesses
```

## Workflow Commands (CLI reference)

Use the `TerraQore` CLI (or the `cli.main` module) to run phases:

```bash
TerraQore init                 # Initialize system
TerraQore new <name>           # Create project
TerraQore ideate <name>        # Ideation phase
TerraQore plan <name>          # Planning phase
TerraQore generate <name>      # Generate code (stack choices supported)
TerraQore validate <name>      # Security and quality validations
TerraQore train <name>         # Run ML training pipelines
TerraQore deploy <name>        # Deploy (targets: k8s, aws-lambda, docker-compose)
```

## Security & Auditing

- Prompt injection detection and mitigation
- Hallucination detection and AST/spec verification
- Sandboxed Docker-based execution with resource limits
- Execution audit logs (JSONL) for traceability

## Testing

Run automated tests from the repository root:

```powershell
cd core_cli
pytest tests/ -v
```

## Troubleshooting (common)

- "API Key Not Found": verify environment variables or `core_cli/config/settings.yaml` entries
- "Module Import Errors": `pip install -r requirements.txt` or `pip install -e .`
- "Database Locked": ensure no other TerraQore instance is running; remove `data/terraqore.db` to reset

## Contributing & License

Contributions welcome. See `core_cli/CONTRIBUTING.md` for contribution guidelines.

This repository is released under the MIT License — see `core_cli/LICENSE`.

---

For full, developer-level documentation, see `Marketing/Doclogs/FLYNT_STUDIO_COMPLETE_DOCUMENTATION.md` or the docs folder if present.

**TERRAQORE Studio** — enterprise-grade agentic AI tooling
