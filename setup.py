import os
import sys
import time

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print("=" * 60)
    print("👻 GHOSTGRAM PRO (روح‌گرام) - FIRST TIME SETUP WIZARD")
    print("=" * 60)
    print("Welcome to GhostGram! Let's get your autonomous Telegram bot")
    print("configured and ready for deployment.\n")

def check_existing_setup():
    if os.path.exists(".env") and os.path.getsize(".env") > 50:
        with open(".env", "r", encoding="utf-8") as f:
            content = f.read()
            if "YOUR_API_ID" not in content and "YOUR_VPS_IP" not in content:
                print("⚠️  WARNING: A valid .env configuration already exists!")
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
    api_id = ask("Telegram API_ID")
    api_hash = ask("Telegram API_HASH")
    phone = ask("Telegram Phone Number (with +countrycode)")
    owner_id = ask("Your Telegram User ID (numeric, get from @userinfobot)")
    owner_name = ask("Your Name / Persona Name", default="User")
    owner_bio = ask("Your Bio / Profession", default="دانشجو و برنامه‌نویس")
    owner_website = ask("Your Website / Channel (optional)", default="yourwebsite.com")
    owner_services = ask("Your Services / Skills (optional)", default="مشاوره، برنامه‌نویسی و طراحی پروژه")
    owner_interests = ask("Your Interests / Hobbies (optional)", default="موسیقی، کتاب، تکنولوژی و گفتگو")
    
    print("\n--- 2. Gemini API Configuration ---")
    print("Get your API key from Google AI Studio (aistudio.google.com)")
    gemini_key = ask("Gemini API Key")
    
    print("\n--- 3. VPS Deployment Configuration ---")
    print("If you don't have a VPS yet, you can leave these as defaults and run locally.")
    vps_ip = ask("VPS IP Address", default="127.0.0.1")
    ssh_user = ask("VPS SSH Username", default="root")
    ssh_port = ask("VPS SSH Port", default="22")

    print("\n💾 Saving configuration to .env...")
    
    env_content = f"""API_ID={api_id}
API_HASH={api_hash}
PHONE_NUMBER={phone}
OWNER_ID={owner_id}
OWNER_NAME={owner_name}
OWNER_BIO={owner_bio}
OWNER_WEBSITE={owner_website}
OWNER_SERVICES={owner_services}
OWNER_INTERESTS={owner_interests}

GEMINI_API_KEYS={gemini_key}

# 🧠 Gemini Models Cascade Configuration
# Format: model_name:rpm:rpd,model_name2:rpm:rpd
# To disable a model, simply remove it from this comma-separated list!
GEMINI_MODELS="gemini-3.6-flash:5:20,gemini-3.5-flash:5:20,gemini-3.0-flash:5:20,gemini-2.5-flash:5:20,gemini-3.5-flash-lite:15:500,gemini-3.1-flash-lite:15:500,gemini-2.5-flash-lite:10:20"

SESSION_NAME=teleagent_session

# Deployment Settings
VPS_IP={vps_ip}
SSH_USER={ssh_user}
SSH_PORT={ssh_port}
"""
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)

    print("✅ .env saved successfully!\n")

    print("=" * 60)
    print("🔐 TELEGRAM AUTHENTICATION")
    print("=" * 60)
    do_login = input("Would you like to log in to Telegram right now? (Y/n): ").strip().lower()
    if do_login != 'n':
        import login
        login.main()

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
