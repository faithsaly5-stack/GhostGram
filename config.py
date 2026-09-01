import os
import sys
from dotenv import load_dotenv

# --- MULTI-PROFILE SUPPORT ---
PROFILE = "default"
if "--profile" in sys.argv:
    try:
        idx = sys.argv.index("--profile")
        PROFILE = sys.argv[idx+1]
    except IndexError:
        pass
elif os.getenv("TELEAGENT_PROFILE"):
    PROFILE = os.getenv("TELEAGENT_PROFILE")

TARGET_ENV_FILE = os.path.join("profiles", PROFILE, ".env")
PROFILE_DIR = os.path.join("profiles", PROFILE)

class Config:
    PROFILE = PROFILE
    PROFILE_DIR = PROFILE_DIR
    TARGET_ENV_FILE = TARGET_ENV_FILE
    
    # Ensure profile directory exists
    if not os.path.exists(PROFILE_DIR):
        os.makedirs(PROFILE_DIR, exist_ok=True)
    
    if os.path.exists(TARGET_ENV_FILE):
        load_dotenv(TARGET_ENV_FILE, override=True)
    else:
        load_dotenv(override=True)
    
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
    GEMINI_MODELS = os.getenv("GEMINI_MODELS", "")
    GEMINI_TTS_MODEL = os.getenv("GEMINI_TTS_MODEL", "gemini-3.1-flash-tts-preview")
    GEMINI_STT_MODEL = os.getenv("GEMINI_STT_MODEL", "models/gemini-3.5-transcribe-live")
    
    SESSION_NAME = os.path.join(PROFILE_DIR, "teleagent_session")
    SESSION_STRING = os.getenv("SESSION_STRING", "")
    OWNER_ID = int(os.getenv("OWNER_ID") or 0)
    OWNER_FIRST_NAME = os.getenv("OWNER_FIRST_NAME", "User")
    OWNER_LAST_NAME = os.getenv("OWNER_LAST_NAME", "")
    OWNER_BIO = os.getenv("OWNER_BIO", "دانشجو و پژوهشگر")
    OWNER_WEBSITE = os.getenv("OWNER_WEBSITE", "yourwebsite.com")
    OWNER_SERVICES = os.getenv("OWNER_SERVICES", "مشاوره، برنامه‌نویسی و طراحی پروژه")
    OWNER_INTERESTS = os.getenv("OWNER_INTERESTS", "موسیقی، ادبیات، تحلیل و گفتگو")
    PHONE_NUMBER = os.getenv("PHONE_NUMBER", "")
    PAL_STATE_FILE = os.getenv("PAL_STATE_FILE", os.path.join(PROFILE_DIR, "pal_state.json"))
    ASSISTANT_STATE_FILE = os.getenv("ASSISTANT_STATE_FILE", os.path.join(PROFILE_DIR, "assistant_state.json"))
    MEMORY_STATE_FILE = os.getenv("MEMORY_STATE_FILE", os.path.join(PROFILE_DIR, "memory_state.json"))
    API_USAGE_FILE = os.getenv("API_USAGE_FILE", os.path.join(PROFILE_DIR, "api_usage.json"))
    
    SHORT_TERM_MEMORY_LIMIT = int(os.getenv("SHORT_TERM_MEMORY_LIMIT", "30"))
    LONG_TERM_SUMMARY_INTERVAL = int(os.getenv("LONG_TERM_SUMMARY_INTERVAL", "30"))
    MAX_LONG_TERM_SUMMARY_CHARS = int(os.getenv("MAX_LONG_TERM_SUMMARY_CHARS", "600"))
    MAX_MESSAGE_SEGMENT_CHARS = int(os.getenv("MAX_MESSAGE_SEGMENT_CHARS", "200"))
    TYPING_SPEED_CPS = float(os.getenv("TYPING_SPEED_CPS", "18.0"))  # characters typed per second
    MIN_TYPING_DELAY = float(os.getenv("MIN_TYPING_DELAY", "1.5"))   # seconds
    MAX_TYPING_DELAY = float(os.getenv("MAX_TYPING_DELAY", "7.0"))   # seconds
    
    # --- Advanced System Tuning ---
    # AI Limits & Connectivity
    GEMINI_MAX_CHARS = int(os.getenv("GEMINI_MAX_CHARS", "50000"))
    GEMINI_MAX_ATTEMPTS = int(os.getenv("GEMINI_MAX_ATTEMPTS", "20"))
    GEMINI_TIMEOUT_SECONDS = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "25.0"))
    
    # System & Media
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "5242880"))
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "3"))
    FFMPEG_TIMEOUT_SECONDS = int(os.getenv("FFMPEG_TIMEOUT_SECONDS", "120"))
    
    # Behavior & Automation
    AUTO_ENGAGE_INTERVAL_MINUTES = int(os.getenv("AUTO_ENGAGE_INTERVAL_MINUTES", "30"))
    GHOST_PURGE_SCAN_LIMIT = int(os.getenv("GHOST_PURGE_SCAN_LIMIT", "3000"))
    AI_VOICE_COOLDOWN_SECONDS = int(os.getenv("AI_VOICE_COOLDOWN_SECONDS", "15"))
