import os
import sys
import time

PROFILE = "default"
if "--profile" in sys.argv:
    try:
        idx = sys.argv.index("--profile")
        PROFILE = sys.argv[idx+1]
    except IndexError:
        pass

TARGET_ENV_FILE = f".env.{PROFILE}" if PROFILE != "default" else ".env"

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

    import os
    import shutil
    from config import TARGET_ENV_FILE, PROFILE_DIR

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
GEMINI_TTS_MODEL="gemini-3.1-flash-tts-preview"
GEMINI_STT_MODEL="models/gemini-3.5-transcribe-live"

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
    
    input("Press Enter to exit setup...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(1)
