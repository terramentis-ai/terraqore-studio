# Workspace Organization: Three-Repo Ecosystem

**Date**: January 4, 2026  
**Purpose**: Define the three independent projects sharing this workspace for wholesome context

---

## 🎯 Philosophy

This workspace houses **three independent projects** that form a complete agentic systems ecosystem:

1. **TerraQore Studio** — Orchestrates agents through workflows
2. **MetaQore** — Governs artifacts and enforces compliance
3. **GUI Frontend** — Provides user interface for both systems

**Why together?**
- **Wholesome context**: Developers see the full stack while coding
- **Rapid iteration**: Changes across layers can be tested immediately
- **Clear separation**: Each project has own repo, docs, versioning
- **Independent deployment**: Each can be deployed separately

---

## 📁 Directory Structure

```
c:\Users\user\Desktop\terraqore_studio\
│
├── .github/                         # TerraQore configs
│   └── copilot-instructions.md     # TerraQore instructions ⚠️ PROJECT 1
│
├── core_cli/                        # ⚠️ PROJECT 1: TerraQore Studio
│   ├── agents/                      # 12 specialized agents
│   ├── core/                        # LLM gateway, state, security
│   ├── orchestration/               # 6-stage pipeline
│   ├── cli/                         # Command-line interface
│   └── ...
│
├── terraqore_api/                   # ⚠️ PROJECT 1: TerraQore API
│   └── ...
│
├── metaqore/                        # ⚠️ PROJECT 2: MetaQore (STANDALONE)
│   ├── .github/
│   │   └── copilot-instructions.md # MetaQore instructions ⚠️ PROJECT 2
│   ├── metaqore/                    # Python package
│   │   ├── core/                    # PSMP, StateManager, Security
│   │   ├── api/                     # REST API layer
│   │   ├── storage/                 # Pluggable backends
│   │   └── ...
│   ├── tests/                       # MetaQore tests
│   ├── requirements.txt             # NO TerraQore dependencies
│   └── README.md                    # MetaQore-specific readme
│
├── gui_simple/                      # ⚠️ PROJECT 3: GUI Frontend (STANDALONE)
│   ├── src/                         # React source
│   ├── package.json                 # Node dependencies
│   ├── vite.config.js               # Vite bundler
│   ├── README.md                    # GUI-specific readme
│   └── ...
│   └── app.py                       # 🗑️ DEPRECATED: Streamlit (ignore)
│
├── docs/                            # ⚠️ PROJECT 1: TerraQore docs
├── ollama_runtime/                  # ⚠️ PROJECT 1: Embedded Ollama
├── scripts/                         # ⚠️ PROJECT 1: Build scripts
│
├── WORKSPACE_ORGANIZATION.md        # THIS FILE (workspace-level)
├── TerraQore_vs_MetaQore.md         # Integration guide (workspace-level)
└── README.md                        # TerraQore root readme
```

---

## 🔀 Git Remote Configuration

### Project 1: TerraQore Studio

**Location**: Root directory + `core_cli/` + `terraqore_api/` + `docs/`  
**Repository**: https://github.com/terramentis-ai/terraqore-studio.git  
**Remote Name**: `origin`

**Commands**:
```bash
cd c:\Users\user\Desktop\terraqore_studio
git remote -v
# origin  https://github.com/terramentis-ai/terraqore-studio.git (fetch)
# origin  https://github.com/terramentis-ai/terraqore-studio.git (push)

# When committing TerraQore changes:
git add core_cli/ terraqore_api/ docs/ .github/copilot-instructions.md
git commit -m "feat(agents): add new capability"
git push origin master
```

### Project 2: MetaQore

**Location**: `metaqore/` subfolder (completely standalone)  
**Repository**: https://github.com/terramentis-ai/metaqore.git  
**Remote Name**: `terramentis`

**Commands**:
```bash
cd c:\Users\user\Desktop\terraqore_studio
git remote -v
# terramentis  https://github.com/terramentis-ai/metaqore.git (fetch)
# terramentis  https://github.com/terramentis-ai/metaqore.git (push)

# When committing MetaQore changes:
git add metaqore/
git commit -m "feat(api): add governance endpoints"
git push terramentis master
```

**IMPORTANT**: MetaQore has ZERO dependencies on TerraQore code. It's a separate Python package that can run completely independently.

### Project 3: GUI Frontend

**Location**: `gui_simple/` subfolder (React app)  
**Repository**: To be created  
**Remote Name**: TBD (e.g., `gui` or `frontend`)

**Commands** (after repo created):
```bash
cd c:\Users\user\Desktop\terraqore_studio
git remote add frontend https://github.com/terramentis-ai/terraqore-gui.git

# When committing GUI changes:
git add gui_simple/
git commit -m "feat(ui): add project dashboard"
git push frontend master
```

**Tech Stack**:
- React 18+
- TypeScript
- Vite (bundler)
- TailwindCSS (styling)

**Deprecated**: `gui_simple/app.py` (Streamlit) — no longer maintained

---

## 🎨 Project Responsibilities

### TerraQore Studio

| Aspect | Details |
|--------|---------|
| **Purpose** | Multi-agent orchestration system |
| **Key Components** | 12 agents (Idea, Planner, Coder, Security, etc.), Orchestration pipeline, LLM Gateway |
| **What It Does** | Generates artifacts (code, plans, ideas), Routes to LLMs (Ollama/OpenRouter), Executes workflows |
| **Dependencies** | FastAPI, Ollama, OpenRouter, Streamlit (deprecated) |
| **Instructions** | `.github/copilot-instructions.md` (root) |
| **Versioning** | v1.5.1-SECURITY-FIRST |

### MetaQore

| Aspect | Details |
|--------|---------|
| **Purpose** | Governance engine for multi-agent systems |
| **Key Components** | PSMP Engine, StateManager, SecureGateway, Compliance Auditor |
| **What It Does** | Validates artifacts, Detects conflicts, Enforces policies, Maintains audit trail |
| **Dependencies** | FastAPI, SQLAlchemy, Pydantic (NO TerraQore code) |
| **Instructions** | `metaqore/.github/copilot-instructions.md` |
| **Versioning** | v1.0 (Phase 1 complete, Phase 2 in progress) |

### GUI Frontend

| Aspect | Details |
|--------|---------|
| **Purpose** | User interface for TerraQore + MetaQore |
| **Key Components** | React dashboard, Project views, Real-time updates |
| **What It Does** | Displays projects/artifacts, Triggers workflows, Shows governance status |
| **Dependencies** | React, Vite, TailwindCSS (calls TerraQore/MetaQore APIs) |
| **Instructions** | `gui_simple/README.md` (to be created) |
| **Versioning** | TBD |

---

## 🔗 Integration Architecture

```
┌─────────────────────────────────────────────┐
│            GUI Frontend (React)             │
│         http://localhost:5173               │
└──────────────┬──────────────┬───────────────┘
               │              │
       REST API Calls    REST API Calls
               │              │
      ┌────────▼──────┐  ┌────▼─────────────┐
      │  TerraQore    │  │   MetaQore       │
      │  API          │  │   API            │
      │  :8000        │  │   :8001          │
      └────────┬──────┘  └────┬─────────────┘
               │              │
      ┌────────▼──────────────▼───────────┐
      │   Orchestration Layer             │
      │   (TerraQore calls MetaQore)      │
      │                                   │
      │   POST /api/v1/artifacts ────>   │
      │   (validate via PSMP)             │
      └───────────────────────────────────┘
```

**Flow**:
1. User interacts with **GUI** (React)
2. GUI calls **TerraQore API** to start workflow
3. TerraQore agents generate artifacts
4. TerraQore calls **MetaQore API** to validate artifacts
5. MetaQore runs PSMP conflict detection
6. MetaQore returns result (accepted/blocked/resolved)
7. TerraQore continues based on MetaQore response
8. GUI displays real-time updates

---

## 🛠️ Development Workflows

### Working on TerraQore Studio

```bash
# 1. Verify you're in root
cd c:\Users\user\Desktop\terraqore_studio

# 2. Make changes to TerraQore code
code core_cli/agents/my_agent.py

# 3. Test
python -m pytest core_cli/tests/

# 4. Stage ONLY TerraQore files
git add core_cli/ terraqore_api/ .github/copilot-instructions.md

# 5. Commit with TerraQore scope
git commit -m "feat(agents): improve code generation"

# 6. Push to TerraQore repo
git push origin master
```

### Working on MetaQore

```bash
# 1. Verify you're in root (MetaQore is subfolder)
cd c:\Users\user\Desktop\terraqore_studio

# 2. Make changes to MetaQore code
code metaqore/metaqore/core/psmp.py

# 3. Test (use MetaQore venv)
cd metaqore
.\.venv\Scripts\python.exe -m pytest tests/unit/

# 4. Stage ONLY MetaQore files
cd ..
git add metaqore/

# 5. Commit with MetaQore scope
git commit -m "feat(psmp): add dependency resolution"

# 6. Push to MetaQore repo
git push terramentis master
```

### Working on GUI Frontend

```bash
# 1. Navigate to GUI folder
cd c:\Users\user\Desktop\terraqore_studio\gui_simple

# 2. Install dependencies (if needed)
npm install

# 3. Run dev server
npm run dev  # http://localhost:5173

# 4. Make changes
code src/components/ProjectDashboard.tsx

# 5. Test
npm run test

# 6. Stage ONLY GUI files
cd ..
git add gui_simple/

# 7. Commit with GUI scope
git commit -m "feat(ui): add artifact timeline view"

# 8. Push to GUI repo (after remote created)
git push frontend master
```

---

## ⚠️ Critical Rules

### NEVER Mix Commits

❌ **Bad** (mixing projects):
```bash
git add core_cli/ metaqore/ gui_simple/
git commit -m "various updates"
```

✅ **Good** (one project per commit):
```bash
git add core_cli/
git commit -m "feat(agents): add validation"
git push origin master

git add metaqore/
git commit -m "feat(api): add endpoints"
git push terramentis master

git add gui_simple/
git commit -m "feat(ui): add dashboard"
git push frontend master
```

### Check Before Pushing

Always verify which remote you're pushing to:

```bash
# Check current branch and remotes
git status
git remote -v

# For TerraQore changes
git log --oneline -1  # Check commit
git push origin master  # Push to TerraQore repo

# For MetaQore changes
git log --oneline -1  # Check commit
git push terramentis master  # Push to MetaQore repo

# For GUI changes
git log --oneline -1  # Check commit
git push frontend master  # Push to GUI repo
```

### Copilot Instructions Selection

When using GitHub Copilot or AI assistants:

- **Working on TerraQore?** → Reference `.github/copilot-instructions.md` (root)
- **Working on MetaQore?** → Reference `metaqore/.github/copilot-instructions.md`
- **Working on GUI?** → Reference `gui_simple/README.md` (to be created)

Each file contains project-specific patterns, architecture, and guidelines.

---

## 📊 Status Dashboard (January 4, 2026)

### TerraQore Studio: v1.5.1-SECURITY-FIRST

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1 (Agents) | ✅ Complete | 12 agents operational |
| Phase 2 (API) | ✅ Complete | FastAPI backend live |
| Phase 3 (Gateway) | ✅ Complete | Ollama + OpenRouter routing |
| Phase 4 (Embedding) | ⚙️ In Progress | Bundled Ollama distribution |
| Phase 5 (Security) | ✅ Complete | Task sensitivity classification |

### MetaQore: v1.0 (Governance Engine)

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1 (Core) | ✅ Complete | Models, PSMP, StateManager, Security, Audit |
| Phase 2 Week 5 | ✅ Complete | FastAPI scaffold + middleware |
| Phase 2 Week 6 | ✅ Complete | CRUD endpoints + pagination |
| Phase 2 Week 7 | 🔄 Current | Governance endpoints, compliance exports |
| Phase 2 Week 8 | 📋 Queued | Streaming hooks, WebSocket support |

### GUI Frontend: React + Vite

| Component | Status | Notes |
|-----------|--------|-------|
| React Setup | ✅ Complete | Vite + TypeScript + TailwindCSS |
| Project Dashboard | 🔄 In Progress | View projects, tasks, artifacts |
| Workflow Triggers | 📋 Queued | Start TerraQore workflows from UI |
| Real-time Updates | 📋 Queued | WebSocket integration |
| Streamlit UI | 🗑️ Deprecated | No longer maintained |

---

## 🚀 Next Steps

### Immediate (Week 7)
1. **MetaQore**: Finish governance endpoints (blocking reports, policy management)
2. **TerraQore**: Complete Phase 4 Ollama bundling
3. **GUI**: Create separate repo + update README

### Short-term (Week 8-10)
1. **MetaQore**: Add WebSocket streaming, compliance export API
2. **TerraQore**: Integrate MetaQore governance into agent workflows
3. **GUI**: Real-time dashboard with WebSocket updates

### Long-term (Week 11+)
1. Deploy all three as separate services
2. Create Docker images for each
3. Add authentication/authorization layer
4. Public API documentation

---

## 📚 Documentation Index

### Workspace-Level Docs
- `WORKSPACE_ORGANIZATION.md` (THIS FILE) — Three-repo structure
- `TerraQore_vs_MetaQore.md` — Integration architecture
- `README.md` (root) — TerraQore overview

### TerraQore Docs
- `.github/copilot-instructions.md` — Development guidelines
- `CHANGELOG.md` — Version history
- `core_cli/CONTRIBUTING.md` — Contribution guide

### MetaQore Docs
- `metaqore/.github/copilot-instructions.md` — Development guidelines
- `metaqore/README.md` — Project overview
- `metaqore/API_REFERENCE.md` — REST API specs
- `metaqore/DEVELOPMENT_GUIDE.md` — Architecture patterns

### GUI Docs
- `gui_simple/README.md` (to be created) — Setup + development guide
- `gui_simple/package.json` — Dependencies + scripts

---

## 💬 Questions?

**"Which project am I working on?"**  
→ Check the file path:
- `core_cli/*` or `terraqore_api/*` = TerraQore
- `metaqore/*` = MetaQore  
- `gui_simple/*` = GUI

**"Which instructions should I follow?"**  
→ Each project has its own copilot instructions:
- TerraQore: `.github/copilot-instructions.md`
- MetaQore: `metaqore/.github/copilot-instructions.md`
- GUI: `gui_simple/README.md`

**"Can I use MetaQore code in TerraQore?"**  
→ **NO.** MetaQore is standalone. TerraQore calls MetaQore via REST API only.

**"Can GUI import from TerraQore directly?"**  
→ **NO.** GUI is a separate React app. It calls TerraQore/MetaQore via HTTP APIs.

**"Why are they all in one folder?"**  
→ For "wholesome context" — developers see the full ecosystem while maintaining clean separation. Each can still be deployed independently.

---

**Last Updated**: January 4, 2026  
**Maintainer**: TerraQore Development Team  
**Status**: Three-repo structure clarified and documented ✅
