import threading
import time
from google import genai
from google.genai import types
from config import Config
from text import Text

class GeminiEngine:
    def __init__(self):
        self.keys = Config.GEMINI_API_KEYS
        if not self.keys:
            print("⚠️ No GEMINI_API_KEYS found in config!")
        self._clients = {}
        self._client_lock = threading.Lock()
        self.model = Config.MODEL_NAME
        
        # Round-Robin State
        self.current_key_idx = 0
        self._idx_lock = threading.Lock()

    def _client(self, api_key: str):
        """
        Return a cached, REUSED genai.Client for this key.
        We also inject a strict 15.0s timeout at the HTTP level.
        """
        with self._client_lock:
            c = self._clients.get(api_key)
            if c is None:
                c = genai.Client(api_key=api_key)
                self._clients[api_key] = c
            return c

    def _get_next_key(self) -> str:
        """Returns the next available API key in round-robin fashion, respecting daily limits."""
        with self._idx_lock:
            from api_tracker import api_tracker
            num_keys = len(self.keys)
            for _ in range(num_keys):
                self.current_key_idx = (self.current_key_idx + 1) % num_keys
                key = self.keys[self.current_key_idx]
                if api_tracker.is_key_available(key):
                    return key
            return None

    async def get_response(self, user_message: str, system_prompt: str, is_json: bool = False) -> str:
        """
        Asynchronously fetches a response using Round-Robin key management
        and a hard 15-second timeout per key attempt.
        """
        # ==========================================
        # 🛡️ PRE-FLIGHT SAFETY SANITIZER
        # ==========================================
        import re
        
        # 1. Strip null bytes and obscure control characters that break REST APIs (keep newlines and tabs)
        control_char_re = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]')
        safe_user_msg = control_char_re.sub('', user_message)
        safe_sys_prompt = control_char_re.sub('', system_prompt)
        
        # 2. Hard payload size limits (Google Gemini Flash has a 1M token limit, but we don't want to send garbage)
        # 50,000 characters is roughly 12,000 words, way more than enough for a Telegram chat history.
        MAX_CHARS = 50000
        if len(safe_user_msg) > MAX_CHARS:
            print(f"⚠️ Payload too large ({len(safe_user_msg)} chars). Truncating to {MAX_CHARS} chars.")
            # Keep the beginning and the end of the history if truncated
            safe_user_msg = safe_user_msg[:MAX_CHARS // 2] + "\n\n...[TRUNCATED]...\n\n" + safe_user_msg[-(MAX_CHARS // 2):]
            
        try:
            contents = [
                types.Content(role="user", parts=[types.Part.from_text(text=safe_user_msg)])
            ]
            
            cfg = types.GenerateContentConfig(
                system_instruction=safe_sys_prompt,
                thinking_config=types.ThinkingConfig(thinking_level="MINIMAL"),
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            )
            
            if is_json:
                cfg.response_mime_type = "application/json"
                
            if not self.keys:
                raise RuntimeError("NO_KEYS_CONFIGURED")

            import asyncio
            import re
            import html
            from api_tracker import api_tracker
            
            # Lazy initialize the global queue lock
            if not hasattr(self, '_queue_lock') or self._queue_lock is None:
                self._queue_lock = asyncio.Lock()
                
            loop = asyncio.get_running_loop()
            num_keys = len(self.keys)
            
            # Global Queue: Process AI requests strictly one by one
            async with self._queue_lock:
                while True:
                    last_err = None
                    resp = None
                    
                    # Round-Robin Loop: Try up to `num_keys` times
                    for attempt in range(num_keys):
                        api_key = self._get_next_key()
                        
                        if not api_key:
                            print("🚫 ALL API KEYS EXHAUSTED FOR TODAY! Pausing queue and dropping message.")
                            from text import Text
                            return Text.ERROR
                            
                        client = self._client(api_key)
                        
                        try:
                            # Increment usage counter right before making the API call
                            from api_tracker import api_tracker
                            api_tracker.record_usage(api_key)
                            
                            # 15-Second Hard Timeout
                            resp = await asyncio.wait_for(
                                loop.run_in_executor(
                                    None, 
                                    lambda c=client, m=self.model, cont=contents, conf=cfg: c.models.generate_content(model=m, contents=cont, config=conf)
                                ),
                                timeout=15.0
                            )
                            
                            # Success! Reset circuit breaker
                            api_tracker.record_success(api_key)
                            break # Success! Exit the round-robin loop
                            
                        except asyncio.TimeoutError:
                            api_tracker.record_error(api_key)
                            last_err = Exception("15-second strict timeout reached")
                            print(f"⚠️ Key timeout (15s). Moving to next key in cycle...")
                            continue
                        except Exception as e:
                            last_err = e
                            err_str = str(e).lower()
                            
                            # ALL ERRORS (API Key banned, Rate limit, Server error, Network error, Bad Request, etc.)
                            # Since the payload is pre-sanitized, we assume any error is a key/network issue.
                            # Action: Cycle to next key and record failure for Circuit Breaker
                            api_tracker.record_error(api_key)
                            print(f"⚠️ Key/Network Error ({type(e).__name__}). Moving to next key in cycle: {e}")
                            continue
                    
                    if resp is not None:
                        break # Successfully got a response, exit infinite retry loop
                        
                    # Infinite Retry Backoff: If ALL keys fail, sleep 30s and try again!
                    print(f"⚠️ All {num_keys} API keys failed (Rate Limit). Queue paused. Sleeping 30s before retrying...")
                    await asyncio.sleep(30)
            
            raw_text = (resp.text or "").strip()
            
            # Clean up text
            emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]|[\ufe00-\ufe0f]', flags=re.UNICODE)
            clean_text = emoji_pattern.sub('', raw_text).strip()
            
            clean_text = html.unescape(clean_text)
            clean_text = re.sub(r'<[^>]+>', '', clean_text)
            
            diacritics_pattern = re.compile(r'[\u064B-\u065F\u0670\u0617-\u061A\u06D6-\u06ED]')
            clean_text = diacritics_pattern.sub('', clean_text)
            
            clean_text = re.sub(r'[ \t]+', ' ', clean_text)
            clean_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', clean_text).strip()
            return clean_text
            
        except Exception as e:
            from text import Text
            print(f"Error in GeminiEngine: {str(e)}")
            return Text.ERROR

# Global singleton instance
gemini = GeminiEngine()
