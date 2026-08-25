import os
from dotenv import load_dotenv
from google import genai
import time

load_dotenv()
keys_str = os.environ.get("GEMINI_API_KEYS", "")
if not keys_str:
    keys_str = os.environ.get("GEMINI_API_KEY", "")

keys = [k.strip() for k in keys_str.split(",") if k.strip()]
if not keys:
    print("No API keys found in .env!")
    exit(1)

key = keys[0]
print(f"Using key starting with {key[:10]}...")

client = genai.Client(api_key=key)

try:
    print("Sending request to gemini-3.7-flash...")
    start_time = time.time()
    response = client.models.generate_content(
        model='gemini-3.7-flash',
        contents='Hello, are you online? Respond with a short sentence.',
    )
    elapsed = time.time() - start_time
    print(f"✅ Success! Latency: {elapsed:.2f}s")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")
