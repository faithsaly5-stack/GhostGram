import os
import sys
import time

from config import PROFILE, PROFILE_DIR, TARGET_ENV_FILE

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print("=" * 60)
    print("👻 GHOSTGRAM PRO (روح‌گرام) - FIRST TIME SETUP WIZARD")
    print("=" * 60)
    print("Welcome to GhostGram! Let's get your autonomous Telegram bot")
    print("configured and ready for deployment.\n")

def check_existing_setup():
    if os.path.exists(TARGET_ENV_FILE) and os.path.getsize(TARGET_ENV_FILE) > 50:
        with open(TARGET_ENV_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            if "YOUR_API_ID" not in content and "YOUR_VPS_IP" not in content:
                print(f"⚠️  WARNING: A valid {TARGET_ENV_FILE} configuration already exists!")
                print("Running this setup will overwrite your current settings.\n")
                choice = input("Do you want to reconfigure? (y/N): ").strip().lower()
                if choice != 'y':
                    print("\n✅ Setup aborted. Your existing configuration is safe.")
                    sys.exit(0)
                print("\n")

def ask(prompt, default=""):
    if default:
        val = input(f"{prompt} [{default}]: ").strip()
        return val if val else default
    else:
        while True:
            val = input(f"{prompt}: ").strip()
            if val:
                return val
            print("❌ This field is required.")

def main():
    clear_screen()
    print_banner()
    check_existing_setup()

    print("--- 1. Telegram API Credentials ---")
    print("Get these from https://my.telegram.org/apps")
    api_id = ask("Telegram API_ID", default="2040")
    api_hash = ask("Telegram API_HASH", default="b18441a1ff607e10a989891a5462e627")
    phone = ask("Telegram Phone Number (with +countrycode)")
    owner_id = ask("Your Telegram User ID (numeric, get from @userinfobot)")
    
    print("\n--- 2. Gemini API Configuration ---")
    print("Get your API key from Google AI Studio (aistudio.google.com)")
    gemini_key = ask("Gemini API Key")
    
    print("\n--- 3. Telegram Session (Optional) ---")
    print("If you already have a SESSION_STRING, paste it here to skip login.")
    print("If you want to log in normally via Telegram code, just press Enter.")
    session_string = input("SESSION_STRING (leave blank for normal login): ").strip()

    import shutil
    print(f"\n💾 Saving configuration to {TARGET_ENV_FILE}...")
    
    env_content = f"""API_ID={api_id}
API_HASH={api_hash}
PHONE_NUMBER={phone}
OWNER_ID={owner_id}

# 📝 EDIT THESE VALUES IN YOUR TEXT EDITOR (Supports Persian/Farsi perfectly)
OWNER_FIRST_NAME=Your First Name / نام شما
OWNER_LAST_NAME=Your Last Name / نام خانوادگی شما
OWNER_BIO=دانشجو و برنامه‌نویس
OWNER_WEBSITE=yourwebsite.com
OWNER_SERVICES=مشاوره، برنامه‌نویسی و طراحی پروژه
OWNER_INTERESTS=موسیقی، کتاب، تکنولوژی و گفتگو

GEMINI_API_KEYS={gemini_key}

# 🧠 Gemini Models Cascade Configuration
# Format: model_name:rpm:rpd,model_name2:rpm:rpd
# To disable a model, simply remove it from this comma-separated list!
GEMINI_MODELS="gemini-3.6-flash:5:20,gemini-3.5-flash:5:20,gemini-3-flash-preview:5:20,gemini-2.5-flash:5:20,gemini-3.5-flash-lite:15:500,gemini-3.1-flash-lite:15:500,gemini-2.5-flash-lite:10:20"

# 🎤 Voice/Audio Models Configuration
# GEMINI_TTS_MODELS: Comma-separated list of TTS models to cascade across if primary fails.
GEMINI_TTS_MODELS="gemini-3.1-flash-tts-preview"
GEMINI_TTS_MODEL="gemini-3.1-flash-tts-preview"
GEMINI_STT_MODEL="models/gemini-3.5-transcribe-live"

# 🧠 Memory & Processing Tuning
# SHORT_TERM_MEMORY_LIMIT: How many of YOUR recent messages to scan to avoid the AI repeating itself.
# Unit: Message Count (e.g., 30 = looks at the last 30 messages you sent)
SHORT_TERM_MEMORY_LIMIT=30
# LONG_TERM_SUMMARY_INTERVAL: Trigger long-term memory compression after this many messages.
# Unit: Message Count (e.g., 30 = compresses memory every 30 messages)
LONG_TERM_SUMMARY_INTERVAL=30
# LONG_TERM_SUMMARY_SCAN_LIMIT: How far back the AI looks when compressing older chat history.
# Unit: Message Count (e.g., 100 = scans the last 100 messages for the summary)
LONG_TERM_SUMMARY_SCAN_LIMIT=100
# MAX_LONG_TERM_SUMMARY_CHARS: Maximum size of the long-term memory file before older memories are deleted.
# Unit: Characters (e.g., 600 = keeps around 100-150 words of core memories)
MAX_LONG_TERM_SUMMARY_CHARS=600
# MAX_MESSAGE_SEGMENT_CHARS: AI splits messages if they get too long, keeping responses looking like human texting.
# Unit: Characters (e.g., 200 = splits long paragraphs into multiple short texts)
MAX_MESSAGE_SEGMENT_CHARS=200

# ⚡ Human Simulation Engine (Ghost Engine 2.0)
# TYPING_SPEED_CPS: How fast the bot pretends to type.
# Unit: Characters Per Second (e.g., 18.0 = fast human typist)
TYPING_SPEED_CPS=18.0
# MIN_TYPING_DELAY: The absolute minimum time the bot will pretend to type, even for a 1-word reply.
# Unit: Seconds (e.g., 1.5 = waits at least 1.5 seconds)
MIN_TYPING_DELAY=1.5
# MAX_TYPING_DELAY: The absolute maximum time the bot will pretend to type, even for a massive essay.
# Unit: Seconds (e.g., 7.0 = never shows "typing..." for more than 7 seconds)
MAX_TYPING_DELAY=7.0
# MAX_DEBOUNCE_WAIT_SECONDS: How long the bot waits for the other person to finish typing before forcing a reply.
# Unit: Seconds (e.g., 45.0 = gives up waiting after 45 seconds)
MAX_DEBOUNCE_WAIT_SECONDS=45.0
# MAX_VOICE_LISTEN_DELAY_SECONDS: How long the bot pretends to "listen" to a voice note.
# Unit: Seconds (e.g., 25.0 = never pretends to listen longer than 25 seconds)
MAX_VOICE_LISTEN_DELAY_SECONDS=25.0

# --- Advanced System Tuning ---
# 🤖 AI Limits & Connectivity
# GEMINI_MAX_CHARS: Maximum text size sent to the AI per request to prevent crashes.
# Unit: Characters (e.g., 50000 = about 10,000 words)
GEMINI_MAX_CHARS=50000
# GEMINI_MAX_ATTEMPTS: How many times the bot tries switching API keys if one gets rate-limited.
# Unit: Retry Count (e.g., 20 = tries up to 20 times across all available keys)
GEMINI_MAX_ATTEMPTS=20
# GEMINI_TIMEOUT_SECONDS: How long to wait for the AI to reply before giving up and trying another key.
# Unit: Seconds (e.g., 25.0 = strict 25-second timeout)
GEMINI_TIMEOUT_SECONDS=25.0
# GEMINI_RPM_COOLDOWN_SECONDS: How long an API key cools down when hitting Google's requests-per-minute limit.
# Unit: Seconds (e.g., 15)
GEMINI_RPM_COOLDOWN_SECONDS=15

# 🗄️ System & Media
# LOG_MAX_BYTES: How large the background log file can get before it creates a new one.
# Unit: Bytes (e.g., 5242880 = exactly 5 Megabytes)
LOG_MAX_BYTES=5242880
# LOG_BACKUP_COUNT: How many old log files to keep before deleting the oldest ones.
# Unit: File Count (e.g., 3 = keeps 3 historical logs)
LOG_BACKUP_COUNT=3
# FFMPEG_TIMEOUT_SECONDS: Maximum time allowed to convert a voice note before killing the process.
# Unit: Seconds (e.g., 120 = gives up on broken audio after 2 minutes)
FFMPEG_TIMEOUT_SECONDS=120

# ⚡ Behavior & Automation
# AUTO_ENGAGE_INTERVAL_MINUTES: How long you must be offline before the bot starts talking on your behalf.
# Unit: Minutes (e.g., 30 = takes over if you haven't spoken in half an hour)
AUTO_ENGAGE_INTERVAL_MINUTES=30
# AUTO_ENGAGE_DEFAULT_DURATION_MINUTES: How long the bot stays active in a chat once triggered.
# Unit: Minutes (e.g., 20 = chats for 20 minutes then goes back to sleep)
AUTO_ENGAGE_DEFAULT_DURATION_MINUTES=20
# AUTO_ENGAGE_LOOP_INTERVAL_SECONDS: How often the bot wakes up in the background to check if it should talk.
# Unit: Seconds (e.g., 60 = checks every 1 minute)
AUTO_ENGAGE_LOOP_INTERVAL_SECONDS=60
# FATAL_ERROR_RETRY_SECONDS: If the bot crashes, how long it waits before rebooting the background loop.
# Unit: Seconds (e.g., 60 = reboots after 1 minute)
FATAL_ERROR_RETRY_SECONDS=60
# GHOST_PURGE_SCAN_LIMIT: How many messages the bot scrolls back to delete when you use the purge command.
# Unit: Message Count (e.g., 3000 = deletes your messages from the last 3000 texts in chat)
GHOST_PURGE_SCAN_LIMIT=3000
# AI_VOICE_COOLDOWN_SECONDS: Anti-spam timer preventing the bot from sending too many voice notes too fast.
# Unit: Seconds (e.g., 15 = must wait 15s between voice messages)
AI_VOICE_COOLDOWN_SECONDS=15

# 🎙️ Media & Audio Settings
# TTS_NOISE_LEVEL: The intensity of the simulated pink noise/static added to the bot's voice to make it sound like a real mic.
# Unit: Amplitude (e.g., 0.012 = subtle static, 0 = crystal clear, 0.05 = noisy room)
TTS_NOISE_LEVEL=0.012
# TTS_HIGHPASS / TTS_LOWPASS: Audio EQ filters applied to simulate a smartphone microphone frequency response.
# Unit: Hertz (Hz)
TTS_HIGHPASS=200
TTS_LOWPASS=4000
# TTS_BITRATE: Compression quality of the generated OGG audio file.
# Unit: Bitrate string (e.g., 32k = standard voice note quality, 64k = high quality)
TTS_BITRATE=32k
# TTS_DEFAULT_VOICE_INDEX: The default AI voice number used by the bot out of the TTS_VOICES list (1-indexed).
# Unit: Integer (e.g., 6 = Aoede)
TTS_DEFAULT_VOICE_INDEX=6
# TTS_VOICES: The list of Gemini TTS voice names available. You can add new ones here if Google adds them.
# Unit: Comma-separated strings
TTS_VOICES=Achernar, Achird, Algenib, Algieba, Alnilam, Aoede, Autonoe, Callirrhoe, Charon, Despina, Enceladus, Erinome, Fenrir, Gacrux, Iapetus, Kore, Laomedeia, Leda, Orus, Puck, Pulcherrima, Rasalgethi, Sadachbia, Sadaltager, Schedar, Sulafat, Umbriel, Vindemiatrix, Zephyr, Zubenelgenubi

# STT_INITIAL_TIMEOUT_SECONDS: How long the bot waits for the Gemini AI to start analyzing a large received audio file.
# Unit: Seconds (e.g., 45.0)
STT_INITIAL_TIMEOUT_SECONDS=45.0
# STT_STREAMING_TIMEOUT_SECONDS: Timeout between streaming text chunks when the AI is transcribing audio.
# Unit: Seconds (e.g., 25.0)
STT_STREAMING_TIMEOUT_SECONDS=25.0

SESSION_STRING={session_string}
"""

    if PROFILE == "default":
        env_content += """
# ☁️ Deployment Settings (Global VPS Config)
VPS_IP=127.0.0.1
SSH_USER=root
SSH_PORT=22
"""

    # Create profile directory and save env file
    os.makedirs(PROFILE_DIR, exist_ok=True)
    with open(TARGET_ENV_FILE, "w", encoding="utf-8") as f:
        f.write(env_content)
        
    # Copy default personas to profile directory
    target_personas = os.path.join(PROFILE_DIR, "personas")
    os.makedirs(target_personas, exist_ok=True)
    if os.path.exists("personas"):
        for p in os.listdir("personas"):
            src = os.path.join("personas", p)
            dst = os.path.join(target_personas, p)
            if os.path.isfile(src) and not os.path.exists(dst):
                shutil.copy2(src, dst)

    print(f"✅ {TARGET_ENV_FILE} saved successfully!\n")

    print("=" * 60)
    print("🎭 HOW PERSONAS WORK (777 Mode)")
    print("=" * 60)
    print("GhostGram can take on ANY personality you want!")
    print("1. Go into the 'personas/' folder.")
    print("2. Create a new text file (e.g. 'hacker.txt').")
    print("3. Write the personality instructions inside the text file.")
    print("4. When you chat in Telegram, activate it anytime with: 777 hacker")
    print("\nIncluded Personas: normal, academic, angry, sarcastic, poetic, drunk, tehrani, etc.\n")

    print("=" * 60)
    print("🚀 HOW TO RUN GHOSTGRAM")
    print("=" * 60)
    print("• Local Run (Windows): Simply double-click 'run.bat'")
    print("• Local Run (Terminal): Run 'python main.py'")
    print("• 24/7 VPS Deployment: Double-click 'deploy.bat'")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(1)
