# MetaQore - Multi-Agent Governance Engine

**Project Scope**: MetaQore Standalone Governance API (Independent Repo)  
**Version**: v2.0-BATTLE-READY | January 5, 2026  
**Status**: ✅ 85% Complete (Governance endpoints shipped; auth/docker outstanding)  
**Related**: TerraQore Studio (privileged client), External agents (standard clients)

---

## 🎯 What is MetaQore?

**MetaQore** is a standalone governance engine for multi-agent AI systems. It provides mandatory state management, conflict detection, compliance auditing, and security routing for any agent-based application. Think of it as **"Kubernetes for AI Agents"**.

### Core Capabilities

1. **PSMP (Project State Management Protocol)**: State machine enforcing artifact lifecycle (DRAFT → ACTIVE → ARCHIVED)
2. **Conflict Detection**: Prevents agents from creating incompatible artifacts (dependency versions, file paths)
3. **Compliance Auditing**: Immutable JSONL audit trails for GDPR/HIPAA/SOC2
4. **Security Routing**: Task sensitivity classification (PUBLIC/INTERNAL/SENSITIVE/CRITICAL)
5. **Specialist Management (HMCP)**: Autonomous agent discovery and training
6. **Multi-Tenancy**: Organization-level governance policies and isolated state

### Architecture Overview

```
External Agents → MetaQore API (:8001) → PSMP Engine → StateManager → SQLite
                        ↓
                  Conflict Detection
                  Blocking Reports
                  Audit Trail
```

---

## 🏗️ Project Structure
```
metaqore/
├── metaqore/                     # Core package
│   ├── api/                      # ✅ FastAPI application
│   │   ├── app.py                # App factory, lifespan management
│   │   ├── middleware.py         # Privileged client detection, request context
│   │   ├── dependencies.py       # Dependency injection
│   │   ├── schemas.py            # Pydantic request/response models
│   │   └── routes/
│   │       ├── artifacts.py      # ✅ CRUD + PSMP validation
│   │       ├── governance.py     # ✅ Conflicts, blocking report, audit trail
│   │       ├── health.py         # ✅ Health checks
│   │       ├── projects.py       # ✅ CRUD + pagination/filtering
│   │       └── tasks.py          # ✅ CRUD + project scoping
│   │
│   ├── core/                     # ✅ Governance logic
│   │   ├── compliance_auditor.py # Audit trail logging
│   │   ├── models.py             # Pydantic models (Project, Task, Artifact, Conflict, AuditLog)
│   │   ├── psmp_engine.py        # PSMP state machine, conflict detection
│   │   ├── secure_gateway.py     # Security routing, task sensitivity
│   │   └── state_manager.py      # State orchestration & persistence plumbing
│   │
│   ├── storage/                  # ✅ Pluggable persistence
│   │   ├── backend.py            # Abstract interface
│   │   └── backends/
│   │       └── sqlite.py         # SQLAlchemy implementation
│   │
│   └── config.py                 # Configuration, GovernanceMode enum
│
├── tests/
│   ├── integration/
│   │   └── test_streaming_integration.py # Renamed to avoid name collision with unit tests
│   └── unit/
│       ├── conftest.py
│       ├── test_api_artifacts.py
│       ├── test_api_governance.py # ✅ Governance + audit coverage
│       ├── test_api_projects.py
│       └── test_api_tasks.py
│
├── API_REFERENCE.md              # REST API documentation
├── DEVELOPMENT_ROADMAP.md        # Phase 1-3 roadmap
├── TODO_UPDATED.md               # Task checklist (Jan 4)
├── requirements.txt
└── README.md
```

---

## 🔌 REST API Overview

### ✅ Implemented Endpoints (Week 7 baseline)

**Projects**:
- `GET /api/v1/projects` - List projects (pagination, status filter)
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects/{id}` - Get project
- `PATCH /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

**Tasks**:
- `GET /api/v1/tasks?project_id={id}` - List tasks (project scoped)
- `POST /api/v1/tasks` - Create task
- `GET /api/v1/tasks/{id}` - Get task
- `PATCH /api/v1/tasks/{id}` - Update task
- `DELETE /api/v1/tasks/{id}` - Delete task

**Artifacts**:
- `GET /api/v1/artifacts?project_id={id}` - List artifacts
- `POST /api/v1/artifacts` - Create artifact (PSMP validated)
- `GET /api/v1/artifacts/{id}` - Get artifact
- `PATCH /api/v1/artifacts/{id}` - Update artifact
- `DELETE /api/v1/artifacts/{id}` - Delete artifact

**Governance & Compliance**:
- `GET /api/v1/governance/conflicts` - Paginated conflicts with severity/type filters
- `POST /api/v1/governance/conflicts/{id}/resolve` - Resolve via `ResolutionStrategy` payload
- `GET /api/v1/governance/blocking-report` - PSMP blocking state + remediation hints
- `GET /api/v1/governance/compliance/export?format=json|csv` - Download audit snapshot
- `GET /api/v1/governance/compliance/audit` - Paginated audit trail with provider/agent filters

**Health**:
- `GET /api/v1/health` - Health check

### ⚙️ Latest Additions
- Governance router now drives conflict listing, resolution workflows, and compliance export (JSON or CSV) backed by `SecureGateway` audit data.
- `tests/unit/test_api_governance.py` covers list/resolve/blocking/export/audit paths; full suite currently 75 tests green.
- Streaming integration test renamed to `tests/integration/test_streaming_integration.py` to prevent pytest module collisions.

## 🎯 Current Priorities (post-governance)
1. **Fix FastAPI Deprecation Warning (P1)**: Replace `status.HTTP_422_UNPROCESSABLE_ENTITY` usage triggered during startup to unblock future FastAPI upgrade.
2. **Authentication + Rate Limiting (P1)**: Add JWT/API key enforcement and tighten privileged-client detection before exposing governance endpoints publicly.
3. **Docker Packaging (P2)**: Author `metaqore/Dockerfile` and integrate into root `docker-compose.yml` so TerraQore + MetaQore ship together.
4. **Audit Tooling (P3)**: Add CLI/Make targets for exporting compliance reports and tailing audit trails for ops teams.

## 🔐 Privileged Client Pattern

### How TerraQore Integrates

**TerraQore sends privileged header**:
```python
headers = {"X-MetaQore-Privileged": "terraqore"}
response = requests.post(
    "http://localhost:8001/api/v1/artifacts",
    json={...},
    headers=headers
)
```

**MetaQore middleware detects**:
```python
class PrivilegedClientMiddleware(BaseHTTPMiddleware):
    HEADER_NAME = "X-MetaQore-Privileged"
    
    def _is_privileged(self, header_value: Optional[str]) -> bool:
        # In production, verify token
        return header_value.lower() in {"1", "true", "yes", "terraqore"}
```

**Privileges granted**:
- Auto-resolve LOW/MEDIUM conflicts
- Extended rate limits
- Priority routing
- Access to `/internal/*` endpoints

---

## 🧪 Testing Strategy

### Run All Tests
```bash
cd metaqore
pytest -q
# or
python -m pytest
```

### Test Specific Endpoints
```bash
pytest tests/unit/test_api_governance.py -v
```

### Manual API Testing
```bash
# Start server
uvicorn metaqore.api.app:app --port 8001 --reload

# Test endpoints
curl http://localhost:8001/api/v1/health
curl http://localhost:8001/api/v1/projects
```

**Naming Note**: Keep integration specs under `tests/integration/` (e.g., `test_streaming_integration.py`) so pytest does not collide with similarly named unit modules.

---

## 📊 Current Status & Blockers

### ✅ Production Ready (85%)
- PSMP engine with conflict detection + blocking reports
- SecureGateway audit logging + CSV/JSON compliance exports
- SQLite-backed state persistence with conflict history
- CRUD endpoints (projects, tasks, artifacts) + governance suite
- Middleware (privileged client detection, request metadata)
- 75 passing tests (unit + integration) via `pytest`

### ⚠️ Blockers for Battle 
None (auth/rate-limit rollout and automation guidance documented below).

---

## 🎯 Next Immediate Actions

Operational rollout (auth + rate limit):
```
export METAQORE_API_KEY="<your-key>"
export METAQORE_API_KEY_HEADER="Authorization"   # or X-API-Key
export METAQORE_ENABLE_RATE_LIMIT=true
export METAQORE_RATE_LIMIT_PER_MINUTE=120
export METAQORE_RATE_LIMIT_BURST=240
export METAQORE_PRIVILEGED_TOKEN="terraqore"    # optional shared secret
```

Automation (enabled locally):
- Pre-push hook present at `.git/hooks/pre-push` (pytest, black, flake8)
- Pre-commit config at `.pre-commit-config.yaml`
- Install locally:
```
pip install pre-commit
pre-commit install --hook-type pre-commit --hook-type pre-push
```

Automation (CI mirror): GitHub Actions workflow at [metaqore/.github/workflows/ci.yml](metaqore/.github/workflows/ci.yml) runs pre-commit (lint/format + pytest hook) and then `pytest -q` on push/PR to main/master.

**Pre-push hook example** (add to `.git/hooks/pre-push` and `chmod +x`):
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "Running pytest..." && pytest -q
echo "Running black..." && black metaqore tests
echo "Running flake8..." && flake8 metaqore tests
```

Pre-commit: install with `pip install pre-commit && pre-commit install --hook-type pre-commit --hook-type pre-push` (config at `.pre-commit-config.yaml`).

Testing naming guidance lives in [`tests/README.md`](tests/README.md).

---

## 📚 Key Files to Know

| Path | Purpose |
|------|---------|
| [`metaqore/api/app.py`](metaqore/api/app.py) | FastAPI app factory |
| [`metaqore/api/routes/governance.py`](metaqore/api/routes/governance.py) | Conflicts, blocking report, audit/export endpoints |
| [`metaqore/core/psmp_engine.py`](metaqore/core/psmp_engine.py) | PSMP conflict detection |
| [`metaqore/core/state_manager.py`](metaqore/core/state_manager.py) | State persistence + conflict history |
| [`metaqore/core/models.py`](metaqore/core/models.py) | Project/task/artifact/conflict/audit models |
| [`tests/unit/test_api_governance.py`](tests/unit/test_api_governance.py) | Coverage for governance + compliance APIs |
| [`API_REFERENCE.md`](metaqore/API_REFERENCE.md) | REST API documentation |

---

**Last Updated**: January 5, 2026  
**Version**: 2.0-BATTLE-READY  
**Battle Target**: January 8, 2026  
**For Workspace Overview**: See root `.github/copilot-instructions.md`  
**For TerraQore Details**: See `core_cli/.github/copilot-instructions.md`  
**For GUI Details**: See `gui_simple/.github/copilot-instructions.md`

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

**Week 6**: Core CRUD endpoints with pagination ✅ DONE  
**Week 7**: Governance endpoints (blocking reports, compliance exports) ✅ DONE (Jan 5)  
**Week 8**: Streaming hooks, WebSocket support, authentication + rate limiting  
**Week 9+**: Performance tuning, Docker packaging, documentation polish

---

## 📚 Key Docs

- **`TODO_UPDATED.md`**: Daily tasks and progress (authoritative, recreated Jan 4)
- **`API_REFERENCE.md`**: REST endpoint documentation (add governance + compliance section)
- **`DEVELOPMENT_GUIDE.md`**: Architecture and patterns
- **Root `.github/copilot-instructions.md`**: TerraQore Studio documentation (separate project)
- **`../TerraQore_vs_MetaQore.md`**: Project separation & integration guide

---

**Last Updated**: January 5, 2026  
**Current Phase**: Phase 2 Week 7 wrap-up (governance endpoints + compliance instrumentation complete)  
**Next Priority**: Authentication + Docker packaging + governance documentation refresh
