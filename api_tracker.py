import json
import os
import time
import threading
from datetime import datetime, timezone

class APIUsageTracker:
    def __init__(self, filename="api_usage.json"):
        self.filename = filename
        self.daily_limit = 495  # Google free tier daily cap is 500 requests per key
        self.rpm_limit = 15     # Google free tier rate limit is 15 requests per minute
        self._lock = threading.Lock()
        
        # Persistent daily count
        self.usage_data = self._load()
        
        # In-memory tracking
        # cooldowns: api_key -> (timestamp_until, reason_str)
        self.cooldowns = {}
        # consecutive transient failures: api_key -> int
        self.consecutive_failures = {}
        # RPM timestamps: api_key -> list of float timestamps (last 60s)
        self.rpm_timestamps = {}
        # Permanently invalid keys (400/403 bad keys): set of api_keys
        self.invalid_keys = set()

    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save(self):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception:
            pass

    def _get_today_str(self):
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def is_key_available(self, api_key: str) -> bool:
        """Checks if a key is ready for immediate execution."""
        with self._lock:
            if api_key in self.invalid_keys:
                return False

            now = time.time()

            # 1. Cooldown check
            if api_key in self.cooldowns:
                exp_time, reason = self.cooldowns[api_key]
                if now < exp_time:
                    return False
                else:
                    # Cooldown expired naturally
                    del self.cooldowns[api_key]
                    self.consecutive_failures[api_key] = 0

            # 2. RPM check (last 60 seconds)
            if api_key in self.rpm_timestamps:
                recent = [ts for ts in self.rpm_timestamps[api_key] if now - ts < 60]
                self.rpm_timestamps[api_key] = recent
                if len(recent) >= self.rpm_limit:
                    return False

            # 3. Daily Limit check
            today = self._get_today_str()
            key_data = self.usage_data.get(api_key, {})
            if key_data.get("date") != today:
                return True

            return key_data.get("count", 0) < self.daily_limit

    def is_key_daily_exhausted(self, api_key: str) -> bool:
        """Checks if key reached its hard daily 500 requests limit."""
        with self._lock:
            if api_key in self.invalid_keys:
                return True
            today = self._get_today_str()
            key_data = self.usage_data.get(api_key, {})
            if key_data.get("date") == today:
                return key_data.get("count", 0) >= self.daily_limit
            return False

    def get_next_cooldown_wait(self, keys: list[str]) -> float:
        """Returns the minimum seconds to wait for the next key to recover from cooldown."""
        with self._lock:
            now = time.time()
            waits = []
            for k in keys:
                if k in self.invalid_keys:
                    continue
                if self.is_key_daily_exhausted(k):
                    continue
                if k in self.cooldowns:
                    rem = self.cooldowns[k][0] - now
                    if rem > 0:
                        waits.append(rem)
                elif k in self.rpm_timestamps and len(self.rpm_timestamps[k]) >= self.rpm_limit:
                    oldest = min(self.rpm_timestamps[k])
                    rem = 60 - (now - oldest)
                    if rem > 0:
                        waits.append(rem)
            return min(waits) if waits else 5.0

    def record_success(self, api_key: str):
        """Records a successful request, updates RPM and daily usage."""
        with self._lock:
            now = time.time()
            self.consecutive_failures[api_key] = 0
            if api_key in self.cooldowns:
                del self.cooldowns[api_key]

            # Update RPM
            if api_key not in self.rpm_timestamps:
                self.rpm_timestamps[api_key] = []
            self.rpm_timestamps[api_key].append(now)

            # Update Daily persistent count
            today = self._get_today_str()
            key_data = self.usage_data.get(api_key, {})
            if key_data.get("date") != today:
                key_data = {"date": today, "count": 1}
            else:
                key_data["count"] = key_data.get("count", 0) + 1

            self.usage_data[api_key] = key_data
            self._save()

    def record_rate_limit(self, api_key: str, cooldown_seconds: int = 45):
        """Temporary 429 / 15 RPM cooldown (NOT a permanent ban)."""
        with self._lock:
            key_preview = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else api_key
            print(f"⏳ Key {key_preview} reached 15 RPM rate limit. Cooling down for {cooldown_seconds}s...")
            self.cooldowns[api_key] = (time.time() + cooldown_seconds, "RATE_LIMIT")

    def record_network_error(self, api_key: str):
        """Handles transient network errors or timeouts gracefully."""
        with self._lock:
            fails = self.consecutive_failures.get(api_key, 0) + 1
            self.consecutive_failures[api_key] = fails
            key_preview = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else api_key

            if fails >= 4:
                # Put on a gentle 60-second rest if multiple consecutive network timeouts occur
                print(f"⚠️ Key {key_preview} had {fails} consecutive network errors. Resting for 60s.")
                self.cooldowns[api_key] = (time.time() + 60, "NETWORK_FAILURES")
            else:
                # Brief 5-second pause to let network recover
                self.cooldowns[api_key] = (time.time() + 5, "TRANSIENT_RETRY")

    def record_daily_exhausted(self, api_key: str):
        """Marks key as daily exhausted (500 requests reached)."""
        with self._lock:
            today = self._get_today_str()
            self.usage_data[api_key] = {"date": today, "count": self.daily_limit}
            self._save()
            key_preview = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else api_key
            print(f"🚫 Key {key_preview} reached daily quota. Pausing until tomorrow (UTC).")

    def record_invalid_key(self, api_key: str):
        """Marks key as invalid (bad API key, 400/403)."""
        with self._lock:
            self.invalid_keys.add(api_key)
            key_preview = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else api_key
            print(f"❌ Key {key_preview} is INVALID or REVOKED. Disabled for this session.")

# Global singleton instance
api_tracker = APIUsageTracker()
