import re
import asyncio
import threading
import logging
from logger import logger
import random
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
            logger.info("⚠️ No GEMINI_API_KEYS found in config!")
        self._clients = {}
        self._client_lock = threading.Lock()

    def _client(self, api_key: str):
        """Returns a cached genai.Client instance for the specified API key."""
        with self._client_lock:
            c = self._clients.get(api_key)
            if c is None:
                c = genai.Client(api_key=api_key, http_options={'timeout': int(Config.GEMINI_TIMEOUT_SECONDS * 1000)})
                self._clients[api_key] = c
            return c



    async def get_response(self, user_message: str, system_prompt: str, is_json: bool = False, start_model: str = None, clean_text: bool = True) -> str:
        """
        Asynchronously fetches a response from Gemini.
        GUARANTEE POLICY: Persistently cascades through the smartest available models
        (or starting from start_model) and all available keys, respecting specific limits.
        """
        if not self.keys:
            logger.info("❌ Error: No Gemini API keys configured!")
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
        
        # Give it enough attempts to cascade through all models and keys without premature abort
        from api_tracker import MODELS_CONFIG
        max_attempts = max(Config.GEMINI_MAX_ATTEMPTS, len(self.keys) * len(MODELS_CONFIG) + 25)
        import time
        overall_start_time = time.time()
        consecutive_errors = 0
        last_failed_key = None
        model_attempts = {}
        excluded_models = set()
        MAX_PER_MODEL_ATTEMPTS = 2

        for attempt in range(max_attempts):
            elapsed_overall = time.time() - overall_start_time
            if elapsed_overall >= Config.GEMINI_SLA_TIMEOUT_SECONDS and start_model != "CHEAPEST":
                logger.info(f"⚠️ {Config.GEMINI_SLA_TIMEOUT_SECONDS}-second SLA threshold reached! Downgrading to CHEAPEST models to guarantee response...")
                start_model = "CHEAPEST"
                excluded_models.clear()

            model_to_use, api_key = api_tracker.get_best_available_model(
                self.keys, start_model=start_model, excluded_models=excluded_models
            )
            
            if not api_key:
                if excluded_models:
                    # All non-excluded models are exhausted; release exclusions to cycle remaining keys
                    excluded_models.clear()
                    model_attempts.clear()
                    continue
                wait_sec = min(10.0, max(1.5, api_tracker.get_next_cooldown_wait(self.keys)))
                logger.info(f"⏳ All keys/models busy or exhausted. Waiting {wait_sec:.1f}s (Attempt {attempt + 1}/{max_attempts})...")
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
                logger.info(f"⏱️ Gemini API Latency on {model_to_use}: {elapsed_time:.2f}s")

                raw_text = resp.text or ""
                if not raw_text.strip():
                    logger.info(f"⚠️ Empty response received from {model_to_use} (Key {api_key[:6]}...). Retrying next candidate...")
                    continue

                # Success! Record usage and return formatted text
                api_tracker.record_success(api_key, model_to_use)

                # Use JSON text explicitly if required, bypass text processing for internal context
                if is_json:
                    return raw_text
                
                if not clean_text:
                    return raw_text

                return clean_outbound_text(raw_text)

            except asyncio.TimeoutError:
                model_attempts[model_to_use] = model_attempts.get(model_to_use, 0) + 1
                if model_attempts[model_to_use] >= MAX_PER_MODEL_ATTEMPTS and start_model != "CHEAPEST":
                    excluded_models.add(model_to_use)
                    logger.info(f"⚡ Fast Cascade: Model '{model_to_use}' hit attempt limit ({MAX_PER_MODEL_ATTEMPTS}). Cascading down...")

                api_tracker.release_rpm_slot(api_key, model_to_use)
                api_tracker.record_network_error(api_key, model_to_use)
                key_preview = f"{api_key[:6]}..."
                logger.info(f"⚠️ Timeout ({Config.GEMINI_TIMEOUT_SECONDS}s) on model '{model_to_use}' (Key {key_preview}). Retrying...")
                
                if api_key != last_failed_key:
                    consecutive_errors = 0
                    backoff = random.uniform(0.1, 0.4)
                else:
                    consecutive_errors += 1
                    backoff = min(3.0, (1.5 ** consecutive_errors)) + random.uniform(0.1, 0.3)
                
                last_failed_key = api_key
                if backoff > 0:
                    logger.info(f"⏳ Backoff (Timeout): Waiting {backoff:.2f}s before retrying same key...")
                    await asyncio.sleep(backoff)
                else:
                    await asyncio.sleep(0)
                continue

            except Exception as e:
                err_str = str(e).lower()
                
                is_model_specific_error = "500" in err_str or "503" in err_str or "504" in err_str or "499" in err_str
                if is_model_specific_error:
                    model_attempts[model_to_use] = model_attempts.get(model_to_use, 0) + 1
                    if model_attempts[model_to_use] >= MAX_PER_MODEL_ATTEMPTS and start_model != "CHEAPEST":
                        excluded_models.add(model_to_use)
                        logger.info(f"⚡ Fast Cascade: Model '{model_to_use}' hit attempt limit ({MAX_PER_MODEL_ATTEMPTS}). Cascading down...")

                err_str = str(e).lower()

                # 1. Fatal Safety/Policy Blocks (No retry possible for this specific prompt)
                if "safety" in err_str or "blocked" in err_str or "content_restriction" in err_str or "finish_reason: safety" in err_str:
                    logger.info(f"🛑 SAFETY BLOCK: The prompt violated Google's safety/content policies.")
                    return Text.ERROR
                    
                # 2. Fatal Geographic / Policy Bans
                if "unsupported user location" in err_str or "location is not supported" in err_str:
                    logger.info(f"🌍 GEO-RESTRICTION: Google Gemini connection issue (VPN/location). Cooling down key for 60s...")
                    for m in MODELS_CONFIG:
                        api_tracker.record_rate_limit(api_key, m["name"], cooldown_seconds=60, quiet=True)

                # 3. Standard API Errors
                elif "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                    if "per day" in err_str or "daily" in err_str or "per-day" in err_str or "per_day" in err_str or "perday" in err_str or "requests_per_day" in err_str or "generaterequestsperday" in err_str:
                        api_tracker.record_daily_exhausted(api_key, model_to_use)
                    else:
                        # Force 60s cooldown because Google RPM limits reset per minute. 15s is too short and causes infinite 429 loops.
                        api_tracker.record_rate_limit(api_key, model_to_use, cooldown_seconds=60)
                elif "api_key_invalid" in err_str or "api key not valid" in err_str:
                    api_tracker.release_rpm_slot(api_key, model_to_use)
                    api_tracker.record_invalid_key(api_key)
                elif "permission_denied" in err_str or "403" in err_str:
                    api_tracker.release_rpm_slot(api_key, model_to_use)
                    api_tracker.record_invalid_key(api_key)
                    key_preview = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else api_key
                    logger.info(f"⚠️ 403 / Permission error for key {key_preview}. Disabled completely for this session.")
                elif "400" in err_str:
                    logger.info(f"❌ BAD REQUEST (400) on {model_to_use}: The prompt is fundamentally flawed or rejected by Google. Aborting to save keys!\n🔍 Reason: {e}")
                    return Text.ERROR
                elif "404" in err_str:
                    api_tracker.record_dead_model(model_to_use)
                elif "500" in err_str or "503" in err_str or "504" in err_str or "499" in err_str:
                    is_quarantined, tier, duration_seconds = api_tracker.record_global_model_failure(model_to_use, self.keys)
                    if is_quarantined:
                        if tier == 1:
                            logger.info(f"🛑 CIRCUIT BREAKER TRIPPED (Tier 1): Model '{model_to_use}' failed 5 times in 5 minutes. Quarantined for {duration_seconds/60:.1f} minutes!")
                        elif tier == 2:
                            logger.info(f"🛑 CIRCUIT BREAKER ESCALATED (Tier 2): Model '{model_to_use}' Quarantined for {duration_seconds/3600:.1f} hours!")
                        else:
                            logger.info(f"💀 CIRCUIT BREAKER MAXIMUM (Tier {tier}): Model '{model_to_use}' Quarantined for {duration_seconds/3600:.1f} hours!")
                    else:
                        api_tracker.record_network_error(api_key, model_to_use)
                        logger.info(f"⚠️ Gemini Server Error on {model_to_use} ({type(e).__name__}). Retrying...")
                elif "timeout" in err_str or "connection" in err_str or "cancelled" in err_str or "ssl" in err_str:
                    api_tracker.release_rpm_slot(api_key, model_to_use)
                    api_tracker.record_network_error(api_key, model_to_use)
                    logger.info(f"⚠️ Local Network/Connection Error on {model_to_use} ({type(e).__name__}). Retrying...")
                else:
                    # 4. Unknown Errors (Catch-All)
                    api_tracker.record_network_error(api_key, model_to_use, is_unknown=True)
                    logger.info(f"⚠️ Unknown Gemini Error on {model_to_use} ({type(e).__name__}): {e}")
                
                if api_key != last_failed_key:
                    consecutive_errors = 0
                    backoff = random.uniform(0.1, 0.4)
                else:
                    consecutive_errors += 1
                    backoff = min(3.0, (1.5 ** consecutive_errors)) + random.uniform(0.1, 0.3)
                
                last_failed_key = api_key
                if backoff > 0:
                    logger.info(f"⏳ Backoff: Waiting {backoff:.2f}s before retrying same key...")
                    await asyncio.sleep(backoff)
                else:
                    await asyncio.sleep(0)
                continue

        logger.info("⚠️ All persistent retry cycles exhausted across all cascading models. Dropping message.")
        return Text.ERROR

# Global singleton instance
gemini = GeminiEngine()
