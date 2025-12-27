# PSMP (Project State Management Protocol) - Implementation Summary

## Overview
Implemented the foundational PSMP infrastructure to enforce mandatory dependency declarations, automatic conflict detection, and project state governance.

## Files Created

### 1. Core PSMP Module (`core/psmp/`)
- **`__init__.py`**: Package entry point exposing main classes
- **`models.py`**: Data models for the PSMP
  - `DependencySpec`: Standard dependency declaration with scope, version, agent, and purpose
  - `DependencyConflict`: Represents detected conflicts with requirements and suggested resolutions
  - `ProjectArtifact`: Artifact metadata with attached dependencies
  - `PSMPEvent`: Immutable audit trail events (state transitions, conflicts, etc.)
  - Enums: `DependencyScope` (runtime/dev/build), `EventType` (10+ event types)

- **`dependency_resolver.py`**: Conflict detection and resolution logic
  - `VersionConstraintParser`: Parse and compare semantic version constraints
  - `DependencyConflictResolver`: Core resolver that
    - Registers dependencies from agents
    - Detects incompatibilities within and across scopes
    - Suggests resolution strategies (3+ per conflict)
    - Generates conflict-free manifests
  - Global getter: `get_dependency_resolver()`

- **`service.py`**: Core PSMP orchestration (`PSMPService`)
  - **State Machine Enforcement**: Valid transitions with logging
    - INITIALIZED → PLANNING → IN_PROGRESS → COMPLETED
    - Any state → BLOCKED ↔ IN_PROGRESS (after resolution) → ARCHIVED
  - **Mandatory Artifact Declaration**: 
    - `declare_artifact()` - Agent must declare artifacts with dependencies
    - Automatically triggers conflict detection
    - Projects auto-block if conflicts found
  - **Conflict Resolution**: 
    - `get_blocking_conflicts()` - Retrieve current blockers
    - `generate_conflict_report()` - Human-readable reports
    - `resolve_conflict_manual()` - Resolve by selecting version
  - **Unified Manifest**: Generate requirements.txt-ready output
  - **Audit Trail**: Event-sourced history with immutable `PSMPEvent` log
  - Global getter: `get_psmp_service()`

### 2. Conflict Resolver Agent (`agents/conflict_resolver_agent.py`)
- Specialized agent that
  - Analyzes blocked projects' dependency conflicts
  - Uses LLM to generate technical assessments
  - Suggests 2-3 resolution strategies per conflict
  - Provides risk assessments and implementation steps
- Output: Formatted resolution report with actionable recommendations
- Integrates with PSMP service to query and resolve conflicts

## Key Features

### 🔒 Mandatory Dependency Declarations
Agents **must** call `psmp.declare_artifact()` with dependencies; no artifact accepted without declarations.

### ⚡ Real-Time Conflict Detection
```python
# Agent generates code with pandas>=2.0
psmp.declare_artifact(
    project_id=1,
    agent_id="CoderAgent",
    artifact_type="code",
    content_summary="API server",
    dependencies=[
        DependencySpec(
            name="pandas",
            version_constraint=">=2.0",
            scope=DependencyScope.RUNTIME,
            declared_by_agent="CoderAgent",
            purpose="data processing"
        )
    ]
)

# Later, another agent declares pandas<2.0
# → Conflict detected immediately
# → Project transitions to BLOCKED
# → User gets clear report
```

### 🚫 Project Blocking
When conflicts detected:
- Project state → BLOCKED
- All workflow operations blocked
- Clear `ProjectBlockedException` raised with details
- Event logged with full context

### 📋 Conflict Reports
```json
{
  "project_id": 1,
  "status": "BLOCKED",
  "total_conflicts": 1,
  "conflicts": [
    {
      "library": "pandas",
      "requirements": [
        {"agent": "CoderAgent", "needs": ">=2.0", "purpose": "data processing"},
        {"agent": "DataScienceAgent", "needs": "<2.0", "purpose": "legacy model"}
      ],
      "severity": "critical",
      "suggested_resolutions": [
        "Update DataScienceAgent to support pandas 2.0",
        "Isolate legacy model in separate service",
        "Use compatibility layer between versions"
      ]
    }
  ]
}
```

### 🔄 State Machine Governance
- Valid transitions enforced
- All transitions logged with reasons
- Prevents invalid state combinations
- BLOCKED ↔ IN_PROGRESS only after conflict resolution

### 📝 Immutable Audit Trail
Every operation logged as `PSMPEvent`:
- Project created
- Artifact declared
- Conflict detected
- Project blocked/unblocked
- State transitions
- Conflict resolutions
- Fully queryable by project ID

## Integration Points

### With Orchestrator (`orchestration/orchestrator.py`)
```python
# In agent execution flow:
psmp = get_psmp_service()

# Before executing, check project state
if psmp.get_project_state(project_id) == "BLOCKED":
    raise ProjectBlockedException(...)

# After agent produces output:
success, artifact, conflicts = psmp.declare_artifact(
    project_id=project_id,
    agent_id=agent.name,
    artifact_type="code",
    content_summary=agent_output[:200],
    dependencies=extract_dependencies(agent_output)
)

if not success and conflicts:
    # Trigger ConflictResolverAgent
    resolver_result = orchestrator.run_conflict_resolution(project_id)
```

### With State Management (`core/state.py`)
- Uses existing StateManager for project storage
- Extends state with BLOCKED status
- Coordinates with task/artifact tables

### With CLI
```bash
# Check project state
TerraQore show "My Project"  # Shows if BLOCKED

# View conflicts
TerraQore conflicts "My Project"

# Trigger resolver agent
TerraQore resolve-conflicts "My Project"

# Once resolved
TerraQore unblock-project "My Project"
```

## Next Actions

1. **Integrate with Orchestrator**:
   - Call `psmp.declare_artifact()` after each agent execution
   - Handle `ProjectBlockedException` gracefully
   - Trigger `ConflictResolverAgent` on conflicts

2. **CLI Commands**:
   - `TerraQore conflicts <project>` - Show blocking conflicts
   - `TerraQore resolve-conflicts <project>` - Run resolver agent
   - `TerraQore manifest <project>` - Export unified dependencies

3. **UI Integration** (ref0006):
   - Display BLOCKED state prominently
   - Show conflict report with visualization
   - Provide "Run Resolver" button

4. **Testing** (ref0002):
   - Add unit tests for resolver logic
   - Integration tests for declare_artifact flow
   - Test state transition validity

---

✅ **PSMP infrastructure complete.** Ready for orchestrator integration and CLI hookup.
