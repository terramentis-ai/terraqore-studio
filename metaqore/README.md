# MetaQore

**Production-Grade Orchestration Governance Engine for Multi-Agent Systems**

> **"MetaQore makes agent orchestration as standard and reliable as Kubernetes is for containerized applications."**

MetaQore is a standalone, cloud-native API service that serves as the foundational infrastructure layer for multi-agent AI systems. It enforces mandatory governance, security, and compliance protocols, transforming experimental agent scripts into production-ready enterprise applications.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
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
pytest tests/unit/test_api_projects.py tests/unit/test_api_tasks.py tests/unit/test_api_artifacts.py -v
```

### Start the API Server (Future)

```bash
uvicorn metaqore.api.app:app --reload
# API available at http://localhost:8000/api/v1
# Docs at http://localhost:8000/docs
```

---

## 🔐 Security Tooling

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
- **API Foundation**: FastAPI Application Factory, CRUD Endpoints, Governance Routes
- **Streaming & Observability**: WebSocket Manager, Webhook Dispatcher, Rich Events, Metrics System, Prometheus Exporter

### 🚧 Phase 3: In-Progress (HMCP Specialist Engine)
- **HMCP Policy Config**: Declarative blueprint for specialist creation
- **Adversarial Testing Harness**: Attack simulation framework
- **LLM Gateway**: Prompt Assembly Engine, Cache-Aware Scheduling

See [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) for detailed roadmap.

---

## 📚 Documentation

- **[DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md)** — Detailed status, tasks, and roadmap
- **[API_REFERENCE.md](API_REFERENCE.md)** — Detailed REST endpoint specs
- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** — Architecture, patterns, immediate priorities

---

## 🤝 Contributing

MetaQore is under active development. Contributions welcome!

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/your-feature`)
3. Write tests + code
4. Ensure tests pass (`pytest tests/unit/`)
5. Format (`black metaqore/`) and lint (`flake8 metaqore/`)
6. Push and create a Pull Request

---

## 📄 License

MIT License — See [LICENSE](LICENSE) for details.
