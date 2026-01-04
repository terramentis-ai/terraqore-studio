# TerraQore GUI Frontend

**React + TypeScript + Vite + TailwindCSS**

Modern web interface for TerraQore Studio and MetaQore governance engine.

⚠️ **IMPORTANT**: This is **Project #3** in a three-repo workspace. See `../WORKSPACE_ORGANIZATION.md` for the complete ecosystem structure.

---

## 🎯 Purpose

This is a **standalone React application** that provides a user-friendly interface for:
- Managing TerraQore projects and workflows
- Viewing artifacts and agent outputs  
- Monitoring MetaQore governance status
- Triggering multi-agent workflows
- Real-time updates via WebSocket (future)

**Repository**: To be created at `https://github.com/terramentis-ai/terraqore-gui.git`  
**Remote**: Will be named `frontend` once repo is created

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn

### Install
```bash
cd gui_simple
npm install
```

### Run Development Server
```bash
npm run dev
# Opens at http://localhost:5173
```

### Build for Production
```bash
npm run build
# Output in dist/
```

---

## 📁 Project Structure

```
gui_simple/
├── src/
│   ├── App.jsx           # Main TerraQoreOS component
│   ├── main.jsx          # React entry point
│   └── index.css         # Tailwind styles
├── index.html            # HTML template
├── package.json          # Dependencies
├── vite.config.js        # Vite configuration
├── tailwind.config.js    # Tailwind configuration
├── postcss.config.js     # PostCSS configuration
└── .gitignore           # Git ignore rules
```

## Getting Started

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The development server will start at `http://localhost:5173`

---

## 🔗 API Integration

This frontend calls two backend APIs:

### TerraQore API (http://localhost:8000)
```typescript
// Start a workflow
POST /api/workflows/run
{ project_id: "proj_123", workflow_type: "ideate" }

// List projects
GET /api/projects
```

### MetaQore API (http://localhost:8001)
```typescript
// List artifacts
GET /api/v1/artifacts?project_id=proj_123

// Check governance status
GET /api/v1/conflicts?project_id=proj_123
```

---

## 🔄 Git Workflow (IMPORTANT)

**This is a separate repository within the workspace.**

### Committing GUI Changes
```bash
# From workspace root
cd c:\Users\user\Desktop\terraqore_studio

# Stage ONLY gui_simple files
git add gui_simple/

# Commit with GUI scope
git commit -m "feat(ui): add project dashboard"

# Push to GUI remote (after repo created)
git push frontend master
```

### Creating the GUI Repository
```bash
# On GitHub, create: https://github.com/terramentis-ai/terraqore-gui

# Add remote
git remote add frontend https://github.com/terramentis-ai/terraqore-gui.git

# Push GUI changes
git push frontend master
```

**⚠️ NEVER mix GUI commits with TerraQore or MetaQore changes.**

---

## 🗑️ Deprecated: Streamlit UI

**`app.py` (Streamlit) is no longer maintained.**

- Old Streamlit UI served at port 8501
- Replaced by this React application  
- Do not use or extend Streamlit code

---

## Key Components

### TerraQoreOS Main Component
- Header with status indicator
- Hero section with CTAs
- Dashboard, AgentsHub, and Settings panels
- Active agent registry
- Interactive console interface
- Workflow execution with approval gates

### Interactive Features

1. **Panel Expansion**: Click dashboard cards to expand and see detailed features
2. **Console**: Toggle the TerraQore Console for interactive workflows
3. **Message Chat**: Send messages to simulate AI orchestration
4. **Workflow Approvals**: Approve or deny recommended workflows
5. **Real-time Status**: Live agent status indicators

## Customization

### Update Panels
Edit the `panels` array in `App.jsx` to customize dashboard cards.

### Add Agents
Modify the `agentTypes` array to add/remove agents from the registry.

### Styling
- Update `tailwind.config.js` for theme customization
- Modify `src/index.css` for global styles

---

## 📚 Documentation

- **Workspace Structure**: `../WORKSPACE_ORGANIZATION.md` ⚠️ READ THIS FIRST
- **TerraQore API**: `../docs/api_reference.md`
- **MetaQore API**: `../metaqore/API_REFERENCE.md`
- **Integration Guide**: `../TerraQore_vs_MetaQore.md`

---

## 💬 Questions?

**"Can I import TerraQore code?"** → NO. GUI is standalone. Use HTTP APIs only.  
**"Is this the same as Streamlit?"** → NO. Streamlit is deprecated.  
**"Which repo do I push to?"** → `frontend` remote (to be created)

---

**Last Updated**: January 4, 2026  
**Status**: Standalone React app, separate repo (to be created)

## Dependencies

- **react**: ^18.2.0 - UI library
- **react-dom**: ^18.2.0 - DOM rendering
- **lucide-react**: ^0.344.0 - Icon library
- **tailwindcss**: ^3.3.6 - Utility CSS
- **vite**: ^5.0.0 - Build tool

## Development

```bash
# Hot module replacement (HMR) is enabled by default
# Changes will automatically refresh in browser

# Linting (when configured)
npm run lint
```

## Production Build

```bash
npm run build
```

Creates optimized build in `dist/` directory ready for deployment.

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile browsers (iOS Safari, Chrome Android)

## License

© 2026 TerraQore Studio - All rights reserved
