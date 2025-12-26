from groq import Groq
import os

api_key = "REDACTED_API_KEY"
client = Groq(api_key=api_key)

print("Available Groq models:")
for model in client.models.list():
    print(f"- {model.id}")
