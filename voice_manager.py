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
        self.current_index = self._load()

    def _load(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("voice_index", self.default_index)
            except Exception:
                pass
        return self.default_index

    def save(self, index: int):
        if 1 <= index <= len(self.voices):
            self.current_index = index
            try:
                with open(self.state_file, 'w', encoding='utf-8') as f:
                    json.dump({"voice_index": self.current_index}, f)
                return True
            except Exception:
                pass
        return False
        
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
