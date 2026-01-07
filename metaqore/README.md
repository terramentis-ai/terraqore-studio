# MetaQore

**Production-Grade Orchestration Governance Engine for Multi-Agent Systems**

> **"MetaQore makes agent orchestration as standard and reliable as Kubernetes is for containerized applications."**

MetaQore is a standalone, cloud-native API service that serves as the foundational infrastructure layer for multi-agent AI systems. It enforces mandatory governance, security, and compliance protocols, transforming experimental agent scripts into production-ready enterprise applications.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests Passing](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#testing)

---

## 📋 Executive Summary

MetaQore extracts and evolves the internal PSMP (Project State Management Protocol) into a standalone service that provides:

1. **Mandatory Artifact Governance** via PSMP state machine
2. **Autonomous Specialist Discovery & Training** via HMCP (Hierarchical Multi-Capability Protocol)
3. **Task-Based Security Routing** via SecureGateway
4. **Production-Grade LLM Execution** via dynamic-prompt LLM Gateway with KV caching
5. **Adversarial Resilience** via comprehensive validation gates and attack simulation
6. **Complete Compliance Auditing** for GDPR, HIPAA, SOC2 readiness

---

## 🎯 Core Vision

Instead of "How do I deploy one agent?", teams ask "How do I orchestrate 50+ agents safely, efficiently, and observably?"

### Key Principles (Non-Negotiable)

- ✅ **PSMP is Mandatory**: Every project, task, and artifact transition is governed by PSMP state machine
- ✅ **Determinism First**: Strict mode provides pure PSMP pipelines; flexibility is opt-in and bounded
- ✅ **SecureGateway Veto Power**: Absolute authority over non-compliant operations
- ✅ **Zero-Trust Architecture**: All requests validated against PSMP + SecureGateway before execution
- ✅ **Immutable Audit Trail**: Complete provenance and compliance logging for every operation
- ✅ **Autonomous Specialist System**: HMCP auto-discovers repetitive patterns and trains optimized agents

---

## 🏗️ Architecture Overview

### Three-Tier Governance Model

```
┌─────────────────────────────────────────┐
│  External Agents                        │
│  (LangChain, AutoGen, Custom, etc.)     │
│  ← REST API / WebSocket / Agent Protocol│
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│  ⭐ MetaQore Orchestration Engine ⭐   │
├─ PSMP Engine (Mandatory Governance)     │
├─ HMCP System (Specialist Management)    │
├─ SecureGateway (Security + Routing)     │
├─ LLM Gateway (Dynamic Execution)        │
├─ Streaming & Webhooks (Real-time)       │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│  Data Layer                             │
│  ├─ SQLite (default) / PostgreSQL       │
│  ├─ Redis (distributed cache)           │
│  └─ Audit Trail (immutable logs)        │
└─────────────────────────────────────────┘
```

### Five Operational Layers

| Layer | Component | Responsibility |
|-------|-----------|-----------------|
| **Governance** | PSMP Engine | State transitions, artifact versioning, conflict detection |
| **Specialist System** | HMCP | Autonomous agent discovery, training, validation, routing |
| **Security** | SecureGateway | Task sensitivity classification, policy veto, threat detection |
| **Execution** | LLM Gateway | Dynamic prompt injection, KV caching, batching, worker pooling |
| **Observability** | Streaming + Metrics | Real-time events, webhooks, Prometheus metrics, compliance audits |

---

## 🚀 Quick Start

### Install

```bash
cd metaqore
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run Tests

```bash
pytest -q
# or filtered:
pytest tests/unit/test_api_governance.py -v
```

### Start the API Server (Future)

```bash
uvicorn metaqore.api.app:app --reload
# API available at http://localhost:8000/api/v1
# Docs at http://localhost:8000/docs
```

---

## � System Specifications for Full Stack Deployment

### Minimum Specifications (Dev/Testing)
- **CPU**: 4+ cores (Intel i5/Ryzen 5 or equivalent)
- **RAM**: 16 GB
- **Storage**: 32 GB SSD (models + database)
- **Python**: 3.11+ (required for llama-cpp-python wheels)
- **GPU**: Optional (CPU inference supported via llama.cpp)
- **Network**: Localhost development

### Recommended Specifications (Production)
- **CPU**: 16+ cores (Intel Xeon/Ryzen 7000 or equivalent)
- **RAM**: 64-128 GB (for multi-model concurrent inference + state caching)
- **Storage**: 512 GB+ SSD (model cache, artifact storage, audit logs)
- **GPU**: NVIDIA RTX 4090/H100 or equivalent for 3-5 concurrent model inferences
- **Python**: 3.11 LTS
- **Network**: Gigabit Ethernet minimum; 10G recommended for distributed deployments

### Capabilities (Fully Assembled System)

Once all components are integrated, the system supports:

1. **12+ Specialized AI Agents** operating concurrently
   - IdeaAgent (creative ideation)
   - PlannerAgent (project architecture)
   - CoderAgent (code generation with 4-file output)
   - CodeValidationAgent (quality scoring 0-10)
   - SecurityVulnerabilityAgent (CRITICAL sensitivity routing)
   - TestCritiqueAgent (automated test generation)
   - DataScienceAgent (ML architecture design)
   - MLOpsAgent (deployment & monitoring)
   - DevOpsAgent (infrastructure automation)
   - ConflictResolverAgent (dependency resolution)
   - NotebookAgent (Jupyter generation)
   - IdeaValidatorAgent (feasibility assessment)

2. **6-Stage Orchestration Pipeline**
   - Ideation → Validation → Planning → Code Generation → Validation → Security Scan
   - Auto-iteration on quality gates (min score 6/10 for code)
   - Mandatory PSMP conflict detection at each stage

3. **Multi-Provider LLM Gateway**
   - Offline-first routing (llama.cpp via MetaQore native)
   - Cloud fallback (OpenRouter with 300+ models including Groq, Anthropic, Claude)
   - Intelligent provider selection based on task sensitivity
   - KV-cache optimization for repeated contexts

4. **Security-First Architecture**
   - TaskSensitivity classification (PUBLIC/INTERNAL/SENSITIVE/CRITICAL)
   - Policy-based routing (DefaultRoutingPolicy, EnterprisePolicy, CompliancePolicy)
   - Prompt injection detection via SecurityValidator
   - Immutable compliance audit trail (JSONL format)

5. **Enterprise Governance (PSMP)**
   - Project state machine (INITIALIZED → PLANNING → IN_PROGRESS → COMPLETED/FAILED)
   - Artifact versioning and conflict detection
   - Dependency resolution with semantic conflict solving
   - Blocking reports on policy violations

6. **Real-Time Collaboration**
   - WebSocket streaming for agent progress updates
   - Live conflict notifications
   - Status aggregation dashboard
   - Concurrent project management (50+ projects)

7. **Performance Targets**
   - Full ideation cycle: 30-45 seconds
   - Full planning cycle: 20-30 seconds
   - Code generation: 45-120 seconds (depending on complexity)
   - Security scan: 15-30 seconds
   - End-to-end workflow: 3-5 minutes for medium complexity project

8. **Scalability**
   - 12+ agents with 10+ concurrent projects
   - 100+ artifacts per project
   - 1000+ state transitions logged per workflow
   - Sub-second response times for health checks and basic queries

---

## �🔐 Security Tooling

### Configure SecureGateway Routing

MetaQore now lets you choose the SecureGateway policy via config or environment variable:

```bash
export METAQORE_SECURE_GATEWAY_POLICY=enterprise  # aliases: default, enterprise, compliance
```

YAML config example:

```yaml
governance_mode: strict
secure_gateway_policy: compliance
```

Policies:
- `default` / `default_local_first`: Local-first with cloud fallback for public tasks
- `enterprise` / `enterprise_residency`: Local-only for internal data, cloud allowed for public
- `compliance` / `compliance_local_only`: All workloads forced through local providers

### Compliance Audit CLI

Generate summaries from the JSONL audit logs using the bundled script:

```bash
cd metaqore
python -m metaqore.scripts.compliance_report --organization acme --log-dir ../logs
# add --json for raw output
```

The CLI loads `compliance_audit_<org>.jsonl`, aggregates routing/veto events, and prints an at-a-glance compliance snapshot for governance reviews.

---

## 📊 Current Implementation Status

### ✅ Phase 1: Complete (Core PSMP Governance)
- **PSMP Engine**: Full state machine with lifecycle states (PROPOSED → ACTIVE → DEPRECATED)
- **Models**: Artifact, Project, Task, Conflict, Checkpoint, Provenance
- **StateManager**: Async checkpointing, time-travel, SQLite backend
- **SecurityGateway**: Task sensitivity classification (PUBLIC/INTERNAL/SENSITIVE/CRITICAL)
- **ComplianceAuditor**: Immutable audit trail with provenance tracking

### ✅ Phase 2: Complete (API & Observability)
- **API Foundation**: FastAPI Application Factory, CRUD Endpoints, Governance Routes (conflict listing, resolution, blocking report, compliance export/audit)
- **Streaming & Observability**: WebSocket Manager, Webhook Dispatcher, Rich Events, Metrics System, Prometheus Exporter

### 🚧 Phase 3: In-Progress (HMCP Specialist Engine)
- **HMCP Policy Config**: Declarative blueprint for specialist creation
- **Adversarial Testing Harness**: Attack simulation framework
- **LLM Gateway**: Prompt Assembly Engine, Cache-Aware Scheduling

See [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) for detailed roadmap.

---

## 📚 Documentation

- **[DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md)** — Detailed status, tasks, and roadmap
- **[API_REFERENCE.md](API_REFERENCE.md)** — REST specs including governance/conflict/compliance endpoints
- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** — Architecture, patterns, immediate priorities
- **[TODO_UPDATED.md](TODO_UPDATED.md)** — Rolling task tracker (Jan 4 refresh)

---

## 🤝 Contributing

MetaQore is under active development. Contributions welcome!

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/governance-refresh`)
3. Write tests + code
4. Ensure tests pass (`pytest`)
5. Format (`black metaqore/`) and lint (`flake8 metaqore/`)
6. Push and create a Pull Request

---

## 📄 License

MIT License — See [LICENSE](LICENSE) for details.
