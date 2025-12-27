# 🔑 TERRAQORE Environment Setup

To enable the AI capabilities of TERRAQORE, you need to configure your API keys.

## 1. Create Configuration File

Navigate to the `core_clli` directory and create a file named `.env` (or rename `.env.example`).

```bash
cd core_clli
cp .env.example .env
```

## 2. Add API Keys

Open `.env` and add your keys:

```ini
# Google Gemini (Recommended - Free Tier available)
# Get key: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_key_here

# Groq (Optional - Fast Fallback)
# Get key: https://console.groq.com/
GROQ_API_KEY=your_key_here
```

## 3. Restart Backend

After saving the `.env` file, restart the backend server:

1. Stop the running server (Ctrl+C)
2. Run: `python backend_main.py`

## 4. Verify Connection

Check the terminal output. You should see:
`INFO: Primary LLM healthy: ...`

## 5. Alternative: Local Ollama

If you prefer running locally without API keys:

1. Install [Ollama](https://ollama.ai/)
2. Pull the models:
   ```bash
   ollama pull llama3
   ollama pull mistral
   ```
3. Ensure Ollama is running (`ollama serve`)
4. TERRAQORE will automatically detect it if cloud providers fail, or you can force it by adding `TERRAQORE_FORCE_OLLAMA=1` to your `.env`.
