import os
import sys
from telethon import TelegramClient
from config import Config

def main():
    print("\n" + "=" * 50)
    print("🔐 TELEGRAM AUTHENTICATION")
    print("=" * 50)
    
    if not Config.API_ID or not Config.API_HASH:
        print("\n❌ Error: Missing API_ID or API_HASH in .env!")
        sys.exit(1)

    phone = Config.PHONE_NUMBER
    if not phone:
        print("\n❌ Error: Missing PHONE_NUMBER in .env!")
        sys.exit(1)

    print(f"API_ID: {Config.API_ID}")
    print(f"Phone Number: {phone}")
    print("-" * 50)
    print("Connecting to Telegram...")
    
    client = TelegramClient(Config.SESSION_NAME, Config.API_ID, Config.API_HASH)
    
    try:
        # client.start() automatically connects, checks auth, and only prompts for code if needed
        client.start(phone=phone)
        me = client.loop.run_until_complete(client.get_me())
        
        # Export StringSession for cloud platforms
        from telethon.sessions import StringSession
        string_session = StringSession.save(client.session)
        
        # Save string_session to the .env file automatically
        from config import TARGET_ENV_FILE
        if os.path.exists(TARGET_ENV_FILE):
            with open(TARGET_ENV_FILE, "r", encoding="utf-8") as f:
                env_content = f.read()
            
            if "SESSION_STRING=" in env_content:
                import re
                env_content = re.sub(r"SESSION_STRING=.*", f"SESSION_STRING={string_session}", env_content)
            else:
                env_content += f"\nSESSION_STRING={string_session}\n"
                
            with open(TARGET_ENV_FILE, "w", encoding="utf-8") as f:
                f.write(env_content)

        print("\n" + "=" * 50)
        print("✅ SUCCESS! Logged in as:")
        print(f"  • Name: {me.first_name} {me.last_name or ''}")
        print(f"  • Username: @{me.username or 'No username'}")
        print(f"  • User ID: {me.id}")
        print("=" * 50)
        print("\n☁️ The SESSION_STRING has been automatically securely saved to your .env file!")
        print("You can now safely deploy to Railway/Render/VPS using just your .env file.")
        print("-" * 50 + "\n")
    except Exception as e:
        print(f"\n❌ Login failed: {e}")
        sys.exit(1)
    finally:
        if client.is_connected():
            client.disconnect()
            
        # Automatically delete the obsolete SQLite session file to keep the folder clean
        session_file = f"{Config.SESSION_NAME}.session"
        journal_file = f"{Config.SESSION_NAME}.session-journal"
        for f in [session_file, journal_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                    print(f"🧹 Cleaned up temporary session database: {f}")
                except Exception:
                    pass

if __name__ == "__main__":
    main()
