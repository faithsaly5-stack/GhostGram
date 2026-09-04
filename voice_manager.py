import os
import json
from config import Config

VOICES = Config.TTS_VOICES

class VoiceManager:
    def __init__(self):
        self.state_file = os.path.join(Config.PROFILE_DIR, "voice_state.json")
        self.voices = VOICES
        self.default_index = Config.TTS_DEFAULT_VOICE_INDEX
        
        saved_data = self._load()
        self.current_index = saved_data.get("voice_index", self.default_index)
        self.voice_changer_active = saved_data.get("voice_changer_active", False)

    def _load(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save(self):
        import threading
        if not hasattr(self, '_write_lock'):
            self._write_lock = threading.Lock()
            self._save_timer = None
            
        self._latest_snapshot = {
            "voice_index": self.current_index,
            "voice_changer_active": self.voice_changer_active
        }
        
        if self._save_timer is not None and self._save_timer.is_alive():
            return True
            
        def _write_task():
            with self._write_lock:
                try:
                    data = getattr(self, '_latest_snapshot', {})
                    tmp_file = f"{self.state_file}.tmp"
                    with open(tmp_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f)
                    os.replace(tmp_file, self.state_file)
                except Exception:
                    pass

        self._save_timer = threading.Timer(3.0, _write_task)
        self._save_timer.start()
        return True

    def set_voice(self, index: int):
        if 1 <= index <= len(self.voices):
            self.current_index = index
            return self.save()
        return False
        
    def toggle_voice_changer(self) -> bool:
        self.voice_changer_active = not self.voice_changer_active
        self.save()
        return self.voice_changer_active
        
    def get_current_voice(self) -> str:
        idx = self.current_index - 1
        if 0 <= idx < len(self.voices):
            return self.voices[idx]
        return self.voices[self.default_index - 1]

    def get_voice_by_index(self, index: int) -> str:
        idx = index - 1
        if 0 <= idx < len(self.voices):
            return self.voices[idx]
        return self.get_current_voice()
    def factory_reset(self):
        """Resets voice index to default and deactivates voice changer."""
        self.current_index = self.default_index
        self.voice_changer_active = False
        self.save()

voice_manager = VoiceManager()
