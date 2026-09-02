import json
import os
import time
import threading
from datetime import datetime, timezone
from config import Config

MODELS_CONFIG = []
models_env = Config.GEMINI_MODELS

# Support multiline format with newlines or single-line with commas
raw_lines = models_env.replace(',', '\n').split('\n')
for line in raw_lines:
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    parts = line.split(':')
    if len(parts) >= 3:
        MODELS_CONFIG.append({
            "name": parts[0].strip(),
            "rpm": int(parts[1].strip()),
            "rpd": int(parts[2].strip())
        })

if not MODELS_CONFIG:
    print("❌ CRITICAL ERROR: No models defined in GEMINI_MODELS inside .env! Please check your .env file.")
    import sys
    sys.exit(1)

class APIUsageTracker:
    def __init__(self, filename=None):
        self.filename = filename or getattr(Config, "API_USAGE_FILE", "api_usage.json")
        self._lock = threading.RLock()
        
        # Persistent daily count
        self.usage_data = self._load()
        
        # In-memory tracking
        # cooldowns: api_key -> {model_name -> (timestamp_until, reason_str)}
        self.cooldowns = {}
        # consecutive transient failures: api_key -> {model_name -> int}
        self.consecutive_failures = {}
        # RPM timestamps: api_key -> {model_name -> list of float timestamps (last 60s)}
        self.rpm_timestamps = {}
        # Permanently invalid keys (400/403 bad keys): set of api_keys
        self.invalid_keys = set()
        
    def _init_key_model_dicts(self, api_key: str):
        if api_key not in self.cooldowns:
            self.cooldowns[api_key] = {}
        if api_key not in self.consecutive_failures:
            self.consecutive_failures[api_key] = {}
        if api_key not in self.rpm_timestamps:
            self.rpm_timestamps[api_key] = {}

    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Migration from old schema {"date": "...", "count": N}
                    today = self._get_today_str()
                    for key, val in data.items():
                        if "count" in val and "models" not in val:
                            data[key] = {"date": today, "models": {}}
                    return data
            except Exception:
                pass
        return {}

    def _save(self):
        import copy
        import threading
        if not hasattr(self, '_write_lock'):
            self._write_lock = threading.Lock()
            self._save_timer = None
            
        self._latest_snapshot = copy.deepcopy(self.usage_data)
        
        if self._save_timer is not None and self._save_timer.is_alive():
            return
            
        def _write_task():
            with self._write_lock:
                try:
                    data = getattr(self, '_latest_snapshot', {})
                    tmp_file = f"{self.filename}.tmp"
                    with open(tmp_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                    os.replace(tmp_file, self.filename)
                except Exception:
                    pass

        self._save_timer = threading.Timer(3.0, _write_task)
        self._save_timer.start()

    def _get_today_str(self):
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
    def get_model_config(self, model_name: str) -> dict:
        for cfg in MODELS_CONFIG:
            if cfg["name"] == model_name:
                return cfg
        return None

    def is_model_key_available(self, api_key: str, model_name: str) -> bool:
        """Checks if a specific key and model combination is ready for immediate execution."""
        with self._lock:
            if api_key in self.invalid_keys:
                return False
                
            cfg = self.get_model_config(model_name)
            if not cfg:
                return False # Unknown model

            self._init_key_model_dicts(api_key)
            now = time.time()

            # 1. Cooldown check
            if model_name in self.cooldowns[api_key]:
                exp_time, reason = self.cooldowns[api_key][model_name]
                if now < exp_time:
                    return False
                else:
                    # Cooldown expired naturally
                    del self.cooldowns[api_key][model_name]
                    self.consecutive_failures[api_key][model_name] = 0

            # 2. RPM check (last 60 seconds)
            if model_name in self.rpm_timestamps[api_key]:
                recent = [ts for ts in self.rpm_timestamps[api_key][model_name] if now - ts < 60]
                self.rpm_timestamps[api_key][model_name] = recent
                if len(recent) >= cfg["rpm"]:
                    return False

            # 3. Daily Limit check
            today = self._get_today_str()
            key_data = self.usage_data.get(api_key, {})
            if key_data.get("date") != today:
                return True
                
            models_data = key_data.get("models", {})
            return models_data.get(model_name, 0) < cfg["rpd"]
            
    def get_best_available_model(self, api_keys: list[str], start_model: str = None):
        """
        Iterates through the sorted MODELS_CONFIG (smartest first).
        If start_model is specified, skips smarter models and starts from that one.
        For each model, checks all API keys.
        Returns the first (model_name, api_key) that is available.
        Returns (None, None) if completely exhausted/rate-limited.
        """
        with self._lock:
            start_idx = 0
            if start_model:
                if start_model == "CHEAPEST" and MODELS_CONFIG:
                    # Cheap = Highest Daily Limit (RPD). If tied, highest RPM.
                    best_idx = len(MODELS_CONFIG) - 1
                    max_score = (-1, -1)
                    for i, cfg in enumerate(MODELS_CONFIG):
                        score = (cfg["rpd"], cfg["rpm"])
                        # Using > means if there's a tie, we pick the FIRST one (upper = smarter)
                        if score > max_score:
                            max_score = score
                            best_idx = i
                    start_idx = best_idx
                else:
                    for i, cfg in enumerate(MODELS_CONFIG):
                        if cfg["name"] == start_model:
                            start_idx = i
                            break
                        
            for cfg in MODELS_CONFIG[start_idx:]:
                model_name = cfg["name"]
                for key in api_keys:
                    if self.is_model_key_available(key, model_name):
                        # Optimistic RPM Booking: Claim the slot instantly to prevent concurrent 'thundering herd' 429s
                        import time
                        now = time.time()
                        if model_name not in self.rpm_timestamps[key]:
                            self.rpm_timestamps[key][model_name] = []
                        self.rpm_timestamps[key][model_name].append(now)
                        return model_name, key
            return None, None

    def is_key_daily_exhausted(self, api_key: str, model_name: str) -> bool:
        """Checks if key reached its hard daily requests limit for a specific model."""
        with self._lock:
            if api_key in self.invalid_keys:
                return True
                
            cfg = self.get_model_config(model_name)
            if not cfg:
                return True
                
            today = self._get_today_str()
            key_data = self.usage_data.get(api_key, {})
            if key_data.get("date") == today:
                models_data = key_data.get("models", {})
                return models_data.get(model_name, 0) >= cfg["rpd"]
            return False

    def get_next_cooldown_wait(self, keys: list[str]) -> float:
        """Returns the minimum seconds to wait for ANY key+model combo to recover from cooldown."""
        with self._lock:
            now = time.time()
            waits = []
            
            for k in keys:
                if k in self.invalid_keys:
                    continue
                self._init_key_model_dicts(k)
                    
                for cfg in MODELS_CONFIG:
                    model_name = cfg["name"]
                    
                    if self.is_key_daily_exhausted(k, model_name):
                        continue
                        
                    if model_name in self.cooldowns[k]:
                        rem = self.cooldowns[k][model_name][0] - now
                        if rem > 0:
                            waits.append(rem)
                    elif model_name in self.rpm_timestamps[k] and len(self.rpm_timestamps[k][model_name]) >= cfg["rpm"]:
                        oldest = min(self.rpm_timestamps[k][model_name])
                        rem = 60 - (now - oldest)
                        if rem > 0:
                            waits.append(rem)
            
            return min(waits) if waits else 4.0

    def record_success(self, api_key: str, model_name: str):
        """Records a successful request, updates RPM and daily usage for the model."""
        with self._lock:
            self._init_key_model_dicts(api_key)
            now = time.time()
            self.consecutive_failures[api_key][model_name] = 0
            if model_name in self.cooldowns[api_key]:
                del self.cooldowns[api_key][model_name]

            # Update Daily persistent count
            today = self._get_today_str()
            key_data = self.usage_data.get(api_key, {})
            if key_data.get("date") != today:
                key_data = {"date": today, "models": {model_name: 1}}
            else:
                models_data = key_data.get("models", {})
                models_data[model_name] = models_data.get(model_name, 0) + 1
                key_data["models"] = models_data

            self.usage_data[api_key] = key_data
            self._save()

    def record_rate_limit(self, api_key: str, model_name: str, cooldown_seconds: int = 15, quiet: bool = False):
        """Temporary 429 / RPM cooldown for a specific model on this key."""
        with self._lock:
            self._init_key_model_dicts(api_key)
            if not quiet:
                key_preview = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else api_key
                print(f"⏳ Key {key_preview} reached RPM limit on {model_name}. Cooling down for {cooldown_seconds}s...")
            self.cooldowns[api_key][model_name] = (time.time() + cooldown_seconds, "RATE_LIMIT")

    def record_network_error(self, api_key: str, model_name: str, is_unknown: bool = False):
        """Handles transient network errors, timeouts, or unknown Google API errors per model."""
        with self._lock:
            self._init_key_model_dicts(api_key)
            fails = self.consecutive_failures[api_key].get(model_name, 0) + 1
            self.consecutive_failures[api_key][model_name] = fails
            key_preview = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else api_key

            if fails >= 10 and is_unknown:
                print(f"🛑 Key {key_preview} had 10 consecutive unknown errors on {model_name}. Quarantining this model for 5 minutes.")
                self.cooldowns[api_key][model_name] = (time.time() + 300, "QUARANTINE_UNKNOWN_ERROR")
            elif fails >= 5:
                print(f"⚠️ Key {key_preview} had {fails} consecutive network errors on {model_name}. Resting this model for 30s.")
                self.cooldowns[api_key][model_name] = (time.time() + 30, "NETWORK_FAILURES")
            else:
                self.cooldowns[api_key][model_name] = (time.time() + 3, "TRANSIENT_RETRY")

    def record_daily_exhausted(self, api_key: str, model_name: str):
        """Marks key as daily exhausted for a specific model."""
        with self._lock:
            self._init_key_model_dicts(api_key)
            cfg = self.get_model_config(model_name)
            limit = cfg["rpd"] if cfg else 0
            
            today = self._get_today_str()
            key_data = self.usage_data.get(api_key, {})
            if key_data.get("date") != today:
                key_data = {"date": today, "models": {}}
            models_data = key_data.get("models", {})
            models_data[model_name] = limit
            key_data["models"] = models_data
            
            self.usage_data[api_key] = key_data
            self._save()
            
            key_preview = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else api_key
            print(f"🚫 Key {key_preview} reached daily quota on {model_name}. Pausing this model until tomorrow (UTC).")

    def record_invalid_key(self, api_key: str):
        """Marks key as entirely invalid (bad API key, 400/403). Applies globally to all models."""
        with self._lock:
            self.invalid_keys.add(api_key)
            key_preview = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else api_key
            print(f"❌ Key {key_preview} is INVALID or REVOKED. Disabled completely for this session.")

    def factory_reset(self):
        """Globally resets all API keys, quotas, rate limits, and bans."""
        with self._lock:
            self.usage_data.clear()
            self.invalid_keys.clear()
            self.rpm_timestamps.clear()
            self.cooldowns.clear()
            self.consecutive_failures.clear()
            self._save()
            print("♻️ API Tracker has been factory reset.")

    def get_stats_report(self) -> str:
        """Generates a human-readable Telegram report of all API keys aggregated by model."""
        with self._lock:
            today = self._get_today_str()
            
            total_configured_keys = set(Config.GEMINI_API_KEYS)
            dead_keys_in_config = self.invalid_keys.intersection(total_configured_keys)
            
            dead_keys = len(dead_keys_in_config)
            healthy_keys = len(total_configured_keys) - dead_keys
            
            if len(total_configured_keys) == 0:
                return "📊 **گزارش لحظه‌ای وضعیت API (Gemini)**\n\nℹ️ هیچ کلیدی در تنظیمات یافت نشد."
            
            report = ["📊 **گزارش وضعیت API (Gemini)**\n"]
            report.append(f"✅ کلیدهای سالم: {healthy_keys} از {len(total_configured_keys)}")
            
            if dead_keys > 0:
                dead_previews = [f"`{k[:6]}...`" if len(k) > 10 else f"`{k}`" for k in dead_keys_in_config]
                report.append(f"❌ کلیدهای مسدود (403): {dead_keys} ({', '.join(dead_previews)})")
                
            report.append("\n**گزارش مجموع مصرف امروز:**")
            
            # Aggregate usage by model
            model_usage = {} # model_name -> count
            model_keys_used = {} # model_name -> set of keys that used it today
            
            for key, data in self.usage_data.items():
                if key in self.invalid_keys:
                    continue
                if data.get("date") == today:
                    models_data = data.get("models", {})
                    for model, count in models_data.items():
                        model_usage[model] = model_usage.get(model, 0) + count
                        if model not in model_keys_used:
                            model_keys_used[model] = set()
                        model_keys_used[model].add(key)
                        
            if not model_usage:
                report.append("🟢 کاملاً آزاد (بدون مصرف امروز برای هیچ مدلی)")
            else:
                for cfg in MODELS_CONFIG:
                    model = cfg["name"]
                    if model in model_usage:
                        used = model_usage[model]
                        keys_used_count = len(model_keys_used[model])
                        total_limit = cfg["rpd"] * healthy_keys if healthy_keys > 0 else 0
                        
                        report.append(f"🤖 `{model}`:")
                        report.append(f"   └ مصرف: {used} / {total_limit} درخواست (توسط {keys_used_count} کلید)")
            
            report.append("\n💡 *سهمیه‌ها هر روز ساعت 00:00 به وقت UTC ریست می‌شوند.*")
            return "\n".join(report)

# Global singleton instance
api_tracker = APIUsageTracker()
