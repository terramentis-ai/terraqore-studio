import os
import sys
print("Starting script...", flush=True)

try:
    from dotenv import load_dotenv
    print("Imported dotenv", flush=True)
    import google.generativeai as genai
    print("Imported genai", flush=True)
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

load_dotenv()
print("Loaded dotenv", flush=True)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY not found in environment")
else:
    print(f"Found API key: {api_key[:5]}...", flush=True)
    try:
        genai.configure(api_key=api_key)
        print("Configured genai. Listing models...", flush=True)
        found = False
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
                found = True
        if not found:
            print("No models found with 'generateContent' capability.")
    except Exception as e:
        print(f"Error listing models: {e}")
print("Script finished.", flush=True)
