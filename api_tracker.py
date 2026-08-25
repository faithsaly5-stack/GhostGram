import json
import os
import time
from datetime import datetime, timezone

class APIUsageTracker:
    def __init__(self, filename="api_usage.json"):
        self.filename = filename
        self.limit = 490  # 10 requests safety buffer below Google's 500 limit
        self.rpm_limit = 15 # Google's 15 requests per minute limit per key
        
        # We only save daily usage to disk, other stats (circuit breaker, rpm) are in-memory.
        self.usage_data = self._load()
        
        # Circuit Breaker: api_key -> consecutive_errors
        self.consecutive_errors = {}
        # Ban expiry: api_key -> timestamp (seconds since epoch)
        self.banned_until = {}
        
        # RPM Tracking: api_key -> list of timestamps (seconds)
        self.rpm_timestamps = {}
        
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
                json.dump(self.usage_data, f)
        except Exception:
            pass
            
    def _get_today_str(self):
        # Google resets limits at midnight Pacific Time usually, but UTC is a safe standard
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
    def is_key_available(self, api_key: str) -> bool:
        now = time.time()
        
        # 1. Circuit Breaker Check
        if api_key in self.banned_until:
            if now < self.banned_until[api_key]:
                return False
            else:
                # Ban expired
                del self.banned_until[api_key]
                self.consecutive_errors[api_key] = 0
                
        # 2. RPM Check
        if api_key in self.rpm_timestamps:
            # Keep only timestamps from the last 60 seconds
            recent = [ts for ts in self.rpm_timestamps[api_key] if now - ts < 60]
            self.rpm_timestamps[api_key] = recent
            if len(recent) >= self.rpm_limit:
                return False
                
        # 3. Daily Limit Check
        today = self._get_today_str()
        key_data = self.usage_data.get(api_key, {})
        
        # If the key was used on a previous day, it is available (and starts at 0)
        if key_data.get("date") != today:
            return True
            
        return key_data.get("count", 0) < self.limit
        
    def record_usage(self, api_key: str):
        now = time.time()
        
        # Update RPM
        if api_key not in self.rpm_timestamps:
            self.rpm_timestamps[api_key] = []
        self.rpm_timestamps[api_key].append(now)
        
        # Update Daily
        today = self._get_today_str()
        key_data = self.usage_data.get(api_key, {})
        
        if key_data.get("date") != today:
            key_data = {"date": today, "count": 1}
        else:
            key_data["count"] = key_data.get("count", 0) + 1
            
        self.usage_data[api_key] = key_data
        self._save()

    def record_success(self, api_key: str):
        """Reset consecutive errors on success."""
        self.consecutive_errors[api_key] = 0
        
    def record_error(self, api_key: str):
        """Increment consecutive errors, ban if >= 3."""
        errors = self.consecutive_errors.get(api_key, 0) + 1
        self.consecutive_errors[api_key] = errors
        
        if errors >= 3:
            # Ban for 3 hours (10800 seconds)
            print(f"🛑 Circuit Breaker TRIPPED for key {api_key[:8]}...! Banning for 3 hours.")
            self.banned_until[api_key] = time.time() + (3 * 3600)

# Global singleton instance
api_tracker = APIUsageTracker()
