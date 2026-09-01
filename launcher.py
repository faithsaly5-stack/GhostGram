import os
import sys
import subprocess

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    clear_screen()
    print("==================================================")
    print("  👻 GhostGram PRO - 1-Click Launcher")
    print("==================================================\n")

    # 1. Ask for profile
    profile_name = input("Enter profile name (e.g. 'work', or 'all' to start everything): ").strip()
    profile_flag = []
    env_file = ".env"
    
    if profile_name.lower() == "all":
        print("\n🚀 Starting ALL profiles concurrently...")
        subprocess.run([sys.executable, "main.py"])
        print("\n[!] Bots stopped.")
        return

    profile_name = profile_name if profile_name else "default"
    profile_flag = []
    
    if profile_name != "default":
        profile_flag = ["--profile", profile_name]
        
    env_file = os.path.join("profiles", profile_name, ".env")
        
    print("\n[1/3] Checking requirements...")
    
    # 2. Check dependencies
    try:
        import telethon
        import google.genai
        import dotenv
        print("Requirements verified!\n")
    except ImportError:
        print("Installing required packages (one-time setup)...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"])
        if result.returncode != 0:
            print("\n[ERROR] Failed to install dependencies. Please check your internet connection.")
            sys.exit(1)
        print("Requirements verified!\n")

    # 3. Setup Wizard
    if not os.path.exists(env_file):
        print(f"[2/3] Configuration file ({env_file}) not found.")
        print("Launching First-Time Setup Wizard...\n")
        
        result = subprocess.run([sys.executable, "setup.py"] + profile_flag)
        if result.returncode != 0 or not os.path.exists(env_file):
            print("\n[ERROR] Setup was cancelled or failed.")
            sys.exit(1)
            
        print("\n🎉 Setup is fully complete! You are ready to go.")
        start_now = input("Do you want to start GhostGram now? (Y/n): ").strip().lower()
        if start_now == 'n':
            sys.exit(0)
    else:
        print(f"[2/3] Configuration file ({env_file}) found.")

    # 4. Login Check
    # Check if SESSION_STRING is in the env file
    has_session = False
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            import re
            if re.search(r"SESSION_STRING=\S+", f.read()):
                has_session = True

    if not has_session:
        print("\n[2/3] Telegram authentication required...")
        result = subprocess.run([sys.executable, "login.py"] + profile_flag)
        if result.returncode != 0:
            print("\n[ERROR] Login failed.")
            sys.exit(1)

    # 5. Launch GhostGram
    print("\n==================================================")
    print("  🚀 Starting GhostGram PRO...")
    print("  (Keep this window open to keep your bot active)")
    print("==================================================\n")
    
    subprocess.run([sys.executable, "main.py"] + profile_flag)
    print("\n[!] Bot stopped.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nLauncher cancelled.")
