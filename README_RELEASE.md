# FlyntCore v1.0

A production-ready multi-agent AI orchestration platform with multi-provider LLM support.

## Features

✨ **Multi-Provider LLM Support**
- Online providers: Google Gemini, Groq, OpenRouter
- Local models: Ollama (phi3, llama, etc.)
- Seamless provider switching without code changes

🤖 **Multi-Agent System**
- Specialized agents: Researcher, Engineer, Data Analyst, Quality Assurance
- Intelligent task routing and execution
- Real-time collaboration and progress tracking

⚡ **Production-Grade Architecture**
- FastAPI backend with comprehensive error handling
- React + Vite frontend with provider-agnostic design
- WebSocket support for real-time updates
- Docker containerization ready

🔒 **Security & Best Practices**
- No hardcoded credentials in codebase
- Environment variable configuration for API keys
- Comprehensive error logging and recovery
- GitHub Actions CI/CD pipeline

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- npm or yarn
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/FlyntCore/FlyntCore.git
cd FlyntCore

# Build the project
./build.sh              # Linux/macOS
.\build.ps1             # Windows
```

### Configuration

1. **Set up API Keys** (for online providers):
```bash
export GEMINI_API_KEY=your_gemini_key
export GROQ_API_KEY=your_groq_key
export OPENROUTER_API_KEY=your_openrouter_key
```

2. **Configure Ollama** (for local models):
```bash
# In a separate terminal
ollama serve

# In another terminal
ollama pull phi3
```

3. **Start the application**:
```bash
./start.sh              # Linux/macOS
.\start.ps1             # Windows (select mode: backend, frontend, or both)
```

### Access the Application

- **Frontend**: http://localhost:3001
- **Backend API**: http://127.0.0.1:8000
- **API Docs**: http://127.0.0.1:8000/docs

## Project Structure

```
FlyntCore/
├── core_clli/              # Backend (Python/FastAPI)
│   ├── agents/             # Multi-agent implementations
│   ├── core/               # Core components
│   ├── orchestration/       # Workflow orchestration
│   └── backend_main.py      # FastAPI app entry point
├── gui/                    # Frontend (React/TypeScript)
│   ├── components/         # React components
│   ├── services/           # API client and services
│   └── index.tsx           # React entry point
├── build.sh/build.ps1      # Build scripts
├── start.sh/start.ps1      # Start scripts
├── requirements.txt        # Python dependencies
├── CHANGELOG.md            # Release notes
├── SETUP_AND_RUN_GUIDE.md  # Detailed setup guide
└── README.md               # This file
```

## Architecture

### Backend Flow
```
Frontend Request 
    ↓
FastAPI Endpoint (/api/llm/*)
    ↓
LLM Client (Abstraction Layer)
    ↓
Selected Provider (Gemini | Groq | OpenRouter | Ollama)
    ↓
Response back to Frontend
```

### Frontend Architecture
- **Provider-Agnostic**: No direct SDK dependencies
- **API-Driven**: All LLM operations flow through backend
- **Resilient**: ErrorBoundary catches runtime errors
- **Switchable**: Change providers in Settings UI without code changes

## Configuration

### LLM Providers

#### Online Providers (Recommended for production)

**Gemini**
```bash
export GEMINI_API_KEY=your_api_key
# Model: models/gemini-2.5-flash
```

**Groq**
```bash
export GROQ_API_KEY=your_api_key
# Model: llama-3.3-70b-versatile
```

**OpenRouter**
```bash
export OPENROUTER_API_KEY=your_api_key
# Model: meta-llama/llama-3.1-70b-instruct
```

#### Local Provider (Development/Privacy)

**Ollama**
```bash
# Install: https://ollama.ai
# Start: ollama serve
# Pull model: ollama pull phi3
# No API key required
```

## API Endpoints

### LLM Endpoints

- `POST /api/llm/chat` - General-purpose LLM completion
- `POST /api/llm/plan` - Task breakdown using Meta-Controller
- `POST /api/llm/execute` - Execute agent tasks
- `GET /api/llm/providers` - List available providers
- `GET /api/llm/config` - Get current LLM configuration
- `POST /api/llm/config` - Update LLM settings

### Project Endpoints

- `GET /api/projects` - List projects
- `POST /api/projects` - Create project
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Workflow Endpoints

- `GET /api/projects/{id}/workflow` - Get workflow
- `POST /api/projects/{id}/workflow` - Save workflow
- `POST /api/projects/{id}/execute` - Execute workflow

See `/docs` endpoint for interactive API documentation.

## Development

### Running Tests

```bash
cd core_clli
pip install pytest pytest-cov
pytest tests -v --cov=core
```

### Code Quality

```bash
# Backend
flake8 core_clli
black core_clli

# Frontend
cd gui
npm run lint
npm run format
```

### Building for Production

```bash
# Build both backend and frontend
./build.sh              # Linux/macOS
.\build.ps1             # Windows
```

## Environment Variables

```bash
# LLM Providers
GEMINI_API_KEY=          # Google Gemini API key
GROQ_API_KEY=            # Groq API key
OPENROUTER_API_KEY=      # OpenRouter API key

# Application
FLYNT_DEBUG=0            # Enable debug mode
FLYNT_FORCE_OLLAMA=0     # Force Ollama as primary provider
FLYNT_TIMEOUT=30         # Request timeout (seconds)

# Ollama
OLLAMA_BASE_URL=http://localhost:11434  # Ollama server URL
```

## Troubleshooting

### Backend won't start
1. Check Python version: `python --version` (should be 3.9+)
2. Verify virtual environment: `source .venv/bin/activate` (Linux/macOS)
3. Check dependencies: `pip install -r requirements.txt`
4. Check logs for error messages

### Frontend build issues
1. Clear node_modules: `rm -rf gui/node_modules && npm ci`
2. Update npm: `npm install -g npm@latest`
3. Check Node version: `node --version` (should be 16+)

### LLM provider not responding
1. **Ollama**: Ensure `ollama serve` is running in another terminal
2. **Online providers**: Check API key is set correctly as environment variable
3. **Network**: Verify internet connection for online providers

### Blank screen on Frontend
- Check browser console for errors (F12 → Console tab)
- Check backend logs for API errors
- Verify backend is running on http://127.0.0.1:8000

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -am 'Add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Submit a pull request

See [CONTRIBUTING.md](core_clli/CONTRIBUTING.md) for detailed guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](core_clli/LICENSE) file for details.

## Support

- 📖 [Documentation](SETUP_AND_RUN_GUIDE.md)
- 🐛 [Issues](https://github.com/FlyntCore/FlyntCore/issues)
- 💬 [Discussions](https://github.com/FlyntCore/FlyntCore/discussions)
- 📧 Email: dev@flyntcore.ai

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - JavaScript UI library
- [TypeScript](https://www.typescriptlang.org/) - Type-safe JavaScript
- [Vite](https://vitejs.dev/) - Next generation frontend tooling
- [Google Generative AI](https://ai.google.dev/) - Gemini API
- [Groq](https://groq.com/) - Fast LLM inference
- [Ollama](https://ollama.ai/) - Local LLM support

---

**Version**: 1.0.0  
**Last Updated**: December 26, 2025  
**Maintained by**: FlyntCore Development Team  
**Repository**: https://github.com/FlyntCore/FlyntCore
