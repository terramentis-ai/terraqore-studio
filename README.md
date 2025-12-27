# 🚀 TERRAQORE Studio

> Enterprise Agentic AI Development Platform

**TERRAQORE Studio** is a comprehensive meta-agentic system that orchestrates specialized AI agents to build, validate, and deploy complete AI projects from conception to production.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)

## ✨ Features

- **Multi-Agent Orchestration** - Specialized agents for ideation, planning, coding, validation, and deployment
- **Multi-Provider LLM Support** - Gemini, Groq, OpenRouter with intelligent fallback routing
- **Production Security** - Prompt injection defense, hallucination detection, sandboxed execution
- **MLOps Pipeline** - Model training, experiment tracking, and automated deployment
- **DevOps Integration** - Docker, Kubernetes, Terraform, CloudFormation generators
- **Real-time Monitoring** - Prometheus, Grafana, and custom metrics collection

## 🏗️ Project Structure

```
terraqore-studio/
├── core_cli/           # Core Python backend & CLI
│   ├── agents/         # Specialized AI agents
│   ├── core/           # Core services & utilities
│   ├── tools/          # Development tools
│   └── orchestration/  # Agent orchestration
├── terraqore_api/      # FastAPI REST service
├── gui/                # React/TypeScript frontend
└── .github/            # CI/CD workflows
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (for GUI)
- Docker (optional, for sandboxed execution)

### Installation

```bash
# Clone the repository
git clone https://github.com/terramentis-ai/terraqore-studio.git
cd terraqore-studio

# Set up Python environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure API keys
cp core_cli/config/settings.example.yaml core_cli/config/settings.yaml
# Edit settings.yaml with your API keys
```

### Running the CLI

```bash
cd core_cli
python -m cli.main --help
```

### Running the API Server

```bash
# Using the start script
./start.sh  # Windows: .\start.ps1

# Or directly
cd terraqore_api
uvicorn app:app --reload --port 8000
```

### Running the GUI

```bash
cd gui
npm install
npm run dev
```

## 🔧 Configuration

Create `core_cli/config/settings.yaml` from the example:

```yaml
llm:
  provider: gemini  # or groq, openrouter
  model: gemini-1.5-flash

providers:
  gemini:
    api_key: ${GEMINI_API_KEY}
  groq:
    api_key: ${GROQ_API_KEY}
```

Set API keys via environment variables:
```bash
export GEMINI_API_KEY=your_key_here
export GROQ_API_KEY=your_key_here
```

## 🛡️ Security

TERRAQORE Studio v1.1 includes enterprise-grade security:

- **Prompt Injection Defense** - 30+ pattern detection with case-insensitive matching
- **Hallucination Detection** - AST validation and specification compliance checking
- **Sandboxed Execution** - Docker-based isolation with CPU/memory/network quotas
- **Execution Auditing** - Comprehensive JSONL transcript logging

## 📖 Documentation

- [Core CLI Documentation](core_cli/Readme.md)
- [API Documentation](terraqore_api/README.md)
- [Contributing Guide](core_cli/CONTRIBUTING.md)

## 🧪 Testing

```bash
cd core_cli
pytest tests/ -v
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](core_cli/LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](core_cli/CONTRIBUTING.md) for details.

---

**TERRAQORE Studio** - Built by [Terramentis AI](https://github.com/terramentis-ai)
