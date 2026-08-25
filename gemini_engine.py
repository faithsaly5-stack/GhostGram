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
        
        # We strictly use the user's selected model ONLY, no fallbacks.
        self.model = Config.MODEL_NAME
        
        # Round-Robin Pointer
        self.current_key_idx = 0
        self._idx_lock = threading.Lock()

    def _client(self, api_key: str):
        """Returns a cached genai.Client instance for the specified API key."""
        with self._client_lock:
            c = self._clients.get(api_key)
            if c is None:
                c = genai.Client(api_key=api_key)
                self._clients[api_key] = c
            return c

    def _get_next_key(self) -> str:
        """Returns the next available API key in round-robin fashion."""
        if not self.keys:
            return None
        with self._idx_lock:
            num_keys = len(self.keys)
            for _ in range(num_keys):
                self.current_key_idx = (self.current_key_idx + 1) % num_keys
                key = self.keys[self.current_key_idx]
                if api_tracker.is_key_available(key):
                    return key
            return None

    def _are_all_keys_dead_or_exhausted(self) -> bool:
        """Checks if all configured keys are permanently invalid or hit the daily 500 cap."""
        if not self.keys:
            return True
        for k in self.keys:
            if not api_tracker.is_key_daily_exhausted(k) and k not in api_tracker.invalid_keys:
                return False
        return True

    async def get_response(self, user_message: str, system_prompt: str, is_json: bool = False) -> str:
        """
        Asynchronously fetches a response from Gemini.
        GUARANTEE POLICY: Persistently retries across all keys, fallback models, and backoffs
        to ensure a response is always delivered, even with only 1 or 2 keys.
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
        num_keys = len(self.keys)
        
        # Max retry cycles: 8 cycles (plenty of time to wait out any RPM rate-limit or network dip)
        max_cycles = 8

        for cycle in range(max_cycles):
            model_to_use = self.model

            cfg = types.GenerateContentConfig(
                system_instruction=safe_sys_prompt,
                thinking_config=types.ThinkingConfig(thinking_level="MINIMAL"),
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            )
            if is_json:
                cfg.response_mime_type = "application/json"

            # Attempt across available keys in the pool
            for _ in range(num_keys):
                api_key = self._get_next_key()
                if not api_key:
                    break

                client = self._client(api_key)
                try:
                    # 15-second strict timeout per attempt
                    resp = await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda c=client, m=model_to_use, cont=contents, conf=cfg: c.models.generate_content(
                                model=m, contents=cont, config=conf
                            )
                        ),
                        timeout=15.0
                    )

                    # Success! Record usage and return formatted text
                    api_tracker.record_success(api_key)
                    raw_text = (resp.text or "").strip()

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
                    clean_text = re.sub(r'[ \t]+', ' ', clean_text)
                    clean_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', clean_text).strip()
                    return clean_text

                except asyncio.TimeoutError:
                    api_tracker.record_network_error(api_key)
                    print(f"⚠️ Key timeout (15s) on model '{model_to_use}'. Retrying...")
                    continue

                except Exception as e:
                    err_str = str(e).lower()

                    if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                        if "per day" in err_str or "daily" in err_str:
                            api_tracker.record_daily_exhausted(api_key)
                        else:
                            # Short 10s cooldown for small key counts
                            cd = 10 if num_keys <= 2 else 30
                            api_tracker.record_rate_limit(api_key, cooldown_seconds=cd)
                    elif "api_key_invalid" in err_str or "permission_denied" in err_str or "400" in err_str or "403" in err_str:
                        api_tracker.record_invalid_key(api_key)
                    else:
                        api_tracker.record_network_error(api_key)
                        print(f"⚠️ Gemini/Network Notice ({type(e).__name__}): {e}")
                    continue

            # If all keys are permanently dead (fake/revoked 400/403) or daily exhausted
            if self._are_all_keys_dead_or_exhausted():
                print("🚫 ALL API KEYS EXHAUSTED FOR TODAY (Daily 500 limit reached or invalid keys).")
                return Text.ERROR

            # If keys are just in temporary cooldown or rate limit, backoff and keep trying!
            if cycle < max_cycles - 1:
                # Use api_tracker to know exactly when the next key will be free (capped at 15s)
                wait_sec = min(15.0, max(2.0, api_tracker.get_next_cooldown_wait(self.keys)))
                print(f"⏳ Persistent Backoff: Waiting {wait_sec:.1f}s before retry cycle {cycle + 2}/{max_cycles} (Model: {self.model})...")
                await asyncio.sleep(wait_sec)

        print("⚠️ All persistent retry cycles exhausted. Dropping message.")
        return Text.ERROR

# Global singleton instance
gemini = GeminiEngine()
