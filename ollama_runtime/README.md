# Bundled Ollama Runtime

This directory contains the embedded Ollama distribution for TerraQore.

## Contents

- `bin/` - Ollama executables (Windows/Linux)
- `models/` - Pre-cached models for instant offline use
- `config/` - Runtime configuration

## Pre-cached Models

- **phi3:latest** (3.8GB) - Fast inference, basic tasks
- **llama3:8b** (4.7GB) - Balanced performance, general purpose
- **gemma2:9b** (5.4GB) - High quality, complex reasoning

## Auto-startup

TerraQore automatically starts the bundled Ollama server:

**Windows**: `start.ps1` launches `ollama_runtime/bin/ollama.exe serve`
**Linux**: `start.sh` launches `ollama_runtime/bin/ollama serve`

## Manual Setup (if needed)

If auto-startup fails:

```bash
# Windows
cd ollama_runtime\bin
.\ollama.exe serve

# Linux
cd ollama_runtime/bin
./ollama serve
```

## Health Check

TerraQore gateway automatically detects bundled Ollama at `http://localhost:11434`

## Disk Space

Total: ~13GB for all 3 models
- Minimum recommended: 16GB free space
- Optimal: 32GB+ for additional models

## Model Management

Models are stored in `models/` and automatically loaded on first use.

To add more models manually:
```bash
ollama pull <model_name>
```

## Troubleshooting

**Port 11434 in use**: Another Ollama instance running. Stop it first.
**Models not loading**: Check disk space in `models/` directory
**Slow startup**: First run extracts models, subsequent starts are faster

## License

Ollama: MIT License - https://github.com/ollama/ollama
Models: Check individual model licenses on Hugging Face
