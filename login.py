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
        print("\n" + "=" * 50)
        print("✅ SUCCESS! Logged in as:")
        print(f"  • Name: {me.first_name} {me.last_name or ''}")
        print(f"  • Username: @{me.username or 'No username'}")
        print(f"  • User ID: {me.id}")
        print("=" * 50 + "\n")
    except Exception as e:
        print(f"\n❌ Login failed: {e}")
        sys.exit(1)
    finally:
        if client.is_connected():
            client.disconnect()

if __name__ == "__main__":
    main()
