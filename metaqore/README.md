# MetaQore

**Governance-First Orchestration Engine for Multi-Agent Systems**

MetaQore is a standalone, production-grade governance engine that enforces artifact management protocols, conflict detection, and compliance auditing for any multi-agent AI system.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests Passing](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#testing)

---

## 🎯 What MetaQore Does

MetaQore sits between your multi-agent system and persistent state, providing:

| Feature | Benefit |
|---------|---------|
| **PSMP Protocol** | Mandatory artifact validation before persistence—no governance shortcuts |
| **Conflict Detection** | Automatic detection of versioning, dependency, and circular reference issues |
| **State Management** | Time-travel checkpoints, project/artifact/task persistence, rollback support |
| **Compliance Audit** | Complete JSON audit trail for GDPR, HIPAA, SOC2 compliance |
| **Security Policies** | Task-based sensitivity classification + enforcement (local/cloud routing) |
| **REST API** | Full HTTP interface—works with any language/framework |

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

## 📊 Architecture

MetaQore is built in layers:

```
┌─────────────────────────────────────┐
│     Your Multi-Agent System         │
│  (TerraQore, LangChain, AutoGen)    │
└────────────┬────────────────────────┘
             │ REST API Calls
             ▼
┌─────────────────────────────────────┐
│   MetaQore REST API Gateway         │
│  (FastAPI + dependency injection)   │
└────────────┬────────────────────────┘
             │
┌────────────▼─────────────────────────┐
│  Governance & State Layer            │
│                                      │
│  ┌────────────────────────────────┐ │
│  │ PSMP Engine                    │ │
│  │ - Artifact versioning          │ │
│  │ - Conflict detection           │ │
│  │ - Dependency resolution        │ │
│  └────────────────────────────────┘ │
│                                      │
│  ┌────────────────────────────────┐ │
│  │ StateManager                   │ │
│  │ - Project/artifact persistence │ │
│  │ - Checkpointing & rollback     │ │
│  │ - PSMP-guarded operations      │ │
│  └────────────────────────────────┘ │
│                                      │
│  ┌────────────────────────────────┐ │
│  │ Security & Compliance          │ │
│  │ - Task sensitivity routing     │ │
│  │ - Governance policies          │ │
│  │ - Audit trail logging          │ │
│  └────────────────────────────────┘ │
└────────────┬─────────────────────────┘
             │
┌────────────▼─────────────────────────┐
│   SQLite Storage (default)           │
│   (PostgreSQL support coming)        │
└──────────────────────────────────────┘
```

### Core Concepts

- **Project**: Top-level container (e.g., "TerraQore Workflow 123")
- **Artifact**: Output from an agent (code, plan, test, spec, etc.)
- **Task**: Unit of work assigned to an agent
- **Conflict**: Issue detected by PSMP (version mismatch, circular dep, etc.)
- **Checkpoint**: Time-travel snapshot for project restoration

---

## 📡 API Overview

### Projects
```bash
# List with pagination & filtering
GET /api/v1/projects?page=1&page_size=25&status=planning

# CRUD
POST   /api/v1/projects                    # Create
GET    /api/v1/projects/{id}               # Get
PATCH  /api/v1/projects/{id}               # Update
DELETE /api/v1/projects/{id}               # Delete
```

### Tasks
```bash
# List tasks for a project (with filtering)
GET /api/v1/tasks?project_id=proj_123&status=in_progress

# CRUD
POST   /api/v1/tasks
GET    /api/v1/tasks/{id}
PATCH  /api/v1/tasks/{id}
DELETE /api/v1/tasks/{id}
```

### Artifacts
```bash
# List artifacts (with type/creator filtering)
GET /api/v1/artifacts?project_id=proj_123&artifact_type=code

# CRUD with PSMP validation
POST   /api/v1/artifacts  # Runs conflict detection
GET    /api/v1/artifacts/{id}
PATCH  /api/v1/artifacts/{id}
DELETE /api/v1/artifacts/{id}
```

See [API_REFERENCE.md](API_REFERENCE.md) for full endpoint documentation.

---

## 🔧 Development

### Project Layout

```
metaqore/
├── metaqore/
│   ├── api/              # FastAPI routers, schemas, middleware
│   ├── core/             # PSMP, StateManager, SecureGateway, Audit
│   ├── storage/          # Pluggable backends (SQLite, PostgreSQL)
│   ├── config.py         # GovernanceMode enum, MetaQoreConfig
│   └── ...
├── tests/
│   ├── unit/             # API tests, model tests, integration tests
│   └── conftest.py
├── requirements.txt      # Core dependencies
├── requirements-dev.txt  # Dev tools (pytest, black, flake8, mypy)
└── DEVELOPMENT_GUIDE.md  # Detailed architecture & patterns
```

### Development Workflow

1. **Create feature branch**: `git checkout -b feat/governance-endpoints`
2. **Code + test**: Write tests first, implement second
3. **Validate**: `pytest tests/unit/ -v`
4. **Format**: `black metaqore/ tests/` + `flake8 metaqore/`
5. **Commit**: Descriptive message with scope (e.g., `feat(api): add blocking reports endpoint`)
6. **Push**: `git push origin feat/governance-endpoints`

See [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for architecture patterns and integration details.

---

## 🎯 Current Status

**Phase 1**: ✅ COMPLETE
- Core models, PSMP engine, StateManager, SecureGateway, Audit trail

**Phase 2 (API Layer)**: 🚧 IN PROGRESS
- Week 5-6: ✅ FastAPI scaffold + CRUD endpoints with pagination/filtering
- Week 7: 🔄 Governance endpoints (blocking reports, compliance exports)
- Week 8: 📋 Streaming hooks, WebSocket support, compliance reporting

See [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for detailed roadmap.

---

## 🔗 Integration

### With TerraQore Studio

MetaQore is a **standalone governance engine** that TerraQore agents call via REST API. They are separate but integrated projects:

- **TerraQore**: Generates artifacts (orchestrates 12+ agents through 6-stage workflow)
- **MetaQore**: Manages and governs artifacts (enforces policies, detects conflicts, audits)

**Integration flow**:
1. TerraQore agent calls `POST /api/v1/artifacts`
2. MetaQore runs PSMP validation
3. Returns result (accepted, blocked, or auto-resolved)
4. TerraQore continues based on response

### With Other Systems

MetaQore can serve **any multi-agent system**—LangChain, AutoGen, custom systems, etc. It only requires HTTP access to the REST API.

See [../TerraQore_vs_MetaQore.md](../TerraQore_vs_MetaQore.md) for complete separation & integration guide.

---

## 🧪 Testing

```bash
# Run unit tests
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ --cov=metaqore

# Specific test file
pytest tests/unit/test_api_projects.py -v
```

All tests pass ✅ (9/9 routes covered).

---

## 📚 Documentation

- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** — Architecture, patterns, immediate priorities
- **[API_REFERENCE.md](API_REFERENCE.md)** — Detailed REST endpoint specs
- **[../TerraQore_vs_MetaQore.md](../TerraQore_vs_MetaQore.md)** — Project separation & integration

---

## 📦 Dependencies

### Core
- **FastAPI** — Modern async web framework
- **Pydantic** — Data validation via Python type hints
- **SQLAlchemy** — ORM for database operations
- **SQLite** — Default persistence (no setup needed)

### Dev
- **pytest** — Unit testing
- **black** — Code formatting
- **flake8** — Linting
- **mypy** — Static type checking

See `requirements.txt` and `requirements-dev.txt`.

---

## 🚀 Deployment

### Local Development
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest tests/unit/
```

### Production (Coming Soon)
- Docker image for containerized deployment
- PostgreSQL backend for horizontal scaling
- Kubernetes manifests for cloud deployment

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

---

## 💬 Questions?

- **Architecture**: See [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)
- **API Usage**: See [API_REFERENCE.md](API_REFERENCE.md)
- **Integration**: See [../TerraQore_vs_MetaQore.md](../TerraQore_vs_MetaQore.md)

---

**Built with ❤️ for governance-first AI systems**

MetaQore v1.0 — January 2026
- ✅ **Safe**: Automatic conflict detection and blocking policies
- ✅ **Optimized**: Automatic specialist discovery and routing
- ✅ **Compliant**: Built-in GDPR/HIPAA-ready audit trails

---

## Key Features

### 1. **Universal State Management (PSMP)**
Track every artifact, dependency, and state transition across any agent

```python
# Any agent can emit artifacts
artifact = client.artifacts.create(
    project_id="proj_123",
    artifact_type="code",
    data={"language": "python", "code": "..."},
    created_by="my_agent",
    depends_on=["art_456"]  # Automatic dependency tracking
)

# Conflicts auto-detected
if artifact.blocked_by:
    # Resolve or escalate
    client.artifacts.resolve_conflict(artifact.id, strategy="merge")
```

### 2. **Specialist System (HMCP)**
Automatically discover and train task-optimized agent variants

```python
# List available specialists
specialists = client.specialists.list(skill="code_generation")

# Route to best performer
routing = client.specialists.route(specialist_id, task)
# → 92% confidence, <500ms latency
```

### 3. **Compliance & Security**
Built-in task sensitivity classification and policy enforcement

```python
# Auto-classify sensitivity
classification = client.security.classify(
    agent_name="SecurityAgent",
    task_type="code_review",
    has_sensitive_data=True
)
# → "critical" sensitivity
# → Local (Ollama) only routing
# → Full audit trail

# Generate compliance report
report = client.compliance.report(time_window="2026-01-01 to 2026-01-03")
```

### 4. **Real-Time Streaming**
WebSocket events for real-time agent coordination

```python
async with client.ws.connect(project_id) as ws:
    await ws.subscribe(event_types=["artifact.*", "specialist.*"])
    
    async for event in ws:
        if event['type'] == 'artifact.created':
            # React to new artifact
            await handle_new_output(event['data'])
```

### 5. **Multi-Vendor Agnostic**
Works with any agent framework and any LLM

| Agent Framework | Status | Integration |
|-----------------|--------|-------------|
| **LangChain** | ✅ Supported | REST API |
| **AutoGen** | ✅ Supported | REST API |
| **Crew.AI** | ✅ Supported | REST API |
| **Custom Code** | ✅ Supported | REST API + SDK |

| LLM Provider | Status |
|--------------|--------|
| **OpenAI** | ✅ Supported |
| **Anthropic** | ✅ Supported |
| **Ollama** | ✅ Supported |
| **Groq** | ✅ Supported |
| **Any LLM** | ✅ Supported |

---

## Quick Start

### 1. Install Client Library

```bash
pip install metaqore-client
```

### 2. Get API Key

Sign up at https://metaqore.io (free tier available)

```bash
export METAQORE_API_KEY=sk_live_abc123...
```

### 3. Connect Your Agent

```python
from metaqore import MetaQore

# Initialize
client = MetaQore(api_key="sk_live_abc123")

# Create project
project = client.projects.create(
    name="My Agent System",
    description="AI analysis tool"
)

# Agent emits artifacts
artifact = client.artifacts.create(
    project_id=project.id,
    artifact_type="analysis",
    data={"summary": "Analysis result..."},
    created_by="my_agent"
)

print(f"✅ Artifact tracked: {artifact.id}")
```

### 4. Monitor in Dashboard

Visit https://metaqore.io/dashboard
- See all artifacts and dependencies
- Track agent performance
- Resolve conflicts
- View compliance audit trail

## 🧪 Mock LLM Client (Development Only)

Local workflows can use the new `MockLLMClient` instead of hitting a real
provider. It mirrors the TerraQore `LLMResponse` shape and can be swapped out
for the production client once your Ollama instance is ready.

```python
from metaqore.mock_llm import MockLLMClient

mock_llm = MockLLMClient(default_mode="summary")
response = mock_llm.generate(
    "List the steps to extract PSMP into MetaQore",
    agent_name="PlannerAgent",
)
print(response.content)
```

Custom fixtures can be registered via `register_template()` or
`register_handler()` to simulate structured outputs for integration tests.

---

## Deployment Options

### Option 1: Cloud SaaS (Recommended)
- **URL**: https://metaqore.io
- **Setup**: 5 minutes
- **Cost**: Free tier + Pro ($99-299/mo)
- **Benefits**: Zero ops, 99.9% uptime, auto-scaling

### Option 2: Self-Hosted Docker
- **Setup**: Docker Compose
- **Cost**: Hosting fees only
- **Benefits**: Full control, on-premises option

### Option 3: Kubernetes
- **Setup**: Helm chart
- **Cost**: Kubernetes cluster
- **Benefits**: Enterprise scale, high availability

See [DEPLOYMENT.md](./DEPLOYMENT.md) for setup guides.

---

## Documentation

### Core Concepts

1. **[PRODUCT_VISION.md](./PRODUCT_VISION.md)** 
   - Vision, market opportunity, competitive landscape
   - 12-month roadmap
   - Revenue model and GTM strategy

2. **[ARCHITECTURE.md](./ARCHITECTURE.md)**
   - System design and component breakdown
   - Extraction plan from TerraQore
   - Data models and schemas
   - Testing strategy

3. **[API_REFERENCE.md](./API_REFERENCE.md)**
   - Complete REST/WebSocket API specification
   - Request/response examples
   - Error handling and rate limits
   - Authentication details

4. **[INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)**
   - LangChain integration patterns
   - AutoGen integration examples
   - Crew.AI integration guide
   - Custom agent integration
   - Error handling and best practices

5. **[DEPLOYMENT.md](./DEPLOYMENT.md)**
   - Cloud SaaS setup
   - Self-hosted Docker (Docker Compose)
   - Kubernetes deployment (Helm charts)
   - Monitoring, backups, and disaster recovery

---

## Architecture Overview

### Three Tiers

```
┌─────────────────────────────────────┐
│  External Agents                    │
│  (LangChain, AutoGen, Custom, etc)  │
└──────────────┬──────────────────────┘
               │ REST API / WebSocket
┌──────────────▼──────────────────────┐
│  MetaQore Orchestration Engine       │
│  ├─ PSMP (State Management)          │
│  ├─ Specialist System (HMCP)         │
│  ├─ Security & Compliance            │
│  ├─ Real-Time Streaming              │
│  └─ Metrics & Analytics              │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Data Layer                          │
│  ├─ PostgreSQL (state)               │
│  ├─ Redis (caching)                  │
│  └─ Audit logs                       │
└─────────────────────────────────────┘
```

### Key Components

| Component | Purpose | Source |
|-----------|---------|--------|
| **PSMP** | State management, artifact governance | TerraQore (extract) |
| **Specialist System** | Auto-discovery and training of optimized agents | TerraQore (extract) |
| **SecureGateway** | Task sensitivity classification, compliance routing | TerraQore (extract) |
| **REST API** | Agent integration, artifact CRUD, metrics | New |
| **WebSocket Manager** | Real-time event streaming | TerraQore (extract) |
| **Metrics Aggregator** | Per-agent and system-wide analytics | TerraQore (extract) |

---

## Extraction Plan from TerraQore

MetaQore extracts and generalizes proven components from TerraQore:

### Phase 1: Core Extraction (Q1 2026)
- Extract PSMP (state.py, psmp_orchestrator_bridge.py)
- Extract Specialist System (agents/, protocols/)
- Extract SecureGateway (security.py, compliance auditing)
- Create standalone API package

### Phase 2: MVP (Q1 2026)
- REST API endpoints (FastAPI)
- SQLite/PostgreSQL backend
- WebSocket streaming
- Early access program (50 teams)

### Phase 3: Production (Q2 2026)
- Self-hosted Docker deployment
- Enterprise features (RBAC, custom policies)
- Specialist marketplace
- 100+ paying customers

### Phase 4: Scale (Q3-Q4 2026)
- Kubernetes support
- Multi-region SaaS
- Certified integrations (LangChain, AutoGen, etc.)
- Industry standard adoption

---

## Competitive Positioning

### vs. LangChain / AutoGen / Crew.AI

**These are agent frameworks**. MetaQore is the **orchestration layer** that:
- Works with any framework (no lock-in)
- Adds governance and state management
- Auto-discovers and trains specialists
- Provides compliance auditing

### vs. Temporal / Prefect / Airflow

**These are workflow orchestrators**. MetaQore is **agent-specific**:
- Designed for LLM + agent workloads
- Understands artifact dependencies
- Native specialist system
- Security-first by default

### Unique Differentiators

✅ **First PSMP standard** for multi-agent governance  
✅ **Specialist system** with auto-discovery and training  
✅ **Compliance ready** (GDPR/HIPAA out-of-box)  
✅ **Vendor agnostic** (any LLM, any agent)  
✅ **Proven architecture** (from TerraQore production use)  

---

## Use Cases

### 1. Multi-Agent Orchestration
Coordinate 10+ agents with automatic state management and conflict detection.

### 2. Enterprise AI Systems
Deploy AI safely with compliance auditing and security-first routing.

### 3. Agent Optimization
Auto-discover which agents/models work best for each task.

### 4. AI Development Teams
Shared state, version control, and audit trails for collaborative development.

### 5. Production AI Systems
Monitor, optimize, and maintain production agents with full observability.

---

## Success Metrics (12 Months)

| Metric | Target |
|--------|--------|
| **Cloud SaaS Signups** | 1,000+ |
| **Paying Customers** | 50-100 |
| **MRR** | $50K+ |
| **Specialists Created** | 100+ |
| **Integration Partners** | 5+ |
| **Community Size** | 5,000+ |

---

## Roadmap

### ✅ Current Phase: Ideation

- ✅ Product vision document
- ✅ Technical architecture design
- ✅ API specification
- ✅ Integration guides
- ✅ Deployment guides
- Next: Validate product-market fit with 5-10 early customers

### 🎯 Q1 2026: MVP & Early Access

- Extract components from TerraQore
- Build REST API (FastAPI)
- Launch early access program
- Get initial customer feedback

### 🚀 Q2-Q3 2026: Production

- Self-hosted deployment option
- Enterprise features
- Integrate with LangChain, AutoGen
- Scale to 100+ customers

### 📈 Q4 2026+: Market Leadership

- Multi-region SaaS
- Open standard specification
- Marketplace for specialists
- $50M+ ARR goal

---

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL (or SQLite for self-hosted)
- **Cache**: Redis
- **Queue**: Celery (for async specialist training)
- **Monitoring**: Prometheus, Datadog

### Deployment
- **Containers**: Docker
- **Orchestration**: Kubernetes (optional)
- **IaC**: Terraform
- **CI/CD**: GitHub Actions

### SDKs & Clients
- **Python**: Official SDK
- **Node.js/TypeScript**: Coming soon
- **Go**: Coming soon

---

## Contributing

MetaQore is extracted from TerraQore (open-source). Plans for community involvement:

1. **Open-Source Core**: PSMP and Specialist System
2. **SDK Contributions**: Help build integrations
3. **Deployment Guides**: Contribute Helm charts, Terraform modules
4. **Integration Examples**: LangChain, AutoGen, Crew.AI adapters

---

## Support & Community

- **Website**: https://metaqore.io
- **Discord**: https://discord.gg/metaqore
- **Documentation**: https://docs.metaqore.io
- **GitHub**: https://github.com/metaqore/metaqore
- **Email**: support@metaqore.io
- **Slack**: (Enterprise tier)

---

## FAQ

**Q: Is this a rebranded TerraQore?**  
A: No. MetaQore extracts the PSMP core from TerraQore and makes it agent-agnostic. MetaQore = orchestration layer for any agent. TerraQore = end-to-end AI development platform.

**Q: Do I have to use MetaQore with TerraQore?**  
A: No. MetaQore works with any agent, any framework.

**Q: Can I self-host MetaQore?**  
A: Yes. Docker Compose and Kubernetes deployment options available.

**Q: How much does MetaQore cost?**  
A: Free tier (10 agents), Pro ($99-299/mo), Enterprise (custom). See [PRODUCT_VISION.md](./PRODUCT_VISION.md).

**Q: When is it available?**  
A: Cloud SaaS in Q1 2026, self-hosted option in Q2 2026.

**Q: How does specialist training work?**  
A: Automatic via MOPD (Multi-teacher Optimization via Policy Distillation). See [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## Contact

- **Product Inquiries**: product@metaqore.io
- **Press**: press@metaqore.io
- **Partnerships**: partnerships@metaqore.io
- **Technical Support**: support@metaqore.io

---

## License

MetaQore will be available under the MIT License (when released).

---

## Acknowledgments

MetaQore builds on proven architecture and patterns from [TerraQore](https://github.com/terraqore/terraqore), an open-source AI development platform.

---

**Last Updated**: January 3, 2026  
**Status**: 📋 Ideation Phase → 🚀 Ready for MVP Planning  
**Maintained by**: MetaQore Product Team

---

## Next Steps

1. **Review Documentation**: Start with [PRODUCT_VISION.md](./PRODUCT_VISION.md)
2. **Explore Architecture**: Read [ARCHITECTURE.md](./ARCHITECTURE.md)
3. **Preview API**: Check [API_REFERENCE.md](./API_REFERENCE.md)
4. **Integration Examples**: See [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)
5. **Deployment Options**: Learn [DEPLOYMENT.md](./DEPLOYMENT.md)
6. **Give Feedback**: Discuss on [Discord](https://discord.gg/metaqore)
