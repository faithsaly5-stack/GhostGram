import re
import asyncio
import threading
import logging
from google import genai
from google.genai import types
from config import Config
from text import Text
from api_tracker import api_tracker
from text_processing import clean_outbound_text

# Suppress harmless google-genai AFC deprecation logger warning to keep logs clean
logging.getLogger("google_genai").setLevel(logging.ERROR)

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
                c = genai.Client(api_key=api_key, http_options={'timeout': Config.GEMINI_TIMEOUT_SECONDS})
                self._clients[api_key] = c
            return c



    async def get_response(self, user_message: str, system_prompt: str, is_json: bool = False, start_model: str = None, clean_text: bool = True) -> str:
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
        MAX_CHARS = Config.GEMINI_MAX_CHARS
        if len(safe_user_msg) > MAX_CHARS:
            safe_user_msg = safe_user_msg[:MAX_CHARS // 2] + "\n\n...[TRUNCATED]...\n\n" + safe_user_msg[-(MAX_CHARS // 2):]

        contents = [
            types.Content(role="user", parts=[types.Part.from_text(text=safe_user_msg)])
        ]

        loop = asyncio.get_running_loop()
        
        # Give it up to configured attempts to cascade through models or wait out cooldowns
        max_attempts = Config.GEMINI_MAX_ATTEMPTS
        import time
        overall_start_time = time.time()

        for attempt in range(max_attempts):
            elapsed_overall = time.time() - overall_start_time
            if elapsed_overall >= 90.0 and start_model != "CHEAPEST":
                print(f"⚠️ 90-second SLA threshold reached! Downgrading to CHEAPEST models to guarantee response...")
                start_model = "CHEAPEST"

            model_to_use, api_key = api_tracker.get_best_available_model(self.keys, start_model=start_model)
            
            if not api_key:
                wait_sec = min(15.0, max(2.0, api_tracker.get_next_cooldown_wait(self.keys)))
                print(f"⏳ All keys/models busy or exhausted. Waiting {wait_sec:.1f}s (Attempt {attempt + 1}/{max_attempts})...")
                await asyncio.sleep(wait_sec)
                continue

            cfg = types.GenerateContentConfig(
                system_instruction=safe_sys_prompt,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            )
            if is_json:
                cfg.response_mime_type = "application/json"

            client = self._client(api_key)
            try:
                import time
                start_time = time.time()
                
                # Strict timeout per attempt
                resp = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda c=client, m=model_to_use, cont=contents, conf=cfg: c.models.generate_content(
                            model=m, contents=cont, config=conf
                        )
                    ),
                    timeout=Config.GEMINI_TIMEOUT_SECONDS
                )
                
                elapsed_time = time.time() - start_time
                print(f"⏱️ Gemini API Latency on {model_to_use}: {elapsed_time:.2f}s")

                # Success! Record usage and return formatted text
                api_tracker.record_success(api_key, model_to_use)
                raw_text = resp.text or ""

                # Use JSON text explicitly if required, bypass text processing for internal context
                if is_json:
                    return raw_text
                
                if not clean_text:
                    return raw_text

                return clean_outbound_text(raw_text)

            except asyncio.TimeoutError:
                # Cool down this specific model across ALL keys globally for 45s to avoid 503 cascades
                for k in self.keys:
                    api_tracker.record_rate_limit(k, model_to_use, cooldown_seconds=45, quiet=True)
                print(f"⚠️ Global Timeout ({Config.GEMINI_TIMEOUT_SECONDS}s) on model '{model_to_use}'. Cooling model down for 45s across all keys...")
                continue

            except Exception as e:
                err_str = str(e).lower()

                # 1. Fatal Safety/Policy Blocks (No retry possible for this specific prompt)
                if "safety" in err_str or "blocked" in err_str or "content_restriction" in err_str or "finish_reason: safety" in err_str:
                    print(f"🛑 SAFETY BLOCK: The prompt violated Google's safety/content policies.")
                    return Text.ERROR
                    
                # 2. Fatal Geographic / Policy Bans
                if "unsupported user location" in err_str or "location is not supported" in err_str:
                    print(f"🌍 GEO-RESTRICTION: Google Gemini connection issue (VPN/location). Cooling down key for 60s...")
                    api_tracker.record_rate_limit(api_key, model_to_use, cooldown_seconds=60)
                    continue

                # 3. Standard API Errors
                if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                    if "per day" in err_str or "daily" in err_str or "per-day" in err_str or "per_day" in err_str:
                        api_tracker.record_daily_exhausted(api_key, model_to_use)
                    else:
                        api_tracker.record_rate_limit(api_key, model_to_use, cooldown_seconds=Config.GEMINI_RPM_COOLDOWN_SECONDS)
                elif "api_key_invalid" in err_str or "api key not valid" in err_str:
                    api_tracker.record_invalid_key(api_key)
                elif "permission_denied" in err_str or "403" in err_str:
                    # Transient 403 or project permission hiccup - cool down key temporarily instead of permanent ban
                    api_tracker.record_rate_limit(api_key, model_to_use, cooldown_seconds=60)
                    print(f"⚠️ 403 / Permission error on {model_to_use} for key. Cooling down key for 60s...")
                elif "400" in err_str:
                    print(f"❌ BAD REQUEST (400) on {model_to_use}: The prompt is fundamentally flawed or rejected by Google. Aborting to save keys!\n🔍 Reason: {e}")
                    return Text.ERROR
                elif "404" in err_str:
                    api_tracker.record_dead_model(model_to_use)
                elif "timeout" in err_str or "connection" in err_str or "500" in err_str or "503" in err_str or "ssl" in err_str:
                    for k in self.keys:
                        api_tracker.record_rate_limit(k, model_to_use, cooldown_seconds=45, quiet=True)
                    print(f"⚠️ Gemini Network/Server Error on {model_to_use} ({type(e).__name__}). Cooling down model for 45s across all keys...")
                else:
                    # 4. Unknown Errors (Catch-All)
                    api_tracker.record_network_error(api_key, model_to_use, is_unknown=True)
                    print(f"⚠️ Unknown Gemini Error on {model_to_use} ({type(e).__name__}): {e}")
                continue

        print("⚠️ All persistent retry cycles exhausted across all cascading models. Dropping message.")
        return Text.ERROR

# Global singleton instance
gemini = GeminiEngine()
