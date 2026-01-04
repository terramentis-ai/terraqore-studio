# MetaQore Copilot Instructions

**Version**: 1.0-METAQORE  
**Date**: January 4, 2026  
**Project Scope**: MetaQore v2.0 - Standalone Orchestration Governance Engine  
**Related**: TerraQore Studio (separate project, uses MetaQore as API client)

---

## 🎯 Project Vision

**MetaQore** is a standalone governance engine that:
- Enforces PSMP (Project State Management Protocol) for all artifact management
- Provides configurable strictness modes (STRICT/ADAPTIVE/PLAYGROUND)
- Manages state, conflicts, and compliance across multi-agent systems
- Serves TerraQore Studio as a privileged API client while remaining open to external agents
- Maintains complete audit trails for compliance (GDPR, SOC2, HIPAA ready)

---

## 📊 Current Status (January 4, 2026)

**Phase 1**: ✅ COMPLETE (Core models, PSMP engine, StateManager, SecurityGateway, Audit)  
**Phase 2 Week 5-6**: 🟡 IN PROGRESS (API scaffold + CRUD endpoints with pagination/filtering live)

### Latest Milestones

- FastAPI app factory with middleware, dependency injection, health routes deployed.
- Full CRUD routers for `/api/v1/projects`, `/api/v1/tasks`, `/api/v1/artifacts` with pagination & status/role filtering.
- Shared response metadata envelopes and pagination utilities reduce code duplication.
- 9 unit tests covering project/task/artifact routes (pytest all passing).
- Storage + StateManager expose delete operations; PSMP guards all artifact creation.
- `TODO_UPDATED.md` is the authoritative task checklist; `.github/copilot-instructions.md` documents TerraQore separation.

---

## 📁 Project Structure

```
metaqore/
├── metaqore/                     # Main Python package
│   ├── api/                      # ✅ FastAPI layer
│   │   ├── app.py                #   App factory + state wiring
│   │   ├── middleware.py         #   Request context, governance headers
│   │   ├── schemas.py            #   Pydantic request/response models
│   │   ├── dependencies.py       #   Dependency injection helpers
│   │   └── routes/               
│   │       ├── health.py         #   Health check endpoint
│   │       ├── projects.py       #   Projects CRUD + pagination/filters
│   │       ├── tasks.py          #   Tasks CRUD + pagination/filters
│   │       ├── artifacts.py      #   Artifacts CRUD + pagination/filters
│   │       └── utils.py          #   Shared route utilities
│   │
│   ├── core/                     # ✅ Governance core
│   │   ├── models.py             #   8 Pydantic models (Project, Task, Artifact, Conflict, etc.)
│   │   ├── psmp.py               #   PSMP engine, conflict detection, blocking reports
│   │   ├── state_manager.py      #   State persistence, PSMP integration, checkpointing
│   │   ├── security.py           #   SecureGateway, task sensitivity, routing policies
│   │   └── audit.py              #   ComplianceAuditor, provenance, compliance reporting
│   │
│   ├── storage/                  # ✅ Pluggable persistence
│   │   ├── backend.py            #   Abstract interface
│   │   └── backends/sqlite.py    #   SQLAlchemy-backed SQLite implementation
│   │
│   ├── config.py                 # Configuration, GovernanceMode enum
│   ├── exceptions.py             # Custom exceptions
│   ├── logger.py                 # Structured logging
│   └── __init__.py               # Package exports
│
├── tests/
│   ├── unit/
│   │   ├── test_api_projects.py  # ✅ Projects routes + filters
│   │   ├── test_api_tasks.py     # ✅ Tasks routes + filters
│   │   ├── test_api_artifacts.py # ✅ Artifacts routes + filters
│   │   ├── test_api_app.py       # ✅ FastAPI wiring
│   │   └── ... (Week 1-4 tests)
│   └── conftest.py
│
├── TODO_UPDATED.md               # Daily task checklist (Jan 4)
├── DEVELOPMENT_GUIDE.md          # Development roadmap
├── API_REFERENCE.md              # REST API documentation
├── README.md                      # Project overview
├── requirements.txt
├── requirements-dev.txt
└── .gitignore
```

---

## 🚀 Quick Start

### Environment Setup
```bash
cd metaqore
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run Tests
```bash
pytest tests/unit/test_api_projects.py tests/unit/test_api_tasks.py tests/unit/test_api_artifacts.py
```

### Run API Server (Not yet; Week 7 onwards)
```bash
# Coming soon: uvicorn metaqore.api.app:app --reload
```

---

## 🔗 Integration with TerraQore

MetaQore is a **standalone governance engine** that TerraQore Studio calls via REST API.

**Separation Principle**:
- **TerraQore**: Generates artifacts (code, plans, tests, etc.)
- **MetaQore**: Manages, validates, and governs artifacts

**Integration Flow**:
1. TerraQore agent calls `POST /api/v1/artifacts` with new artifact
2. MetaQore runs PSMP conflict detection
3. Returns result (accepted, blocked, auto-resolved)
4. TerraQore decides next action based on response

**Key**: MetaQore can serve any multi-agent system, not just TerraQore.

---

## 📋 Daily Development

### Before Starting Work
1. Check `TODO_UPDATED.md` for your task
2. Create a feature branch: `git checkout -b feat/governance-endpoints`
3. Verify environment: `pip install -r requirements.txt`

### During Development
- Write code + tests together
- Run relevant tests frequently: `pytest tests/unit/test_api*.py`
- Keep models in sync via `metaqore/core/models.py`
- Use type hints throughout

### Before Committing
- Format: `black metaqore/ tests/`
- Lint: `flake8 metaqore/ tests/`
- Test: `pytest tests/unit/` (full suite if possible)
- Commit with descriptive message: `feat(api): add governance endpoints`

---

## 🎯 Next Steps

**Week 6 (Current)**: Core CRUD endpoints with pagination ✅ DONE  
**Week 7**: Governance endpoints (blocking reports, compliance exports)  
**Week 8**: Streaming hooks, WebSocket support, compliance reporting  
**Week 9+**: Performance tuning, documentation, deployment

---

## 📚 Key Docs

- **`TODO_UPDATED.md`**: Daily tasks and progress (this is the source of truth)
- **`API_REFERENCE.md`**: REST endpoint documentation (needs Week 6 updates)
- **`DEVELOPMENT_GUIDE.md`**: Architecture and patterns
- **Root `.github/copilot-instructions.md`**: TerraQore Studio documentation (separate project)
- **`../TerraQore_vs_MetaQore.md`**: Project separation & integration guide

---

**Last Updated**: January 4, 2026  
**Current Phase**: Phase 2 Week 6 (Core CRUD + pagination live)  
**Next Priority**: Governance endpoints + compliance reporting
