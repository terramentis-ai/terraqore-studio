# Changelog

All notable changes to FlyntCore are documented in this file.

## [1.0.0] - 2025-12-26

### Added
- **Multi-Provider LLM Support**: Seamless integration with Gemini, Groq, OpenRouter, and local Ollama
- **Backend LLM Abstraction Layer**: Unified API endpoints for chat, task planning, and agent execution
- **Frontend Provider-Agnostic Architecture**: Decoupled from Gemini SDK; routes all LLM calls through backend API
- **Production-Grade Error Handling**: React ErrorBoundary component prevents blank screens; comprehensive logging
- **Settings UI Enhancements**: Provider descriptions, setup instructions, and connection status indicators
- **GitHub Actions CI/CD**: Automated testing and building for backend and frontend
- **Docker Support**: Dockerfile for API containerization
- **Multi-Agent System**: Specialized agents (Researcher, Engineer, Data Analyst, QA) with role-specific prompts
- **Task Planning**: Meta-Controller generates structured JSON plans with subtasks
- **Real-Time Collaboration**: WebSocket support for live updates and collaboration

### Changed
- **Frontend Service Layer**: Complete rewrite to use backend API instead of direct SDK calls
- **Backend Configuration**: Settings now use environment variables for API keys to prevent credential leaks
- **Default Ollama Model**: Updated from `llama3.2` to `phi3` for better performance on local systems
- **API Response Format**: Fixed inconsistencies in project list endpoint to support both array and object shapes

### Fixed
- **UI Blank Screen Issue**: Added ErrorBoundary and improved API client resilience
- **Meta-Controller Failures**: Non-existent Gemini model names replaced with valid models
- **Backend Startup**: Fixed Depends() usage in setup functions to work with direct initialization
- **Health Check Timeouts**: Wrapped health checks with timeout handling to prevent blocking startup

### Security
- **Removed Exposed API Keys**: Replaced hardcoded credentials with environment variable configuration
- **Sensitive Data Protection**: Excluded config files with secrets from git via .gitignore
- **Example Configuration**: Created settings.example.yaml template for safe configuration setup

### Deployment
- **Build Scripts**: Added build.sh and build.ps1 for streamlined project building
- **Start Scripts**: Added start.sh and start.ps1 for easy local development setup
- **GitHub Actions Workflows**: 
  - Backend testing on Python 3.9, 3.10, 3.11
  - Frontend building on Node 16, 18, 20
  - Release automation with artifact uploads
  - Optional GitHub Pages deployment

### Documentation
- **SETUP_AND_RUN_GUIDE.md**: Comprehensive installation and configuration instructions
- **System Architecture**: Clear separation of concerns between frontend, backend, and LLM providers
- **API Documentation**: FastAPI /docs endpoint with interactive Swagger UI
- **Environment Configuration**: Detailed guide for setting up providers locally and online

## [0.9.0] - Pre-release
- Initial development version with MVP features
- Basic multi-agent system
- Gemini SDK integration (later migrated to backend abstraction)

---

## Version History

### v1.0.0
- **Release Date**: December 26, 2025
- **Type**: Major Release
- **Status**: Production Ready
- **Breaking Changes**: 
  - Frontend now requires backend to be running for all LLM operations
  - API key configuration moved to environment variables (removed from settings.yaml)

### Upgrade Guide from v0.9.0
1. Back up your current `settings.yaml` if customized
2. Copy `settings.example.yaml` to `settings.yaml`
3. Set environment variables for your LLM providers:
   ```bash
   export GEMINI_API_KEY=your_key
   export GROQ_API_KEY=your_key
   export OPENROUTER_API_KEY=your_key
   ```
4. Restart both backend and frontend services
5. Configure LLM provider in Settings UI (no code changes needed to switch providers)

## Future Roadmap

### v1.1.0 (Q1 2026)
- [ ] Database persistence for workflows and executions
- [ ] Advanced analytics dashboard
- [ ] Support for more LLM providers (Claude, Llama Cloud)
- [ ] Batch processing for large datasets

### v1.2.0 (Q2 2026)
- [ ] Plugin system for custom agents
- [ ] Kubernetes deployment templates
- [ ] Advanced monitoring and observability
- [ ] Rate limiting and quota management

### v2.0.0 (Q3 2026)
- [ ] Distributed execution across multiple machines
- [ ] Advanced caching for LLM responses
- [ ] Fine-tuning support for local models
- [ ] Enterprise authentication (OAuth, SAML)

---

**Maintained by**: FlyntCore Development Team  
**Repository**: https://github.com/FlyntCore/FlyntCore  
**Issues**: https://github.com/FlyntCore/FlyntCore/issues  
**Discussions**: https://github.com/FlyntCore/FlyntCore/discussions
