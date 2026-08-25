import os
import re
import html
import time
import asyncio
import threading
from google import genai
from google.genai import types
from config import Config
from text import Text
from api_tracker import api_tracker

class GeminiEngine:
    def __init__(self):
        self.keys = Config.GEMINI_API_KEYS
        if not self.keys:
            print("⚠️ No GEMINI_API_KEYS found in config!")
        self._clients = {}
        self._client_lock = threading.Lock()

    def _client(self, api_key: str):
        """Returns a cached genai.Client instance for the specified API key."""
        with self._client_lock:
            c = self._clients.get(api_key)
            if c is None:
                c = genai.Client(api_key=api_key)
                self._clients[api_key] = c
            return c

    async def get_response(self, user_message: str, system_prompt: str, is_json: bool = False, start_model: str = None) -> str:
        """
        Asynchronously fetches a response from Gemini.
        GUARANTEE POLICY: Persistently cascades through the smartest available models
        (or starting from start_model) and all available keys, respecting specific limits.
        """
        if not self.keys:
            print("❌ Error: No Gemini API keys configured!")
            return Text.ERROR

        # 1. Clean payload and strip control characters
        control_char_re = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]')
        safe_user_msg = control_char_re.sub('', user_message)
        safe_sys_prompt = control_char_re.sub('', system_prompt)

        # 2. Safety cap on payload size
        MAX_CHARS = 50000
        if len(safe_user_msg) > MAX_CHARS:
            safe_user_msg = safe_user_msg[:MAX_CHARS // 2] + "\n\n...[TRUNCATED]...\n\n" + safe_user_msg[-(MAX_CHARS // 2):]

        contents = [
            types.Content(role="user", parts=[types.Part.from_text(text=safe_user_msg)])
        ]

        loop = asyncio.get_running_loop()
        
        # Give it up to 20 attempts to cascade through models or wait out cooldowns
        max_attempts = 20

        for attempt in range(max_attempts):
            model_to_use, api_key = api_tracker.get_best_available_model(self.keys, start_model=start_model)
            
            if not api_key:
                wait_sec = min(15.0, max(2.0, api_tracker.get_next_cooldown_wait(self.keys)))
                print(f"⏳ All keys/models busy or exhausted. Waiting {wait_sec:.1f}s (Attempt {attempt + 1}/{max_attempts})...")
                await asyncio.sleep(wait_sec)
                continue

            cfg = types.GenerateContentConfig(
                system_instruction=safe_sys_prompt,
                thinking_config=types.ThinkingConfig(thinking_level="MINIMAL"),
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            )
            if is_json:
                cfg.response_mime_type = "application/json"

            client = self._client(api_key)
            try:
                # 25-second strict timeout per attempt
                resp = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda c=client, m=model_to_use, cont=contents, conf=cfg: c.models.generate_content(
                            model=m, contents=cont, config=conf
                        )
                    ),
                    timeout=25.0
                )

                # Success! Record usage and return formatted text
                api_tracker.record_success(api_key, model_to_use)
                raw_text = (resp.text or "").strip()

                if is_json:
                    return raw_text

                # Post-processing: clean emoji, HTML, diacritics
                emoji_pattern = re.compile(
                    r'[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]|[\ufe00-\ufe0f]',
                    flags=re.UNICODE
                )
                clean_text = emoji_pattern.sub('', raw_text).strip()
                clean_text = html.unescape(clean_text)
                clean_text = re.sub(r'<[^>]+>', '', clean_text)
                diacritics_pattern = re.compile(r'[\u064B-\u065F\u0670\u0617-\u061A\u06D6-\u06ED]')
                clean_text = diacritics_pattern.sub('', clean_text)
                
                # Convert ZWNJ (نیم‌فاصله) to space for casual human-like style
                clean_text = clean_text.replace('\u200c', ' ')
                
                clean_text = re.sub(r'[ \t]+', ' ', clean_text)
                clean_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', clean_text).strip()
                return clean_text

            except asyncio.TimeoutError:
                api_tracker.record_network_error(api_key, model_to_use)
                print(f"⚠️ Key timeout (25s) on model '{model_to_use}'. Cascading...")
                continue

            except Exception as e:
                err_str = str(e).lower()

                # 1. Fatal Safety/Policy Blocks (No retry possible for this specific prompt)
                if "safety" in err_str or "blocked" in err_str or "content_restriction" in err_str or "finish_reason: safety" in err_str:
                    print(f"🛑 SAFETY BLOCK: The prompt violated Google's safety/content policies.")
                    return Text.ERROR
                    
                # 2. Fatal Geographic / Policy Bans
                if "unsupported user location" in err_str or "location is not supported" in err_str:
                    print(f"🌍 GEO-RESTRICTION: Google Gemini is blocked in this server's region!")
                    api_tracker.record_invalid_key(api_key)
                    continue

                # 3. Standard API Errors
                if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                    if "per day" in err_str or "daily" in err_str:
                        api_tracker.record_daily_exhausted(api_key, model_to_use)
                    else:
                        api_tracker.record_rate_limit(api_key, model_to_use, cooldown_seconds=25)
                elif "api_key_invalid" in err_str or "permission_denied" in err_str or "403" in err_str:
                    api_tracker.record_invalid_key(api_key)
                elif "400" in err_str:
                    print(f"❌ BAD REQUEST (400) on {model_to_use}: The prompt was rejected by Google.")
                    # It might be a model specific format error, we can treat it as a network error to fallback
                    api_tracker.record_network_error(api_key, model_to_use, is_unknown=True)
                elif "404" in err_str:
                    print(f"❌ NOT FOUND (404): Model '{model_to_use}' is invalid or deprecated! Disabling model for this key.")
                    api_tracker.record_daily_exhausted(api_key, model_to_use) # Effectively disables it for the day
                elif "timeout" in err_str or "connection" in err_str or "500" in err_str or "503" in err_str:
                    api_tracker.record_network_error(api_key, model_to_use, is_unknown=False)
                    print(f"⚠️ Gemini Network Error on {model_to_use}: {e}")
                else:
                    # 4. Unknown Errors (Catch-All)
                    api_tracker.record_network_error(api_key, model_to_use, is_unknown=True)
                    print(f"⚠️ Unknown Gemini Error on {model_to_use} ({type(e).__name__}): {e}")
                continue

        print("⚠️ All persistent retry cycles exhausted across all cascading models. Dropping message.")
        return Text.ERROR

# Global singleton instance
gemini = GeminiEngine()
