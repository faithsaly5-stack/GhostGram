import os
import json
import asyncio
import random
from config import Config

class AssistantManager:
    def __init__(self, state_file=Config.ASSISTANT_STATE_FILE):
        self.state_file = state_file
        self.dm_enabled = False      # By default, Assistant mode is OFF
        self.active_chats = set()    # Specific group IDs where assistant is explicitly enabled
        self.muted_chats = set()     # Specific chat IDs where assistant is temporarily paused/muted by owner
        self._locks = {}
        self.load_state()

    def load_state(self):
        """Loads assistant mode settings from disk."""
        if os.path.exists(self.state_file) and os.path.getsize(self.state_file) > 0:
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.dm_enabled = bool(data.get("dm_enabled", False))
                        self.active_chats = set(data.get("active_chats", []))
                        self.muted_chats = set(data.get("muted_chats", []))
                    elif isinstance(data, list):
                        self.active_chats = set(data)
                        self.dm_enabled = False
                        self.muted_chats = set()
            except Exception as e:
                print(f"⚠️ Error loading Assistant state: {e}")
                self.dm_enabled = False
                self.active_chats = set()
                self.muted_chats = set()
        else:
            self.dm_enabled = False
            self.active_chats = set()
            self.muted_chats = set()

    def save_state(self):
        """Persists assistant state to disk atomically."""
        try:
            data = {
                "dm_enabled": self.dm_enabled,
                "active_chats": list(self.active_chats),
                "muted_chats": list(self.muted_chats)
            }
            tmp_file = f"{self.state_file}.tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_file, self.state_file)
        except Exception as e:
            print(f"⚠️ Error saving Assistant state: {e}")

    def is_active_for_chat(self, chat_id: int, is_private: bool = True) -> bool:
        """Checks if Assistant mode is active and not muted in this chat."""
        if not self.dm_enabled:
            return False
        if not is_private:
            return False
        chat_id = int(chat_id)
        if chat_id in self.muted_chats:
            return False
        return True

    def mute_chat(self, chat_id: int):
        """Mutes/stops Assistant ONLY in this chat so the owner can talk, while keeping other DMs active."""
        chat_id = int(chat_id)
        self.muted_chats.add(chat_id)
        self.save_state()
        return True

    def activate_global(self, chat_id: int = None):
        """Enables universal Assistant mode for ALL DMs, and un-mutes this specific chat if it was paused."""
        self.dm_enabled = True
        if chat_id is not None:
            chat_id = int(chat_id)
            if chat_id in self.muted_chats:
                self.muted_chats.remove(chat_id)
        self.save_state()
        return True

    def deactivate_global(self):
        """Globally disables Assistant mode across all DMs."""
        self.dm_enabled = False
        self.muted_chats.clear()
        self.save_state()
        return True

    def factory_reset(self):
        """Globally disables the assistant and un-mutes all chats."""
        self.dm_enabled = False
        self.muted_chats.clear()
        self.active_chats.clear()
        self.save_state()
        print("♻️ Assistant Manager has been factory reset.")




    def calculate_typing_delay(self, text: str) -> float:
        """Calculates a realistic typing duration based on text length and punctuation."""
        from typing_helper import calculate_human_typing_delay
        return calculate_human_typing_delay(text)

    async def send_assistant_message(self, client, chat_id, text: str, reply_to=None):
        """Simulates natural reading and typing delay before sending assistant response."""
        if not text or not text.strip():
            return None
        text = text.strip()
        from typing_helper import ContinuousTyping, calculate_human_typing_delay
        typing_delay = calculate_human_typing_delay(text)
        
        async with ContinuousTyping(client, chat_id):
            await asyncio.sleep(typing_delay)
            if reply_to:
                return await client.send_message(chat_id, text, reply_to=reply_to)
            else:
                return await client.send_message(chat_id, text)

# Global singleton instance
assistant_manager = AssistantManager()

