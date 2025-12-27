# Test Critique Agent - Implementation Summary

## Overview
Implemented a comprehensive test analysis and generation system that analyzes Python codebases using AST parsing and generates test recommendations and scaffolds.

## Components Created

### 1. Codebase Analyzer (`tools/codebase_analyzer.py`)
**Purpose**: Analyze Python projects to identify code structure and complexity

**Key Classes**:
- `CodeElement`: Represents classes, functions, async functions with metadata
  - Attributes: name, type, line numbers, decorators, complexity score, docstring
- `CodebaseAnalysis`: Aggregated analysis results
  - Tracks: file count, class/function/import counts, per-file data
- `CodebaseAnalyzer`: Main analyzer using AST parsing
  - Methods:
    - `analyze()` - Full codebase analysis with exclusions
    - `_analyze_file()` - Single file analysis
    - `_estimate_complexity()` - Cyclomatic complexity estimation
    - `get_untested_coverage_areas()` - Identify untested high-complexity functions
    - `generate_coverage_report()` - Human-readable analysis report

**Features**:
- AST-based code analysis (no string parsing)
- Automatic cyclomatic complexity scoring
- Excludes common directories (venv, __pycache__, etc)
- Generates coverage reports with priority areas
- Identifies high-complexity functions needing test focus

### 2. Test Suite Generator (`tools/test_suite_generator.py`)
**Purpose**: Generate pytest-compatible test scaffolds and recommendations

**Key Classes**:
- `TestTemplate`: Stores and renders test code templates
- `TestSuiteGenerator`: Generates test files from analysis
  - Methods:
    - `generate_tests_for_file()` - Generate tests for specific source file
    - `generate_full_test_suite()` - Generate tests for entire project
    - `generate_critical_tests()` - Focus on high-complexity functions
    - `estimate_test_coverage()` - Coverage gap analysis
    - `_generate_class_tests()` - Class-specific test templates
    - `_generate_function_tests()` - Function-specific test templates

**Features**:
- Generates pytest-compatible test files
- Creates test fixtures and test classes
- Prioritizes high-complexity functions
- Identifies untested areas by complexity
- Provides actionable coverage estimates

### 3. Test Critique Agent (`agents/test_critique_agent.py`)
**Purpose**: AI agent that orchestrates codebase analysis and generates critique

**Key Class**:
- `TestCritiqueAgent(BaseAgent)`: Specialized agent for test analysis
  - Methods:
    - `validate_context()` - Ensure project_id or project_root provided
    - `execute()` - Main analysis workflow
    - `_generate_response()` - Build detailed critique response
    - `_build_critique()` - Format findings into actionable report

**Integration**:
- Extends `BaseAgent` with standard interface
- Registered in orchestrator during initialization
- Triggered by `TerraQore test-critique` CLI command
- Produces `test_critique` artifact types
- Can be called from orchestrator workflows

### 4. CLI Commands
**New command**: `TerraQore test-critique <project> [-o output]`

**Workflow**:
```bash
# Run test critique on project
TerraQore test-critique "My Project"

# Save report to file
TerraQore test-critique "My Project" -o tests/report.txt

# Outputs:
# - Code structure summary
# - High-complexity functions
# - Test coverage estimate
# - Untested areas by priority
# - Generated test file paths
# - Next steps for test implementation
```

## Key Features

### 📊 Codebase Analysis
- Scans Python files with AST parsing
- Identifies all classes, functions, imports
- Calculates cyclomatic complexity for each element
- Generates hierarchical file/function map

### 🎯 Priority-Based Testing
High-priority test areas identified by:
1. Cyclomatic complexity (>5 flagged as high-priority)
2. Public API (private functions deprioritized)
3. Lack of existing test coverage
4. Core business logic impact

### 🔧 Test Generation
Generated tests include:
- Test classes for each source class
- Test functions for public functions
- Fixture templates
- Edge case test marks for high-complexity functions
- Performance test placeholders
- TODO markers for test implementation

### 📈 Coverage Reporting
Reports include:
- Total function/class counts
- Complexity metrics by file
- Untested complexity breakdown
- Priority ranking of untested areas
- Test generation recommendations
- Actionable next steps

## Integration Points

### With Orchestrator
```python
# Agent registered in _register_agents()
from agents.test_critique_agent import TestCritiqueAgent
agent = TestCritiqueAgent(llm_client, verbose=True, retriever=retriever)
orchestrator.agent_registry.register(agent)

# Can be triggered from workflows
result = orchestrator.run_agent("TestCritiqueAgent", context)
```

### With CLI
```bash
# Standalone command
TerraQore test-critique "Project Name"

# Can be chained with other commands
TerraQore plan "Project" && TerraQore test-critique "Project"
```

### With PSMP
- Produces `test_critique` artifacts
- Artifact declaration includes analysis findings
- Can block project if coverage too low (future enhancement)

## Data Flow

```
Project Source Code
    ↓
CodebaseAnalyzer.analyze()
    ├─ Scan all Python files
    ├─ Parse AST for each file
    ├─ Extract classes/functions/imports
    └─ Calculate complexity metrics
    ↓
CodebaseAnalysis Results
    ├─ Per-file code elements
    ├─ Complexity scores
    └─ Structure hierarchy
    ↓
TestCritiqueAgent.execute()
    ├─ Format analysis results
    ├─ Identify untested areas
    ├─ Generate test templates
    └─ Create recommendations
    ↓
AgentResult
    ├─ Analysis report
    ├─ Priority areas
    ├─ Generated test files
    └─ Next steps
    ↓
User Reports / Test Generation
```

## Test Generation Example

### Input: Python source file
```python
class DataProcessor:
    def process_data(self, data: List[Dict]) -> Dict:
        # Complex logic with 6+ decision points
        pass
```

### Output: Generated test scaffold
```python
class TestDataProcessor:
    @pytest.fixture
    def setup(self):
        instance = DataProcessor()
        yield instance
    
    def test_initialization(self, setup):
        assert setup is not None
    
    @pytest.mark.priority("high")
    def test_process_data_edge_cases():
        """Test edge cases for process_data (complexity: 6)."""
        # TODO: Add edge case tests
        pass
    
    @pytest.mark.priority("high")
    def test_process_data_performance():
        """Test performance of process_data."""
        # TODO: Add performance test
        pass
```

## CLI Output Example

```
🧪 Test Critique for: MyProject

📊 CODEBASE ANALYSIS REPORT
============================================================

📁 Files: 24
🏛️  Classes: 8
🔧 Functions: 156
📦 Imports: 42

⚠️  HIGH COMPLEXITY FUNCTIONS (>5):
  • src/core/orchestrator.py:312 - run_agent() (complexity: 8)
  • src/agents/base.py:45 - execute() (complexity: 7)
  • src/core/state.py:120 - create_project() (complexity: 6)

🧪 TEST COVERAGE ASSESSMENT
============================================================

Total Functions: 156
Total Complexity: 487
Test Files: 3 test files found

🔴 HIGH PRIORITY TEST AREAS:
  1. src/core/orchestrator.py
  2. src/agents/base.py
  3. src/core/state.py

⚠️  UNTESTED COMPLEXITY BY FILE:
  • src/core/orchestrator.py: 85
  • src/core/state.py: 72
  • src/agents/base.py: 64

🎯 Generated 3 critical test files:
  • test_orchestrator_critical.py
  • test_base_critical.py
  • test_state_critical.py

🚀 NEXT STEPS
============================================================
1. Review high-priority test areas above
2. Run: TerraQore generate-tests <project>  # Generate test scaffold
3. Implement specific test logic in generated files
4. Run tests: pytest tests/
5. Monitor coverage with: TerraQore test-coverage <project>
```

## Next Actions

1. **Test Generation Integration**:
   - Add `TerraQore generate-tests <project>` to apply scaffolds
   - Auto-create `tests/` directory structure
   - Handle existing test files gracefully

2. **Coverage Monitoring**:
   - Add `TerraQore test-coverage <project>` command
   - Calculate actual coverage from pytest runs
   - Track coverage trends over time

3. **Intelligent Test Writing**:
   - Use LLM to fill in test implementations
   - Learn from existing tests in project
   - Suggest specific assertions based on code

4. **CI/CD Integration**:
   - Run test critique in CI pipeline
   - Fail build if coverage too low
   - Generate coverage reports as artifacts

5. **Advanced Analysis**:
   - Branch coverage estimation
   - Data flow analysis for test case generation
   - Mutation testing for test quality assessment

---

✅ **Test Critique Agent complete.** Ready for: Test generation automation, coverage tracking, and intelligent test implementation via LLM.
