# Workflow Playground Guide

## Overview

The **Workflow Playground** is an interactive environment for designing and visualizing AI agent workflows in real-time. Similar to Google AI Studio or OpenAI Playground, it provides a user-friendly interface for submitting tasks and monitoring their execution across a multi-agent system.

## Accessing the Playground

1. Launch the TerraQore Studio application
2. Click the **P** icon in the left navigation sidebar
3. The Playground panel will load with three main sections: Input, Visualization, and Details

## Features

### 1. Workflow Prompt Input

**Location:** Top-left panel

Enter natural language descriptions of tasks you want your agent cluster to execute:

```
Examples:
- "Analyze the latest market trends in tech stocks"
- "Generate a Python script to process CSV files"
- "Research competitors in the SaaS space and create a comparison"
```

**Controls:**
- **Textarea:** Multi-line input field for detailed prompts
- **Execute Workflow Button:** Submit the prompt to the agent cluster
  - Displays `▶ Execute Workflow` when ready
  - Shows `⚙ Executing...` with spinner while processing
  - Disabled during execution or with empty prompt

### 2. Execution Statistics

**Location:** Below input area

Real-time metrics showing workflow progress:

| Metric | Description |
|--------|-------------|
| **Total** | Total number of steps in the workflow |
| **Completed** | ✓ Steps successfully finished |
| **Running** | ⚙ Steps currently executing |
| **Failed** | ✕ Steps that encountered errors |
| **Idle** | ○ Steps waiting to execute |

### 3. Execution Flow Visualization

**Location:** Left panel, main area

Visual representation of all workflow steps in order:

#### Step Status Indicators

Each step displays:
- **Status Icon** (left): Visual indicator of current state
  - `○` = Idle
  - `◉` = Thinking
  - `⚙` = Executing
  - `✓` = Completed
  - `✕` = Failed

- **Step Name**: Agent-assigned task name
- **Step Info**: Sequential number and agent type
- **Status Badge** (right): Current execution status

#### Color Coding

Steps are color-coded by status:
- 🟢 **Green** (`bg-emerald-500/20`): Completed successfully
- 🔵 **Blue** (with pulse): Currently executing or thinking
- 🔴 **Red** (`bg-red-500/20`): Execution failed
- ⚪ **Gray** (`bg-zinc-800/50`): Idle/pending

#### Interaction

- **Click** any step to view detailed information in the right panel
- **Scroll** through large workflows with smooth scrolling
- **Hover** for visual feedback

### 4. Step Details Inspector

**Location:** Right panel, top section

When you click a workflow step, detailed information appears:

#### Step Header
- **Step Name** with color-coded indicator
- **Status Badge**: Current execution state
- **Agent Type**: Which agent handled this step

#### Output Section
- **Output Display**: Full text output from the step
- **Scrollable**: For outputs longer than the panel
- **Syntax Highlighting**: Preserves formatting for code output
- **Empty State**: "No output available" message if step hasn't produced output yet

#### Metadata
- **ID**: Unique identifier of the step
- **Timestamp**: Exact execution time

### 5. Activity Log

**Location:** Right panel, bottom section

Real-time stream of agent communications (last 10 entries):

#### Log Entry Format

Each log shows:
- **Agent Name** (bold, uppercase)
- **Message** describing action or result
- **Timestamp** (local time)

#### Log Types

Logs are color-coded by type:
- 🟢 **Success** (green): Successful operations
- 🔵 **Info** (blue): Status updates and information
- 🟡 **Warning** (amber): Non-critical issues
- 🔴 **Error** (red): Failures and exceptions

#### Viewing History

- Scroll through past activity
- Most recent entries at the bottom
- Auto-scrolls during execution
- Shows up to 10 most recent entries

## Workflow Execution Example

### Step-by-Step Walkthrough

1. **Enter Prompt**
   ```
   "Analyze quarterly sales data and identify top-performing regions"
   ```

2. **Click Execute**
   - Prompt is submitted to the Meta-Controller
   - Button changes to "⚙ Executing..."
   - Statistics update in real-time

3. **Watch Execution**
   - Steps appear in the flow visualization
   - Each step transitions: Idle → Executing → Completed/Failed
   - Activity log updates with each agent action

4. **Inspect Results**
   - Click on "Data Analysis" step
   - View detailed output in the right panel
   - Check timestamp and agent information

5. **Execution Complete**
   - All steps reach "Completed" status
   - Statistics show 100% progress
   - Ready for new prompt

### Example Workflow Breakdown

For the prompt: "Generate a report on market opportunities"

```
Meta Control System (Root)
├── Researcher: Research market trends
│   └── Output: Market analysis data
├── Analyst: Process and analyze data
│   └── Output: Statistical insights
├── Engineer: Generate visualizations
│   └── Output: Chart/graph code
└── Reviewer: QA check results
    └── Output: Approval status
```

## Advanced Usage

### Monitoring Large Workflows

For complex workflows with many steps:
1. Use statistics to track overall progress
2. Scroll through steps to find bottlenecks
3. Click failing steps to debug issues
4. Check activity log for error messages

### Understanding Agent Types

The playground displays workflow steps by agent type:
- **Meta-Controller**: Orchestration and task decomposition
- **Orchestrator**: Sub-task coordination
- **Researcher**: Information gathering and analysis
- **Engineer**: Code generation and execution
- **Data Analyst**: Numerical analysis and insights
- **Quality Assurance**: Validation and verification
- **Execution Engine**: Technical implementation

### Debugging Failed Steps

When a step fails (red status):
1. Click the failed step
2. Read the output in the details panel
3. Check the activity log for error messages
4. Modify your prompt to address the issue
5. Execute a new workflow

### Comparing Multiple Executions

1. Execute a workflow
2. Document results by taking notes
3. Modify the prompt
4. Execute again
5. Compare step outputs side-by-side

## Tips & Tricks

### Prompt Engineering

- **Be specific**: "Find 3 competitors" vs "Find competitors"
- **Provide context**: "For the SaaS industry" vs no context
- **Set expectations**: "Create a 500-word summary" with length
- **Request format**: "As a markdown table" or "As JSON"

### Performance

- Large workflows may take time to render
- Start with simpler prompts if you encounter lag
- The playground handles 50+ steps smoothly
- Complex outputs scroll for readability

### Reading Logs

- Watch the activity log for execution order
- Look for warnings before errors
- System messages indicate overall progress
- Agent names show who performed each action

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+Enter` | Submit workflow (if textarea focused) |
| Scroll | Navigate through steps and logs |
| Click | Select step for inspection |

## Troubleshooting

### Workflow Won't Execute
- Ensure prompt is not empty
- Check that server is running
- Look for error messages in activity log

### No Output Shown
- Step may still be executing (wait for completion)
- Some intermediate steps may not produce output
- Check the step details panel for metadata

### Slow Performance
- Large workflows may take time to render
- Try simpler prompts first
- Check browser console for errors
- Restart the application if needed

### Steps Appear Idle
- They may be queued waiting for dependencies
- Check activity log for execution order
- Some steps execute in parallel

## Comparison to Similar Tools

### vs Google AI Studio
- ✓ Multi-agent orchestration (not just LLM)
- ✓ Hierarchical task decomposition
- ✓ Custom agent types and workflows
- ○ Simpler prompt engineering (similar)

### vs OpenAI Playground
- ✓ Multi-step workflow support
- ✓ Real-time agent communication visibility
- ✓ Specialized agent roles
- ○ Parameter tuning (OpenAI more advanced)

## Best Practices

1. **Start Simple**: Test with basic prompts before complex workflows
2. **Monitor Execution**: Watch the flow to understand agent interaction
3. **Inspect Details**: Click steps to understand intermediate results
4. **Review Logs**: Check activity log to troubleshoot issues
5. **Iterate**: Refine prompts based on results

## Keyboard & Accessibility

- Full keyboard navigation support
- Screen reader compatible
- High contrast color scheme
- Clear visual feedback on interactions

---

For more information, see the main [README.md](../README.md)
