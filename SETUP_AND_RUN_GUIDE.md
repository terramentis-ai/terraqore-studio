# FlyntCore v1.0 - Complete Setup & Run Guide

## System Overview

FlyntCore is a comprehensive **Personal Developer Assistant for Agentic AI Projects** consisting of:

1. **FastAPI Backend** (`core_clli/`) - Multi-agent orchestration, PSMP dependency management, test critique
2. **React Frontend** (`gui/`) - Flynt Studio UI with project/task management, workflow execution
3. **Integration Bridge** - Full REST API connecting frontend to backend

## Prerequisites

### Python Environment
- Python 3.10+
- pip package manager

### Node.js Environment  
- Node.js 18+ or better
- npm package manager

## Part 1: Backend Setup (FastAPI)

### Step 1: Navigate to backend directory
```bash
cd core_clli
```

### Step 2: Create and activate virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure settings (optional)
```bash
# Check default settings
cat config/settings.yaml

# To customize, edit config/settings.yaml
```

### Step 5: Start the FastAPI server
```bash
python backend_main.py
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

The backend will:
- Initialize the PSMP (Project State Management Protocol) system
- Create SQLite database for state persistence
- Start REST API endpoints at `http://localhost:8000`
- Enable Swagger docs at `http://localhost:8000/docs`

## Part 2: Frontend Setup (React)

### Step 1: Open new terminal and navigate to GUI
```bash
cd gui
```

### Step 2: Install dependencies
```bash
npm install
```

### Step 3: (Optional) Configure API endpoint
```bash
# Create .env.local file
echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local

# Default is http://localhost:8000, override as needed
```

### Step 4: Start the development server
```bash
npm run dev
```

**Expected output:**
```
  VITE v4.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

### Step 5: Open in browser
Navigate to `http://localhost:5173/` - you should see Flynt Studio

## Part 3: Using Flynt Studio

### Initial Navigation

1. **Workspace Tab** (default)
   - View all projects
   - Create new projects
   - Click "View Details" to manage individual projects

2. **Playground Tab**
   - Free-form prompt-based orchestration
   - Type objective and hit "Execute"
   - Watch agents work in real-time
   - View execution logs

3. **Dashboard Tab**
   - System analytics and metrics
   - Execution history
   - Performance insights

4. **Models & Tools Tab**
   - Toggle available tools
   - View active capabilities
   - Manage integrations

## Part 4: Complete Workflow Example

### Create Your First Project

```
1. Click "WORKSPACE" tab in left sidebar
2. Click "+ New Project" button
3. Enter project name: "My First AI Project"
4. System creates project with database entry
5. Click "View Details" on the new project card
```

### Create Tasks

```
In Project Detail view:
1. Click "TASKS" tab
2. Click "+ New Task"
3. Add task:
   - Title: "Design System Architecture"
   - Priority: "HIGH"
   - Milestone: "Planning"
4. Click "Create"
```

### Execute Workflows

```
Back in Project Detail (Overview tab):
1. Click "💡 Ideate" to brainstorm ideas
2. Watch agents work in Terminal
3. Click "📋 Plan" to create detailed plan
4. Click "⚙️ Execute" for execution
5. Click "✓ Review" for quality check
```

### Monitor Execution

```
1. Terminal tab shows real-time logs
2. See which agents are working
3. View status transitions (THINKING → EXECUTING → COMPLETED)
4. Check for errors and warnings
```

### Resolve Conflicts

```
In Project Detail:
1. Click "CONFLICTS" tab
2. If conflicts exist (dependency mismatches)
3. Click "Suggest Resolution"
4. System recommends version updates
5. Apply resolution
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Flynt Studio (React)                  │
│  ProjectDashboard → ProjectDetail → Playground          │
│       ↓                ↓                ↓                │
│  [WORKSPACE]    [PROJECT MGMT]    [EXECUTION]           │
└────────────────────────┬──────────────────────────────────┘
                         │ HTTP REST API
                         ↓
┌─────────────────────────────────────────────────────────┐
│           FastAPI Backend (core_clli)                   │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Projects │  │  Tasks   │  │ Workflows│              │
│  │ Router   │  │  Router  │  │ Router   │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │             │             │                     │
│       └─────────────┴─────────────┘                     │
│                     ↓                                    │
│         ┌───────────────────────┐                       │
│         │  PSMP Orchestrator    │                       │
│         │  Agent Router         │                       │
│         │  Dependency Resolver  │                       │
│         └───────────┬───────────┘                       │
│                     ↓                                    │
│    ┌────────────────────────────────────┐              │
│    │    11 Specialized AI Agents        │              │
│    │  - Planner, Coder, Analyst, etc.  │              │
│    └────────────┬───────────────────────┘              │
│                 ↓                                        │
│    ┌────────────────────────────────────┐              │
│    │   SQLite State Database            │              │
│    │   - Projects, Tasks, Executions    │              │
│    └────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

## Troubleshooting

### Backend Won't Start
```bash
# Check Python version
python --version  # Should be 3.10+

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Try running with verbose output
python -u backend_main.py
```

### Frontend Won't Connect
```bash
# Check API endpoint is running
curl http://localhost:8000/health

# If not responding, restart backend:
# Ctrl+C in backend terminal
python backend_main.py

# Clear npm cache
npm cache clean --force
npm install

# Restart frontend
npm run dev
```

### Port Already in Use
```bash
# Backend (change port in backend_main.py)
# Or kill process using port 8000
# Windows: netstat -ano | findstr :8000
# macOS/Linux: lsof -i :8000

# Frontend (runs on 5173, usually available)
# Or configure in vite.config.ts
```

### Database Issues
```bash
# Reset database (delete SQLite file)
rm core_clli/*.db

# Restart backend - will recreate database
python backend_main.py
```

## API Documentation

While running backend, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These show all available endpoints with example requests.

## Key Endpoints

```
# Projects
POST   /projects          - Create project
GET    /projects          - List all projects
GET    /projects/{id}     - Get project details
PATCH  /projects/{id}     - Update project

# Tasks
POST   /projects/{id}/tasks          - Create task
GET    /projects/{id}/tasks          - List tasks
GET    /tasks/{id}                   - Get task details
PATCH  /tasks/{id}                   - Update task

# Workflows
POST   /projects/{id}/workflows/{type}  - Execute workflow
POST   /agents/{type}/execute           - Execute agent

# Conflicts
GET    /projects/{id}/conflicts        - Get conflicts
POST   /projects/{id}/conflicts/resolve - Resolve conflict
GET    /projects/{id}/manifest         - Get manifest
```

## Performance Tips

1. **Reduce AI Icon Generation**: Icons generate on startup; disable if slow
   - Comment out icon generation in App.tsx

2. **Database Optimization**: For many projects
   - Index frequently queried fields
   - Archive completed projects

3. **Frontend Bundling**: For production
   ```bash
   npm run build
   npm run preview
   ```

## Environment Variables

### Backend (core_clli/.env)
```
GOOGLE_API_KEY=your-key-here
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///flynt.db
```

### Frontend (gui/.env.local)
```
VITE_API_BASE_URL=http://localhost:8000
VITE_GOOGLE_API_KEY=your-key-here
```

## Next Steps

1. **Create sample projects** to understand workflows
2. **Execute different workflow types** (ideate, plan, execute, review)
3. **Monitor Terminal tab** to see agent interactions
4. **Explore Dashboard** for analytics
5. **Check Conflicts tab** for dependency management examples

## Support Resources

- **Backend Docs**: `core_clli/README.md`
- **Frontend Docs**: `gui/README.md`
- **API Implementation**: `FASTAPI_IMPLEMENTATION.md`
- **PSMP Spec**: `core_clli/PSMP_IMPLEMENTATION.md`
- **Test Critique**: `core_clli/TEST_CRITIQUE_IMPLEMENTATION.md`
- **Session Summary**: `SESSION_COMPLETION_SUMMARY.md`
- **Master Index**: `MASTER_INDEX.md`

## Quick Commands Reference

```bash
# Terminal 1: Start Backend
cd core_clli
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python backend_main.py

# Terminal 2: Start Frontend
cd gui
npm install  # first time only
npm run dev

# Browser: Open http://localhost:5173/
```

---

**FlyntCore v1.0** is now ready to use! Start in the WORKSPACE tab and create your first project.
