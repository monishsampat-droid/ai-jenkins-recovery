import os
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise SystemExit("API key missing. Set it in this terminal first.")

client = genai.Client(api_key=api_key)

print("Connecting to Gemini...")

response = client.interactions.create(
    model="gemini-3.8-flash",
    input="Reply with only: AI connection successful",
)

print(response.output_text)