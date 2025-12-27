# Contributing to Flynt Studio

First off, thank you for considering a contribution to Flynt Studio! It's people like you that make Flynt such a great platform.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

## How Can I Contribute?

### **Reporting Bugs** 🐛

Before creating bug reports, please check the [issue list](../../issues) as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps which reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed after following the steps**
- **Explain which behavior you expected to see**
- **Include screenshots and animated GIFs if possible**
- **Include your environment details** (OS, Python version, etc.)

### **Suggesting Enhancements** ✨

Enhancement suggestions are tracked as [GitHub issues](../../issues). When creating an enhancement suggestion, please include:

- **A clear and descriptive title**
- **A step-by-step description of the suggested enhancement**
- **Specific examples to demonstrate the steps**
- **A description of the current behavior and expected behavior**
- **An explanation of why this enhancement would be useful**

### **Pull Requests** 🔄

- Fill in the required template
- Follow the Python [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Include appropriate test cases
- Update documentation as needed
- End all files with a newline

---

## Development Setup

### **Prerequisites**
- Python 3.9 or higher
- Git
- Virtual environment

### **Setup Steps**

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR-USERNAME/Flynt-Studio.git
   cd Flynt-Studio
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Additional dev dependencies
   ```

4. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## Testing

### **Run All Tests**
```bash
pytest tests/ -v
```

### **Run Specific Test File**
```bash
pytest tests/test_core_components.py -v
```

### **Run with Coverage**
```bash
pytest tests/ --cov=core --cov=agents --cov-report=html
```

### **Run Async Tests**
```bash
pytest tests/ -v -m asyncio
```

---

## Code Quality

### **Format Code**
```bash
black . --line-length=100
```

### **Check Linting**
```bash
flake8 . --max-line-length=100
```

### **Type Checking**
```bash
mypy core/ agents/ --ignore-missing-imports
```

### **All Quality Checks**
```bash
make lint  # or run all checks
```

---

## Commit Messages

Follow the conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### **Types**
- `feat:` A new feature
- `fix:` A bug fix
- `docs:` Documentation changes
- `style:` Code style changes (no functional changes)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Dependency updates, etc.

### **Example**
```
feat(monitoring): add health check endpoint for agents

Add new GET /health/agents endpoint to retrieve
agent health status including success rate and
execution times.

Closes #123
```

---

## Documentation

### **Update Docs When**
- Adding new features
- Changing behavior
- Fixing bugs that are documented
- Improving clarity

### **Documentation Format**
- Use Markdown
- Include code examples
- Keep sections logically organized
- Update table of contents if needed

---

## Pull Request Process

1. **Create a descriptive PR title** following commit message conventions
2. **Update relevant documentation** in `/docs`
3. **Add tests** for new functionality
4. **Run all tests locally** and ensure they pass
5. **Request review** from maintainers
6. **Address feedback** with additional commits
7. **Merge** once approved

### **PR Template**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] Added tests
- [ ] All tests pass
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes
```

---

## Style Guide

### **Python Style**
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints
- Write docstrings for classes and functions
- Keep lines under 100 characters

### **Docstring Format**
```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of function.
    
    Longer description if needed, explaining
    behavior and usage.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param validation fails
        
    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        True
    """
    pass
```

### **Comments**
```python
# Good: Explains WHY, not WHAT
# Retry with exponential backoff to handle rate limits
backoff_delay = retry_delay * (2 ** attempt)

# Bad: States obvious
# Set backoff_delay to retry_delay times 2 to the power of attempt
backoff_delay = retry_delay * (2 ** attempt)
```

---

## Project Structure

```
Flynt-Studio/
├── agents/                 # AI agent implementations
│   ├── base.py            # Base agent class
│   ├── *_agent.py         # Specialized agents
│   └── __init__.py
├── core/                  # Core platform services
│   ├── error_handler.py   # Error recovery system
│   ├── monitoring.py      # Health & metrics
│   ├── llm_client.py      # LLM provider integration
│   └── ...
├── orchestration/         # Workflow orchestration
│   ├── orchestrator.py    # Main orchestrator
│   └── executor.py        # Task execution
├── tools/                 # Utility tools
├── tests/                 # Test suite
├── docs/                  # Documentation
├── examples/              # Usage examples
└── scripts/               # Deployment scripts
```

---

## Key Directories to Know

- **`agents/`** - Where agent implementations go
- **`core/`** - Core platform functionality (don't modify lightly)
- **`tests/`** - All test files belong here
- **`docs/`** - Project documentation
- **`examples/`** - Usage examples for features

---

## Common Tasks

### **Adding a New Agent**
1. Create `agents/new_agent.py`
2. Extend `BaseAgent` class
3. Implement `get_system_prompt()` and `execute()`
4. Register in `orchestration/orchestrator.py`
5. Add tests in `tests/test_agents.py`

### **Adding a New Feature**
1. Create feature branch: `git checkout -b feature/name`
2. Implement feature with tests
3. Update documentation
4. Submit PR with clear description

### **Fixing a Bug**
1. Create bug-fix branch: `git checkout -b fix/bug-name`
2. Add regression test
3. Fix the bug
4. Verify all tests pass
5. Submit PR with link to issue

---

## Questions or Need Help?

- 📖 Check the [documentation](../docs/)
- 💬 Ask in [GitHub Discussions](../../discussions)
- 📧 Email: dev@flyntstudio.dev
- 🐛 Report bugs in [Issues](../../issues)

---

## Recognition

Contributors will be recognized in:
- Git commit history
- [CONTRIBUTORS.md](CONTRIBUTORS.md) file
- Release notes (if applicable)

---

**Thank you for contributing to Flynt Studio! 🎉**
