import os
import json
import asyncio
from config import Config
from logger import logger

class PalManager:
    def __init__(self, state_file=Config.PAL_STATE_FILE):
        self.state_file = state_file
        self.active_chats = {} # dict: chat_id -> mode ("normal" or "lust")
        self.auto_engage_chats = {} # dict: chat_id -> duration_minutes
        self._locks = {}
        self._debounce_tasks = {}
        self.load_state()

    def load_state(self):
        """Loads active chat IDs and auto-engage chat IDs from disk."""
        if os.path.exists(self.state_file) and os.path.getsize(self.state_file) > 0:
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.active_chats = {int(chat_id): "normal" for chat_id in data}
                        self.auto_engage_chats = {}
                    elif isinstance(data, dict):
                        raw_active = data.get("active_chats", {})
                        if isinstance(raw_active, list):
                            self.active_chats = {int(chat_id): "normal" for chat_id in raw_active}
                        else:
                            self.active_chats = {int(k): str(v) for k, v in raw_active.items()}
                            
                        raw_engage = data.get("auto_engage_chats", {})
                        if isinstance(raw_engage, list):
                            self.auto_engage_chats = {int(chat_id): 20 for chat_id in raw_engage}
                        else:
                            self.auto_engage_chats = {int(k): int(v) for k, v in raw_engage.items()}
            except Exception as e:
                logger.error(f"⚠️ Error loading Pal state: {e}")
                self.active_chats = {}
                self.auto_engage_chats = {}
        else:
            self.active_chats = {}
            self.auto_engage_chats = {}

    def save_state(self):
        """Persists active chat IDs and auto-engage IDs to disk (Async Offloaded)."""
        import asyncio
        data = {
            "active_chats": self.active_chats.copy(),
            "auto_engage_chats": self.auto_engage_chats.copy()
        }
        
        def _write():
            try:
                tmp_file = f"{self.state_file}.tmp"
                with open(tmp_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                os.replace(tmp_file, self.state_file)
            except Exception as e:
                logger.error(f"⚠️ Error saving Pal state: {e}")

        try:
            loop = asyncio.get_running_loop()
            loop.run_in_executor(None, _write)
        except RuntimeError:
            _write()

    def is_active(self, chat_id: int) -> bool:
        return chat_id in self.active_chats
        
    def get_mode(self, chat_id: int) -> str:
        return self.active_chats.get(chat_id, "normal")
        
    def is_auto_engage_active(self, chat_id: int) -> bool:
        return chat_id in self.auto_engage_chats

    def activate(self, chat_id: int, mode: str = "normal") -> bool:
        """Activates Pal for a chat. Returns True if changed."""
        if self.active_chats.get(chat_id) != mode:
            self.active_chats[chat_id] = mode
            self.save_state()
            return True
        return False
        
    def activate_auto_engage(self, chat_id: int, duration_minutes: int = None) -> bool:
        """Activates Auto-Engage (Lurker) for a chat with a specific duration."""
        if duration_minutes is None:
            duration_minutes = Config.AUTO_ENGAGE_DEFAULT_DURATION_MINUTES
        if self.auto_engage_chats.get(chat_id) != duration_minutes:
            self.auto_engage_chats[chat_id] = duration_minutes
            self.save_state()
            return True
        return False

    def deactivate(self, chat_id: int) -> bool:
        """Deactivates Pal for a chat. Returns True if changed."""
        if chat_id in self.active_chats:
            del self.active_chats[chat_id]
            self.save_state()
            return True
        return False
        
    def deactivate_auto_engage(self, chat_id: int) -> bool:
        """Deactivates Auto-Engage for a chat."""
        if chat_id in self.auto_engage_chats:
            del self.auto_engage_chats[chat_id]
            self.save_state()
            return True
        return False

    def deactivate_all(self) -> int:
        """Deactivates Pal globally for all chats. Returns the number of deactivated chats."""
        count = len(self.active_chats) + len(self.auto_engage_chats)
        self.active_chats.clear()
        self.auto_engage_chats.clear()
        self.save_state()
        return count

    def deactivate_all_engages(self) -> int:
        """Deactivates Auto-Engage globally for all chats."""
        count = len(self.auto_engage_chats)
        self.auto_engage_chats.clear()
        self.save_state()
        return count

    def factory_reset(self):
        """Globally clears all Pal and Auto-Engage configurations."""
        self.active_chats.clear()
        self.auto_engage_chats.clear()
        self.save_state()
        logger.info("♻️ Pal Manager has been factory reset.")

    def get_active_count(self) -> int:
        return len(self.active_chats)
        
    def get_auto_engage_count(self) -> int:
        return len(self.auto_engage_chats)

    def calculate_typing_delay(self, text: str) -> float:
        """Calculates a realistic typing duration based on text length and punctuation."""
        from human_behavior import calculate_human_typing_delay
        return calculate_human_typing_delay(text)

    async def send_human_message(self, client, chat_id, text: str, reply_to=None):
        """
        Simulates typing status + sends message naturally.
        """
        if not text or not text.strip():
            return None
        
        text = text.strip()
        from human_behavior import ContinuousTyping, calculate_human_typing_delay
        typing_delay = calculate_human_typing_delay(text)
        
        async with ContinuousTyping(client, chat_id):
            await asyncio.sleep(typing_delay)
            if reply_to:
                return await client.send_message(chat_id, text, reply_to=reply_to)
            else:
                return await client.send_message(chat_id, text)

# Global singleton instance
pal_manager = PalManager()

