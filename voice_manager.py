import os
import json
from config import Config

VOICES = [
    "Achernar", "Achird", "Algenib", "Algieba", "Alnilam", "Aoede",
    "Autonoe", "Callirrhoe", "Charon", "Despina", "Enceladus", "Erinome",
    "Fenrir", "Gacrux", "Iapetus", "Kore", "Laomedeia", "Leda", "Orus",
    "Puck", "Pulcherrima", "Rasalgethi", "Sadachbia", "Sadaltager",
    "Schedar", "Sulafat", "Umbriel", "Vindemiatrix", "Zephyr", "Zubenelgenubi"
]

class VoiceManager:
    def __init__(self):
        self.state_file = os.path.join(Config.PROFILE_DIR, "voice_state.json")
        self.voices = VOICES
        self.default_index = 6 # Aoede is index 6
        
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
        import asyncio
        data = {
            "voice_index": self.current_index,
            "voice_changer_active": self.voice_changer_active
        }
        
        def _write():
            try:
                tmp_file = f"{self.state_file}.tmp"
                with open(tmp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
                os.replace(tmp_file, self.state_file)
            except Exception:
                pass

        try:
            loop = asyncio.get_running_loop()
            loop.run_in_executor(None, _write)
            return True
        except RuntimeError:
            _write()
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
        return None

voice_manager = VoiceManager()
