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

**Key Difference from TerraQore**:
- **TerraQore**: Orchestrates 12+ specialized agents (Idea, Planner, Coder, etc.) through workflow stages
- **MetaQore**: Enforces governance rules that TerraQore agents must follow via REST API

---

## 📁 Project Structure

```
metaqore/                          # Standalone Python package
├── DEVELOPMENT_GUIDE.md          # Development roadmap
├── ARCHITECTURE.md               # Design document (v1 extraction plan)
├── ARCHITECTURE_ENHANCEMENT_MAP.md # Enhancement analysis
├── API_REFERENCE.md              # REST API specification (needs v2 update)
├── TODO_UPDATED.md               # Current task checklist (most accurate)
├── PROGRESS.md                   # Weekly progress tracking
├── REVIEW_RECONCILIATION.md      # This week's status analysis
│
├── metaqore/                     # Main Python package
│   ├── __init__.py               # Package exports + version
│   ├── config.py                 # GovernanceMode enum, MetaQoreConfig
│   ├── exceptions.py             # Custom exceptions (GovernanceViolation, ConflictDetectedError, etc.)
│   ├── logger.py                 # Structured logging setup
│   │
│   ├── core/                     # Core governance components
│   │   ├── models.py             # ✅ COMPLETE: 8 Pydantic models
│   │   ├── psmp.py               # ✅ COMPLETE: PSMPEngine with conflict detection
│   │   ├── state_manager.py      # ✅ COMPLETE: PSMP-integrated persistence
│   │   ├── security.py           # ✅ COMPLETE: SecureGateway + policies
│   │   └── audit.py              # ✅ COMPLETE: Compliance auditor
│   │
│   ├── hmcp/                     # Hierarchical Multi-Capability Protocol
│   │   ├── registry.py           # Specialist registry (Week 5+)
│   │   ├── routing.py            # Confidence-based routing (Week 5+)
│   │   └── validation.py         # 4-stage validation gate (Week 5+)
│   │
│   ├── api/                      # REST API layer
│   │   ├── app.py                # FastAPI factory (Week 5)
│   │   ├── middleware.py         # Governance enforcement (Week 5)
│   │   ├── schemas.py            # Pydantic request/response (Week 5)
│   │   └── routes/               # API endpoints (Week 5-7)
│   │
│   ├── streaming/                # WebSocket & webhooks
│   │   ├── websocket_manager.py  # (Week 9)
│   │   ├── webhook_dispatcher.py # (Week 10)
│   │   └── events.py             # Event types (Week 9)
│   │
│   ├── metrics/                  # Observability
│   │   ├── aggregator.py         # Metrics collection (Week 10)
│   │   └── exporter.py           # Prometheus exporter (Week 10)
│   │
│   ├── mock_llm/                 # ✅ COMPLETE: Offline testing harness
│   │   ├── client.py             # MockLLMClient with scenarios
│   │   └── scenarios.py          # Pre-defined response templates
│   │
│   └── storage/                  # ✅ COMPLETE: Pluggable persistence
│       ├── backend.py            # Abstract interface
│       └── backends/
│           ├── sqlite.py         # ✅ SQLite (default)
│           ├── postgres.py       # PostgreSQL (Week 4)
│           └── redis.py          # Redis cache (Week 6)
│
├── tests/                        # Test suite
│   ├── conftest.py               # Pytest fixtures
│   ├── unit/
│   │   ├── test_psmp.py          # ⏳ Blocked by environment
│   │   ├── test_models.py        # ⏳ Blocked by environment
│   │   ├── test_storage_sqlite.py # ⏳ Blocked by environment
│   │   ├── test_state_manager.py # ❌ Not started
│   │   ├── test_security.py      # ⏳ Week 4
│   │   └── test_audit.py         # ⏳ Week 4
│   └── integration/              # Integration tests (Week 5+)
│
├── requirements.txt              # ✅ Core dependencies
├── requirements-dev.txt          # ⚠️ Currently failing to install
├── .gitignore                    # ✅ Python/IDE files
├── README.md                     # Project documentation
└── START_HERE.md                 # Quick start guide
```

---

## 🆕 Status Snapshot (January 4, 2026)

- Phase 1 (core models, PSMP, StateManager, SecureGateway, Audit) ✅ complete.
- Phase 2 Week 5 scaffold ✅: FastAPI app factory, middleware stack, dependency providers.
- Phase 2 Week 6 🚧: `/api/v1/projects`, `/api/v1/tasks`, `/api/v1/artifacts` routers now expose full CRUD plus pagination & filtering with shared response envelopes.
- Regression suite now covers the new routers (`tests/unit/test_api_*.py`).
- Source of truth for daily priorities: `metaqore/TODO_UPDATED.md` (updated Jan 4, 2026).

---

## 🔄 How MetaQore Integrates with TerraQore Studio

### Architecture Diagram

```
┌─────────────────────────────────┐
│     TerraQore Studio            │
│  (Multi-Agent Orchestration)    │
│  - 12 Specialized Agents        │
│  - 6-Stage Workflow             │
│  - LLM Gateway (Ollama/OpenRouter)
└────────────┬────────────────────┘
             │ (calls via REST API)
             │
┌────────────▼──────────────────────┐
│    MetaQore API Gateway            │
│  - Authentication                  │
│  - Rate Limiting                   │
│  - Request Routing                 │
└────────────┬──────────────────────┘
             │
┌────────────▼──────────────────────┐
│  MetaQore Orchestration Engine     │
│  ┌──────────────────────────────┐  │
│  │ PSMP Core                    │  │
│  │ - Artifact Management        │  │
│  │ - Conflict Detection         │  │
│  │ - Blocking Reports           │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │ State Management             │  │
│  │ - Project Persistence        │  │
│  │ - Time-Travel Checkpoints    │  │
│  │ - Dependency Tracking        │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │ Security & Compliance        │  │
│  │ - Governance Enforcement     │  │
│  │ - Audit Trail Logging        │  │
│  │ - Veto Mechanisms            │  │
│  └──────────────────────────────┘  │
└────────────────────────────────────┘
             │
┌────────────▼──────────────────────┐
│  SQLite Database                   │
│  - Projects, Artifacts, Tasks      │
│  - Conflicts, Checkpoints          │
│  - Compliance Audit Trail          │
└────────────────────────────────────┘
```

### TerraQore Agent Workflow → MetaQore Integration

1. **Agent generates code artifact** → Calls `POST /api/v1/artifacts`
2. **MetaQore receives artifact** → Runs PSMP conflict detection
3. **Result**:
   - ✅ **No conflicts**: Artifact persisted, returned to agent
   - ⚠️ **Conflicts detected**: Returns blocking report with suggestions
   - 🔴 **Policy violated**: STRICT mode rejects, ADAPTIVE mode auto-resolves
4. **Agent receives response** → Decides next action (retry, escalate, etc.)

---

## 🎯 Development Workflow

### Environment Setup

```bash
# Initialize virtual environment
cd metaqore
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Install dev tooling (✅ fixed after network reconnect on Jan 4)
pip install -r requirements-dev.txt

# Verify core package works
python -c "from metaqore import MetaQoreConfig; print('✅ MetaQore imports OK')"
```

### Development Cycle

1. **Create feature branch**:
   ```bash
   git checkout -b feature/state-manager
   ```

2. **Implement feature** (currently: StateManager implementation):
   ```bash
   # Edit metaqore/core/state_manager.py
   # Test locally with:
   python -c "from metaqore.core.state_manager import StateManager"
   ```

3. **Write unit tests** (after environment fixed):
   ```bash
   pytest tests/unit/test_state_manager.py -v
   pytest --cov=metaqore tests/
   ```

4. **Format and lint**:
   ```bash
   black metaqore/
   flake8 metaqore/
   mypy metaqore/
   ```

5. **Commit**:
   ```bash
   git add metaqore/core/state_manager.py tests/unit/test_state_manager.py
   git commit -m "feat: implement StateManager with PSMP integration"
   ```

### Key Files to Understand

| File | Purpose | Status | Next Step |
|------|---------|--------|-----------|
| **metaqore/config.py** | Governance modes, configuration | ✅ Complete | Reference in StateManager |
| **metaqore/core/models.py** | Data models | ✅ Complete | Use in StateManager CRUD |
| **metaqore/core/psmp.py** | Conflict detection engine | ✅ Complete | Call from StateManager |
| **metaqore/storage/backend.py** | Abstract persistence | ✅ Complete | Inherit in StateManager |
| **metaqore/storage/backends/sqlite.py** | SQLite implementation | ✅ Complete | Inject in StateManager |
| **metaqore/core/state_manager.py** | **STATE PERSISTENCE** | ❌ NOT STARTED | **BUILD THIS NEXT** |

---

## 🔧 Immediate Development Priorities

### Priority 1: Debug Development Environment (URGENT)
**Status**: Blocking all testing and linting  
**Problem**: `pip install -r requirements-dev.txt` fails (exit code 1)  
**Solution**:
```bash
# Step 1: Check pip version
.\.venv\Scripts\python -m pip --version

# Step 2: Upgrade pip
.\.venv\Scripts\python -m pip install --upgrade pip

# Step 3: Retry install (check verbose output for conflicts)
.\.venv\Scripts\python -m pip install -r requirements-dev.txt -v

# Step 4: If still failing, list actual error
# Look for: version conflicts, missing system dependencies, etc.
```

### Priority 2: Implement StateManager (CRITICAL)
**File**: `metaqore/core/state_manager.py`  
**Depends On**:
- ✅ `StorageBackend` (abstract interface ready)
- ✅ `SQLiteBackend` (concrete implementation ready)
- ✅ `PSMPEngine` (conflict detection ready)
- ✅ `models.py` (all data models defined)

**Key Requirements**:
1. Wrap `StorageBackend` with PSMP validation layer
2. For `create_artifact()`: Call `psmp_engine.check_conflicts()` before persist
3. For `get_project()`: Load all related artifacts and tasks
4. Raise `ConflictDetectedError` if conflicts unresolved
5. Support checkpointing (create snapshot, restore from checkpoint)

**Estimated Effort**: 2-3 days

### Priority 3: Write Comprehensive Unit Tests (HIGH)
**When**: After StateManager implemented and environment fixed  
**Coverage**:
- **test_psmp.py**: Conflict detection, versioning, blocking reports
- **test_models.py**: Serialization, validation, computed fields
- **test_storage_sqlite.py**: CRUD operations, transactions
- **test_state_manager.py**: State persistence, PSMP integration

**Target**: 80%+ coverage by end of Phase 1

### Priority 4: Reconcile Documentation (MEDIUM)
**When**: After Week 3 complete  
**Tasks**:
- [ ] Rewrite ARCHITECTURE.md for v2 design (not extraction plan)
- [ ] Update API_REFERENCE.md with PSMP governance flows
- [ ] Create MetaQore-specific architecture diagrams
- [ ] Document governance mode enforcement at API level
- [ ] Link to TerraQore instructions (show separation clearly)

---

## 📚 Key Architectural Concepts

### PSMP (Project State Management Protocol)
**Purpose**: Enforce artifact governance at persistence layer  
**How It Works**:
1. All artifacts flow through `PSMPEngine` before storage
2. Engine checks for conflicts (versioning, dependencies, circular refs, etc.)
3. Returns blocking report if conflicts detected
4. Agent can retry, override, merge, or escalate
5. Resolution tracked in `Conflict` model with provenance

**Implementation**: `metaqore/core/psmp.py` + `metaqore/core/state_manager.py`

### Governance Modes
**STRICT**: Block all conflicts immediately (production, safety-critical)  
**ADAPTIVE**: Auto-resolve conflicts using strategies (development, fast iteration)  
**PLAYGROUND**: Log only, never block (experiments, learning)

**Configuration**: Set via `METAQORE_GOVERNANCE_MODE` env var or `config.py`

### Storage Backend Pattern
**Why Abstract?**: Different deployments need different backends
- **SQLite** (default): File-based, single-machine, no setup
- **PostgreSQL** (production): Horizontal scaling, enterprise features
- **Redis** (cache): High-speed in-memory persistence

**How to Add New Backend**:
1. Create class inheriting from `StorageBackend`
2. Implement all 8 CRUD operation groups
3. Register in StateManager constructor

---

## 🧪 Testing Strategy

### Unit Tests (Week 1-4)
- Test each component in isolation
- Use mock objects for dependencies
- Run via `pytest tests/unit/`

### Integration Tests (Week 5+)
- Test full workflows (artifact creation → PSMP validation → persistence)
- Use real SQLite database
- Run via `pytest tests/integration/`

### Performance Tests (Week 10+)
- Benchmark <150ms p99 latency target
- Stress test with 1000+ concurrent requests
- Run via `pytest tests/performance/`

### Compliance Tests (Week 4)
- Verify audit trail completeness
- Test policy enforcement
- Verify signature validation

---

## 🚀 Release Schedule

| Phase | Weeks | Status | MVP Deliverable |
|-------|-------|--------|-----------------|
| Phase 1: Core | 1-4 | 🟡 In Progress | PSMP engine + state mgmt |
| Phase 2: API | 5-8 | ⏳ Scheduled | REST endpoints + governance |
| Phase 3: Observability | 9-12 | ⏳ Scheduled | Streaming + metrics |
| Phase 4: Production | 13-16 | ⏳ Scheduled | PostgreSQL + K8s |

**Target MVP**: End of Phase 2 (Week 8) with TerraQore integration

---

## 🔗 Related Projects

### TerraQore Studio
- **Location**: Root of workspace (`core_cli/`)
- **Purpose**: Multi-agent orchestration with 12+ specialized agents
- **Relationship**: Uses MetaQore as governance API client
- **Instructions**: See `.github/copilot-instructions.md` (TerraQore-specific)

### MetaQore (This Project)
- **Location**: `metaqore/` folder
- **Purpose**: Standalone governance engine
- **Clients**: TerraQore (primary) + external agents (future)
- **Instructions**: This file (MetaQore-specific)

**Key Principle**: MetaQore doesn't know about TerraQore's agents; it only knows about artifacts and governance rules.

---

## 📞 Common Questions

### Q: When do I use MetaQore vs. TerraQore?
**A**: 
- Use **TerraQore** if you're building AI agent workflows (ideation → planning → code)
- Use **MetaQore** if you need artifact governance across any system (multi-agent, multi-model, etc.)

### Q: Can MetaQore run standalone?
**A**: Yes! It's a complete REST API. Call it from any client (TerraQore, LangChain, AutoGen, custom code, etc.)

### Q: What makes MetaQore's governance different?
**A**: PSMP is mandatory—all artifacts must flow through conflict detection and can be blocked/versioned. No "governance-free" mode.

### Q: How do I debug StateManager when it's ready?
**A**: 
```python
from metaqore.core.state_manager import StateManager
from metaqore.storage.backends.sqlite import SQLiteBackend
from metaqore.core.models import Project

backend = SQLiteBackend("test.db")
mgr = StateManager(backend)
project = mgr.create_project(Project(name="Test"))
print(f"Created: {project.id}")
```

### Q: When should I commit?
**A**: After each completed task (daily at minimum). Push to feature branch, don't merge to main until week completes and all tests pass.

---

## 🎓 Learning Resources

**PSMP Concept**: See `ARCHITECTURE_ENHANCEMENT_MAP.md` (explains governance philosophy)  
**Data Models**: See `metaqore/core/models.py` (well-commented)  
**Storage Pattern**: See `metaqore/storage/backends/sqlite.py` (reference implementation)  
**API Design**: See `API_REFERENCE.md` (needs v2 update, but shows endpoint structure)

---

**Status**: Ready to implement StateManager. Environment debugging required first.

**Contact**: If blocked > 1 day on a task, escalate immediately.
