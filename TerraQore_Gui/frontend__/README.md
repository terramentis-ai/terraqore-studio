<div align="center">
  <h1>TerraQore Studio</h1>
  <p>A modern UI for designing, executing, and visualizing multi‑agent AI workflows.</p>
</div>

## Overview
- Playground‑first experience: design and run workflows with real‑time visualization.
- Multi‑agent orchestration with status, logs, and step outputs.
- Clean, responsive layout with collapsible panels and smooth scrolling.
- Built with React + Vite + D3.

## Features
- **Workflow Playground:** main landing page for prompt‑driven executions.
- **Realtime Logs:** stream agent activity with status coloring.
- **Step Details:** inspect outputs, metadata, and timestamps.
- **Mission Dashboard:** overview metrics and active tasks.
- **Models & Tools:** enable/disable tools like Google Search and Code Interpreter.
 - **Deploy / Export:** quick actions to Deploy to AgentsHub, Export to GitHub, and Download artifacts.

## Quick Start

Prerequisites: Node.js 18+

```bash
# Install deps
npm install

# Configure environment
# Create .env.local and add your Gemini API key
# VITE_GEMINI_API_KEY=your_api_key_here

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Configuration
- Environment: set `VITE_GEMINI_API_KEY` in `.env.local`.
- Rate limiting: icon generation is serialized to avoid 429s.
- Styling: Tailwind utility classes applied across views.

## Project Structure
```
metaagent-framework-ui/
├── components/
│   ├── Playground.tsx       # Primary workflow playground UI
│   ├── Dashboard.tsx        # Mission analytics
│   ├── ModelsAndTools.tsx   # Registry & tool toggles
│   ├── Terminal.tsx         # Activity log stream
│   └── AgentFlow.tsx        # (Muted) legacy topology view
├── services/
│   └── geminiService.ts     # Gemini integration
├── App.tsx                  # App shell & navigation
├── types.ts                 # Types and enums
├── constants.ts             # Colors & initial nodes
├── index.tsx                # React entry
└── vite.config.ts           # Vite config
```

## Usage
- Open the app and you’ll land on the **Workflow Playground**.
- Enter a prompt (e.g., "Analyze Q4 sales and summarize top regions").
- Click **Execute Workflow** to run.
- Monitor steps, click any to inspect details under the prompt; view output in the **Preview Console** panel.

## Notes
- The legacy topology cluster workspace is muted; the Playground is the default.
- Large outputs and long workflows are scrollable; use the Preview toggle on smaller screens.

## Troubleshooting
- If the UI doesn’t scroll: ensure you’re on the latest build; the layout uses `overflow-auto` and `min-h-0` for all key flex containers.
- If requests fail: verify `VITE_GEMINI_API_KEY` and network access.

## License
MIT
<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# TerraQore Studio - AI Agent Framework UI

A powerful visualization and orchestration platform for multi-agent AI workflows. Featuring real-time monitoring, workflow design, and execution playground.

> Note: The Workflow Playground is now the primary landing experience. The legacy topology cluster view is muted for this release.

View your app in AI Studio: https://ai.studio/apps/drive/1wyiQouM7s2Ln4_Zppt_0GfDygAT-4EW8

## Features

### 🎯 **Workspace**
- Real-time D3.js visualization of agent execution flows
- Interactive node-based workflow representation
- Support for multiple agent types with dynamic icons
- Drag-and-drop node manipulation
- Real-time status tracking and updates

### 🎮 **Workflow Playground**
- Interactive workflow design and execution environment
- Prompt-based task submission with instant feedback
- Visual execution flow tracking with step-by-step visualization
- Real-time agent communication logs
- Step details panel with output inspection
- Execution statistics (Total, Completed, Running, Failed, Idle)
- Similar to Google AI Studio and OpenAI Playground

### 📊 **Mission Dashboard**
- Comprehensive execution metrics
- Agent communication analytics
- Job progress tracking
- Active task monitoring
- Real-time convergence visualization

### 📦 **Resources Registry**
- Models and tools configuration
- Enabled tools management
- System resource monitoring

### 🔧 **System Settings**
- Configuration management
- Advanced options

## Installation & Setup

**Prerequisites:** Node.js (v16+)

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure API Key:**
   Set the `GEMINI_API_KEY` in [.env.local](.env.local) with your Gemini API key:
   ```
   VITE_GEMINI_API_KEY=your_api_key_here
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   ```

4. **Build for production:**
   ```bash
   npm run build
   ```

## Project Structure

```
metaagent-framework-ui/
├── components/
│   ├── AgentFlow.tsx          # D3.js workflow visualization
│   ├── AgentDetails.tsx        # Node detail panel
│   ├── ControlPanel.tsx        # Execution control interface
│   ├── Dashboard.tsx           # Mission analytics dashboard
│   ├── ModelsAndTools.tsx      # Resource registry
│   ├── Terminal.tsx            # Real-time activity log
│   └── Playground.tsx          # 🆕 Workflow playground with visualization
├── services/
│   └── geminiService.ts        # Gemini API integration
├── App.tsx                     # Main application component
├── types.ts                    # TypeScript type definitions
├── constants.ts                # Configuration constants
├── index.tsx                   # React entry point
└── vite.config.ts             # Vite build configuration
```

## Playground Features

### Workflow Execution
- Enter natural language prompts describing your AI task
- Real-time execution monitoring with visual feedback
- Support for complex multi-agent workflows

### Execution Flow Visualization
- Step-by-step task breakdown
- Color-coded status indicators:
  - 🟢 Completed (Green)
  - 🔵 Running/Executing (Blue with pulse animation)
  - 🔴 Failed (Red)
  - ⚪ Idle/Pending (Gray)

### Step Details Inspector
- View detailed output for each workflow step
- Metadata including step ID and execution timestamp
- Agent type and status information
- Real-time log stream of all agent communications

### Statistics Dashboard
- Total workflow steps count
- Completion metrics
- Execution time tracking
- Error monitoring

## Architecture

### State Management
- React hooks with centralized MetaState
- Real-time node updates and synchronization
- Execution log streaming

### Visualization
- D3.js for hierarchical workflow graphs
- Interactive zoom and pan controls
- Draggable nodes for workflow exploration
- Dynamic icon generation via Gemini Vision API

### AI Integration
- Gemini API for:
  - Agent icon generation
  - Workflow orchestration
  - Tool execution
  - Code generation and execution

## Usage Examples

### Running a Basic Workflow
1. Navigate to the **Workflow Playground** tab
2. Enter a prompt: "Analyze sales data from Q4 and generate a report"
3. Click "Execute Workflow"
4. Monitor agent execution in real-time
5. Click any step to view detailed output

### Monitoring Execution
- Use the **Mission Dashboard** for high-level metrics
- Check the **Realtime Stream** for detailed logs
- Inspect individual agent outputs via the Workspace

### Customizing Tools
1. Go to **Resources Registry**
2. Toggle required tools (Google Search, Code Interpreter, etc.)
3. Changes apply to subsequent executions

## Technologies

- **Frontend:** React 18 + TypeScript
- **Visualization:** D3.js v7
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **AI:** Google Gemini API
- **State:** React Hooks

## Development

### Hot Module Replacement
```bash
npm run dev
```

### Type Checking
TypeScript is configured for strict mode. Check types with:
```bash
npx tsc --noEmit
```

### Environment Variables
Create `.env.local`:
```
VITE_GEMINI_API_KEY=your_api_key_here
```

## API Integration

The application integrates with Google's Gemini API for:
- Multi-agent orchestration
- Dynamic icon generation
- Tool execution and code interpretation
- Real-time task decomposition

## Performance Considerations

- Rate limiting: Icon generation requests are serialized (200ms delay between requests)
- Virtual scrolling for large execution logs
- Memoized computations for workflow statistics
- D3.js optimization for large node graphs

## Contributing

1. Create a feature branch
2. Make changes in components or services
3. Test locally with `npm run dev`
4. Build and verify with `npm run build`

## License

MIT License - See LICENSE file for details
