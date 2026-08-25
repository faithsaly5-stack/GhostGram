import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_ID = int(os.getenv("API_ID") or 0)
    API_HASH = os.getenv("API_HASH") or ""
    @staticmethod
    def _load_keys():
        keys = [k.strip() for k in os.getenv("GEMINI_API_KEYS", "").split(",") if k.strip()]
        if os.path.exists("apis.txt"):
            try:
                with open("apis.txt", "r", encoding="utf-8") as f:
                    file_keys = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                    for k in file_keys:
                        if k not in keys:
                            keys.append(k)
            except Exception:
                pass
        return keys

    GEMINI_API_KEYS = _load_keys()
    SESSION_NAME = os.getenv("SESSION_NAME", "teleagent_session")
    SESSION_STRING = os.getenv("SESSION_STRING", "")
    OWNER_ID = int(os.getenv("OWNER_ID") or 0)
    OWNER_NAME = os.getenv("OWNER_NAME", "User")
    OWNER_BIO = os.getenv("OWNER_BIO", "دانشجو و پژوهشگر")
    OWNER_WEBSITE = os.getenv("OWNER_WEBSITE", "yourwebsite.com")
    OWNER_SERVICES = os.getenv("OWNER_SERVICES", "مشاوره، برنامه‌نویسی و طراحی پروژه")
    OWNER_INTERESTS = os.getenv("OWNER_INTERESTS", "موسیقی، ادبیات، تحلیل و گفتگو")
    PHONE_NUMBER = os.getenv("PHONE_NUMBER", "")
    PAL_STATE_FILE = os.getenv("PAL_STATE_FILE", "pal_state.json")
    ASSISTANT_STATE_FILE = os.getenv("ASSISTANT_STATE_FILE", "assistant_state.json")
    MEMORY_STATE_FILE = os.getenv("MEMORY_STATE_FILE", "memory_state.json")
    SHORT_TERM_MEMORY_LIMIT = int(os.getenv("SHORT_TERM_MEMORY_LIMIT", "30"))
    LONG_TERM_SUMMARY_INTERVAL = int(os.getenv("LONG_TERM_SUMMARY_INTERVAL", "30"))
    MAX_LONG_TERM_SUMMARY_CHARS = int(os.getenv("MAX_LONG_TERM_SUMMARY_CHARS", "600"))
    MAX_MESSAGE_SEGMENT_CHARS = int(os.getenv("MAX_MESSAGE_SEGMENT_CHARS", "200"))
    TYPING_SPEED_CPS = float(os.getenv("TYPING_SPEED_CPS", "18.0"))  # characters typed per second
    MIN_TYPING_DELAY = float(os.getenv("MIN_TYPING_DELAY", "1.5"))   # seconds
    MAX_TYPING_DELAY = float(os.getenv("MAX_TYPING_DELAY", "7.0"))   # seconds

