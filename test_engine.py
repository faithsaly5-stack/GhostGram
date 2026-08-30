import asyncio
import os
import sys
from dotenv import load_dotenv

from speech_to_text import transcribe_audio_file

async def main():
    load_dotenv("profiles/default/.env")
    keys_str = os.getenv("GEMINI_API_KEYS", "")
    if not keys_str:
        print("No API keys found in env!")
        return
    api_keys = [k.strip() for k in keys_str.split(",") if k.strip()]

    test_file = "test.mp3"

    import time
    print("Testing with real mp3 file...")
    start_t = time.time()
    res = await transcribe_audio_file(test_file, api_keys)
    elapsed = time.time() - start_t
    print(f"Result for mp3 file:\n{res}")
    print(f"\nTime taken: {elapsed:.2f}s")
    
    print("Test finished.")

if __name__ == "__main__":
    asyncio.run(main())
