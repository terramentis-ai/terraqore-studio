# TERRAQORE v1.0 - Complete System Startup Guide

## ✅ System Status: READY FOR TESTING

All 6 tasks have been successfully implemented and integrated:
- ✅ Task 1: Multi-Agent Orchestration System
- ✅ Task 2: Agent Specialization Router
- ✅ Task 3: Project & Workflow Management
- ✅ Task 4: Test Generation & Code Critique
- ✅ Task 5: Model Registry & Performance Analytics
- ✅ Task 6: Self-Marketing & Attribution Layer

## Prerequisites

### Backend
- Python 3.9+
- FastAPI
- Required packages (see `core_clli/requirements.txt`)

### Frontend
- Node.js 18+
- npm or yarn
- Vite build tool

## Step 1: Verify Python Environment

```bash
# Navigate to backend
cd c:\Users\user\Desktop\TERRAQORE_v1.0_pre_release\core_clli

# Check Python version
python --version  # Should be 3.9+

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Start Backend API

```bash
# From core_clli directory
python backend_main.py

# Expected output:
# INFO: Uvicorn running on http://localhost:8000
# INFO: FastAPI app started with all routers registered
```

The FastAPI server will:
- Initialize SQLite databases for attribution and state management
- Register all 4 router groups:
  - `/api/projects/*` - Project management
  - `/api/tasks/*` - Task execution
  - `/api/workflows/*` - Workflow orchestration
  - `/api/task6/*` - Self-marketing & attribution

**Verify Backend Health:**
```bash
curl http://localhost:8000/docs  # OpenAPI documentation
curl http://localhost:8000/api/projects/list  # Should return empty list or existing projects
```

## Step 3: Install & Build Frontend

```bash
# Navigate to GUI
cd c:\Users\user\Desktop\TERRAQORE_v1.0_pre_release\gui

# Install dependencies
npm install

# Start development server
npm run dev

# Expected output:
# VITE v5.x.x  ready in XXX ms
# ➜  Local:   http://localhost:5173/
# ➜  press h to show help
```

## Step 4: Access Application

Open your browser:
```
http://localhost:5173
```

You should see the TERRAQORE Studio interface with:
- Left sidebar with 7 navigation tabs
- Main content area (starts with Project Workspace)
- Settings and configuration panels

## Testing Flow

### Phase 1: Verify Existing Functionality (Tasks 1-5)

Navigate through tabs:

1. **Project Workspace** (W)
   - Create a new project
   - Set project details
   - Verify database persistence

2. **Workflow Playground** (P)
   - Execute sample workflows
   - Check agent execution logs
   - Verify agent specialization routing

3. **Mission Dashboard** (D)
   - View execution metrics
   - Check agent performance
   - Monitor system health

4. **Resources Registry** (R)
   - View available models
   - Check tool availability
   - Verify model switching

5. **Task History** (H)
   - View executed tasks
   - Check workflow results
   - Verify task persistence

### Phase 2: Test Task 6 Features

1. **Navigate to Project Gallery** (G)
   - Click "G" icon in left sidebar
   - Should load "Project Gallery" view

2. **View Projects with Achievements**
   - See all created projects
   - View achievement badges (🏆, 🚀, etc.)
   - Check total points calculation

3. **Test Sorting**
   - Sort by Completion % (highest first)
   - Sort by Points (most achievements)
   - Sort by Recent (most updated)

4. **Project Details Modal**
   - Click on any project card
   - View full statistics
   - See achievement breakdown

5. **Export Projects**
   - Click export button in modal
   - Verify JSON download works
   - Check data integrity

### Phase 3: API Testing

Test Task 6 endpoints directly:

```bash
# 1. Attribute code artifact
curl -X POST http://localhost:8000/api/task6/attribute-code \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_name": "test_feature.py",
    "artifact_type": "PYTHON_MODULE",
    "project_id": "test_proj_1",
    "attribution_level": "GENERATED",
    "description": "Test Python module"
  }'

# 2. Get project attributions
curl http://localhost:8000/api/task6/project-attributions/test_proj_1

# 3. Check achievement
curl -X POST http://localhost:8000/api/task6/check-achievement \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "test_proj_1",
    "achievement_type": "PROJECT_CREATED",
    "context": {}
  }'

# 4. Get achievements
curl http://localhost:8000/api/task6/project-achievements/test_proj_1

# 5. Export project
curl -X POST http://localhost:8000/api/task6/export-project \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "test_proj_1",
    "format": "MARKDOWN"
  }'

# 6. Get full summary
curl http://localhost:8000/api/task6/project-summary/test_proj_1
```

## Complete Workflow Test (5 minutes)

1. **Create Project**
   - Tab: Project Workspace
   - Click "Create New Project"
   - Fill in: Name, Description, Language
   - Click Create

2. **Execute Workflow**
   - Tab: Workflow Playground
   - Select created project
   - Run "Code Generation" workflow
   - Check completion

3. **View Results**
   - Tab: Mission Dashboard
   - Verify workflow completed successfully
   - Check agent execution logs

4. **Check Achievements**
   - Tab: Project Gallery
   - Find your project in the gallery
   - Verify it shows "PROJECT_CREATED" badge (🎯)
   - Points should show ≥10

5. **Export Project**
   - Click on project card
   - Click "Export Project" button
   - Select "MARKDOWN" format
   - Download should work

## Expected Behavior

### Success Indicators

✅ **Backend Startup**
- No errors or exceptions
- All routers registered
- Database files created (if not exists)
- API docs accessible at `/docs`

✅ **Frontend Startup**
- No console errors
- All tabs render correctly
- Navigation works smoothly
- Gallery component loads without errors

✅ **Project Creation**
- New projects appear in workspace
- Data persists after refresh
- Achievements auto-awarded

✅ **Gallery Display**
- Projects appear with cards
- Achievement badges visible
- Statistics calculated correctly
- Sorting filters work

✅ **API Integration**
- All 6 endpoints respond with 200 status
- Data formats match Pydantic models
- Error handling returns appropriate status codes

## Troubleshooting

### Backend Won't Start

```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <PID> /F

# Restart backend
python backend_main.py
```

### Frontend Build Issues

```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and lock file
rmdir /s /q node_modules
del package-lock.json

# Reinstall
npm install
npm run dev
```

### Import Errors in Backend

```bash
# Ensure core_clli is in Python path
# The backend_main.py should handle this

# Or manually add to Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/core_clli"
python backend_main.py
```

### Gallery Component Not Loading

1. Check browser console for errors (F12)
2. Verify ProjectGallery.tsx syntax
3. Check API endpoint responds: `curl http://localhost:8000/api/projects/list`
4. Clear browser cache and refresh

## Key Files for Task 6

- **Backend Systems**
  - `core_clli/core/attribution_system.py` - Code attribution tracking
  - `core_clli/core/achievement_system.py` - Achievement management
  - `core_clli/core/export_system.py` - Multi-format export
  - `terraqore_api/routers/task6_marketing.py` - REST API endpoints

- **Frontend**
  - `gui/components/ProjectGallery.tsx` - Gallery UI component
  - `gui/types.ts` - Updated with Tab.GALLERY
  - `gui/App.tsx` - Updated with gallery routing

- **Documentation**
  - `TASK_6_IMPLEMENTATION.md` - Comprehensive implementation guide

## Next Steps After Testing

1. **Performance Optimization**
   - Profile database queries
   - Optimize React component rendering
   - Add caching for frequently accessed data

2. **Feature Expansion**
   - Add more achievement types
   - Implement sharing functionality
   - Add analytics dashboard

3. **Production Deployment**
   - Set up CI/CD pipeline
   - Configure environment variables
   - Deploy to cloud infrastructure

4. **Documentation**
   - Create user guide
   - Write API reference
   - Add video tutorials

## Contact & Support

For issues or questions:
1. Check `TASK_6_IMPLEMENTATION.md` for detailed documentation
2. Review error logs in browser console and backend terminal
3. Verify all dependencies are installed correctly

---

**Status**: ✅ System Ready for Testing
**Last Updated**: 2024-12-19
**Version**: TERRAQORE v1.0 Pre-Release
