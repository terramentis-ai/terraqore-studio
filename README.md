![TerraQore Banner](https://github.com/terramentis-ai/terraqore-studio/blob/master/docs/terraqore_banner.jpeg)

> Enterprise-Grade Meta-Agentic AI Development Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/) [![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)

**TerraQore Studio** is a comprehensive meta-agentic orchestration platform that coordinates **12 specialized AI agents** through a complete project lifecycle: ideation → validation → planning → code generation → quality validation → security scanning → deployment. Now featuring advanced **Data Science (DSAgent)**, **MLOps (MLOAgent)**, and **DevOps (DOAgent)** capabilities.

---

## 🏗️ Architecture Overview

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI / API / GUI Layer                     │
│              (User Interface & Interaction)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Agent Orchestrator & Workflow Engine            │
│        (State Management, Task Sequencing, PSMP)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                 12 Specialized AI Agents                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   Idea     │  │  Validator │  │  Planner   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   Coder    │  │ CodeValida │  │  Security  │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Notebook  │  │  Conflict  │  │   Test     │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │DataScience │  │   MLOps    │  │  DevOps    │  ✨ NEW  │
│  └────────────┘  └────────────┘  └────────────┘            │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│            Multi-Provider LLM Client Layer                   │
│   ┌─────────────────┐         ┌──────────────────┐         │
│   │   OpenRouter    │  ◄──►   │     Ollama       │         │
│   │   (Primary)     │         │   (Fallback)     │         │
│   └─────────────────┘         └──────────────────┘         │
│        300+ Models                  Local Models            │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Core Services & Infrastructure                  │
│   • SQLite State Management   • Security Validator          │
│   • PSMP Conflict Detection   • Research Tool (ddgs)        │
│   • Build Data Collector      • Attribution System          │
└─────────────────────────────────────────────────────────────┘
```

### Agent Specialization

Each agent operates with a dynamic **PROMPT_PROFILE** system that injects context-aware instructions:

| Agent | Role | Input | Output |
|-------|------|-------|--------|
| **IdeaAgent** | Innovation specialist | User concept | Research-backed variations |
| **IdeaValidatorAgent** | Feasibility analyst | Generated ideas | Feasibility scores & risks |
| **PlannerAgent** | Task architect | Validated idea | Dependency graph & milestones |
| **CoderAgent** | Implementation engineer | Task breakdown | Production-ready code |
| **CodeValidationAgent** | QA reviewer | Generated code | Quality score & issues |
| **SecurityVulnerabilityAgent** | Red-team auditor | Codebase | OWASP/CWE vulnerability report |
| **NotebookAgent** | Jupyter specialist | ML/DS tasks | Interactive notebooks |
| **ConflictResolverAgent** | Merge coordinator | Artifact conflicts | Resolution strategy |
| **TestCritiqueAgent** | Coverage strategist | Code repository | Test recommendations |
| **DSAgent** ✨ | Data science architect | ML project requirements | Framework selection, pipeline design |
| **MLOAgent** ✨ | MLOps specialist | Model deployment needs | Serving, monitoring, drift detection |
| **DOAgent** ✨ | DevOps engineer | Infrastructure requirements | IaC, Kubernetes, CI/CD pipelines |

---

## 🎯 Key Features

### 🤖 Intelligent Orchestration
- **6-Stage Pipeline**: Automatic progression through ideation, validation, planning, coding, quality checks, and security scanning
- **PSMP Protocol**: Project State Management Protocol prevents artifact conflicts and blocks unsafe operations
- **Adaptive Routing**: Task-specific LLM model selection (e.g., Claude for coding, GPT-4 for analysis)

### 🔐 Enterprise Security
- **Prompt Injection Defense**: Built-in security validator scans all agent inputs
- **Sandboxed Execution**: Docker-based isolation for untrusted code
- **Audit Logging**: Full execution trace with structured JSONL logs
- **Vulnerability Scanning**: Automated OWASP Top 10 & CWE mapping

### 🌐 Multi-Provider LLM Support
- **Primary**: Groq (llama-3.3-70b-versatile) or OpenRouter (300+ models)
- **Fallback**: Ollama (offline-capable local models)
- **Smart Routing**: Automatic provider selection based on availability and task type
- **Single API Key**: OpenRouter key unlocks all cloud providers (Groq, Gemini, Anthropic, etc.)
- **Cost Optimization**: Configurable per-agent model selection

### 📊 Production ML Lifecycle
- Experiment tracking and model registry
- Automated hyperparameter tuning
- Model serving and deployment orchestration
- Data drift and performance monitoring

### ⚙️ DevOps Automation
- Infrastructure-as-Code generation (Terraform, CloudFormation)
- Container orchestration (Docker, Kubernetes)
- CI/CD pipeline scaffolding (GitHub Actions, GitLab CI)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ (tested on 3.14.2)
- Node.js 18+ (optional, for GUI)
- Docker (optional, for sandboxed execution)

### Installation

```powershell
# Clone and setup environment
git clone https://github.com/terramentis-ai/terraqore-studio.git
cd terraqore-studio
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt

# Configure LLM providers
copy core_cli\\config\\settings.example.yaml config\\settings.yaml
# Edit config/settings.yaml with your API keys
```

### Configuration Example

```yaml
llm:
  primary_provider: groq  # or openrouter
  fallback_provider: ollama

  groq:
    api_key: ""  # Set GROQ_API_KEY env var (recommended)
    model: llama-3.3-70b-versatile
    temperature: 0.7

  openrouter:
    api_key: ""  # Set OPENROUTER_API_KEY env var (recommended)
    model: openai/gpt-4o-mini
    temperature: 0.7

  ollama:
    base_url: "http://localhost:11434"
    model: phi3.5:latest
    temperature: 0.3

  task_routing:
    ideation:
      provider: groq
      model: llama-3.3-70b-versatile
    code:
      provider: openrouter
      model: anthropic/claude-3.5-sonnet
```

### Basic Usage

```powershell
# Initialize TerraQore
cd core_cli
python -m cli.main init

# Create a new project
python -m cli.main new "AI Code Review Assistant"

# Run ideation phase (research + variations)
python -m cli.main ideate "AI Code Review Assistant"

# Generate project plan
python -m cli.main plan "AI Code Review Assistant"

# List all projects
python -m cli.main list

# View project details
python -m cli.main show "AI Code Review Assistant"
```

### API Server

```powershell
cd core_cli
python -m cli.main backend_main:app --reload
# Server runs on http://localhost:8000
```

### GUI (Optional)

```powershell
cd gui
npm install
npm run dev
# GUI runs on http://localhost:5173
```

---

## 📁 Project Structure

```
terraqore_studio/
├── core_cli/                 # Primary backend & CLI
│   ├── agents/              # 12 specialized AI agents
│   │   ├── base.py         # BaseAgent with PROMPT_PROFILE system
│   │   ├── idea_agent.py
│   │   ├── planner_agent.py
│   │   ├── coder_agent.py
│   │   ├── data_science_agent.py  # ✨ ML architecture
│   │   ├── mlops_agent.py         # ✨ Model deployment
│   │   ├── devops_agent.py        # ✨ Infrastructure
│   │   └── ...
│   ├── core/                # Core services
│   │   ├── llm_client.py   # Multi-provider LLM abstraction
│   │   ├── state.py        # SQLite state management
│   │   ├── security_validator.py
│   │   └── psmp/           # Project State Management Protocol
│   ├── orchestration/       # Workflow coordination
│   │   └── orchestrator.py
│   ├── tools/              # Utility tools
│   │   └── research.py     # Web search (ddgs)
│   └── cli/                # Command-line interface
│       └── main.py
├── terraqore_api/          # FastAPI REST service
├── gui/                    # React frontend
├── config/                 # Global configuration
│   └── settings.yaml
├── data/                   # SQLite databases & artifacts
└── projects/              # Generated project outputs
```

---

## 🔧 Workflow Pipeline

### 1. **Ideation** (IdeaAgent)
- Researches current trends using ddgs search
- Generates 3-5 project variations
- Refines recommendations based on feasibility

### 2. **Validation** (IdeaValidatorAgent)
- Scores technical, timeline, and resource feasibility (0-10)
- Identifies risks and mitigation strategies
- Gates progression to planning phase

### 3. **Planning** (PlannerAgent)
- Breaks project into tasks with dependencies
- Generates milestones and time estimates
- Creates execution roadmap

### 4. **Code Generation** (CoderAgent)
- Implements tasks according to plan
- Generates production-ready code
- Follows language-specific best practices

### 5. **Code Validation** (CodeValidationAgent)
- Scores code quality (0-10)
- Checks style, documentation, error handling
- Blocks deployment if score < 6.0

### 6. **Security Scanning** (SecurityVulnerabilityAgent)
- Scans for OWASP Top 10 vulnerabilities
- Maps findings to CWE/CVE standards
- Flags critical issues for remediation

---

## 🧪 Testing

```powershell
# Run full system regression test
python test_terraqore.py

# Test code validation pipeline
python test_code_validation.py

# Test security vulnerability scanning
python test_security_scan.py

# Test specialized agents (DS, MLOps, DevOps)
python test_specialized_agents.py

# Run full test suite
cd core_cli
pytest tests/ -v

# Test specific agent
pytest tests/test_agents.py::TestIdeaAgent -v
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **"No API key found"** | Set `OPENROUTER_API_KEY` env var or configure in `config/settings.yaml` |
| **"Ollama unavailable"** | Non-blocking if primary provider is configured; install Ollama for offline mode |
| **Import errors** | Ensure `pip install -r requirements.txt` completed successfully |
| **Database locked** | Stop all TerraQore instances; remove `data/terraqore.db` to reset |
| **Research tool warnings** | `pip install ddgs>=9.10.0` to update search dependency |

---

## 📊 System Requirements

- **Python**: 3.10+ (tested on 3.14.2)
- **Memory**: 4GB minimum, 8GB recommended
- **Storage**: 500MB for installation + generated artifacts
- **Network**: Required for OpenRouter API (optional for offline Ollama mode)

### Python 3.14 Compatibility Notes
- Core runtime fully compatible
- Some dev tools (black, flake8, mypy) may require C++ compiler
- Use wheel-only installs or downgrade to Python 3.12 if needed

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](core_cli/CONTRIBUTING.md) for guidelines.

### Development Setup

```powershell
# Install dev dependencies
pip install -r core_cli/requirements.txt

# Run linters
black core_cli/
flake8 core_cli/

# Run type checks
mypy core_cli/
```

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](core_cli/LICENSE) for details.

---

## 📝 Release Notes

### v1.2.0-STABLE — January 2, 2026

**Production-Ready Release: Full Pipeline Validation & Specialized Agents**

**🎯 Major Updates:**
- **3 New Specialized Agents**: 
  - **DSAgent**: ML architecture design (framework selection, data pipelines, training strategies)
  - **MLOAgent**: Production MLOps (deployment, monitoring, drift detection, CI/CD)
  - **DOAgent**: Infrastructure-as-Code (Terraform, Kubernetes, multi-cloud deployment)
- **Enhanced Security**: Environment variable-based API key management (no hardcoded secrets)
- **Fixed JSON Parsing**: CoderAgent now successfully generates code on first iteration
- **LLM Provider Updates**: 
  - Groq SDK 1.0.0 support (llama-3.3-70b-versatile)
  - Improved OpenRouter integration
  - Automatic fallback handling

**✅ Fully Validated Workflows:**
- **Ideation**: 35.77s (6 research sources, multi-variation generation) ✓
- **Planning**: 25.98s (13 tasks, 4 milestones, dependency graph) ✓
- **Code Generation**: First-iteration success (4 files, production-ready) ✓
- **Code Validation**: Hallucination detector operational (24 findings detected) ✓
- **Security Scanning**: 0 vulnerabilities (OWASP/CWE compliance) ✓
- **Specialized Agents**: All 3 tested and operational ✓
  - DSAgent: 25.55s (sentiment analysis architecture)
  - MLOAgent: 22.85s (fraud detection MLOps pipeline)
  - DOAgent: 35.68s (e-commerce microservices infrastructure)

**🔧 Bug Fixes:**
- Fixed CoderAgent JSON parsing (escape sequence handling)
- Fixed specialized agent context attribute errors
- Fixed AgentResult creation in all 3 new agents
- Corrected execution_time calculation in agent responses

**🔐 Security Improvements:**
- Removed hardcoded API keys from config files
- Added environment variable support (GROQ_API_KEY, OPENROUTER_API_KEY)
- Enhanced prompt injection detection

**📦 Breaking Changes:**
- API keys must now be set via environment variables (recommended) or config files
- Groq model updated to llama-3.3-70b-versatile (llama-3.1-70b-versatile deprecated)

**Migration Notes:**
- Set environment variables: `GROQ_API_KEY` and/or `OPENROUTER_API_KEY`
- Update `config/settings.yaml` if using file-based configuration
- Existing projects work without modification

---

### v1.1 — December 31, 2025

**Agent Prompt System Unification**
- Migrated all 9 agents to dynamic `PROMPT_PROFILE` system
- Research tool modernization (ddgs 9.10.0)
- Python 3.14 compatibility updates

---

**TerraQore Studio** — Where AI Agents Build AI Systems

For detailed architecture documentation, see [.github/copilot-instructions.md](.github/copilot-instructions.md)

