import asyncio
import re
import json
from datetime import datetime, timezone
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import MessageIdInvalidError, FloodWaitError
from config import Config
from text import Text
from prompt import Prompt
from persona_manager import persona_manager
from gemini_engine import gemini
from pal_manager import pal_manager
from assistant_manager import assistant_manager
from memory_manager import memory_manager
from typing_helper import ContinuousTyping, calculate_human_typing_delay
from time_utils import get_current_persian_datetime
import random

session_target = StringSession(Config.SESSION_STRING) if Config.SESSION_STRING else Config.SESSION_NAME
client = TelegramClient(session_target, Config.API_ID, Config.API_HASH)
my_info = None

def is_owner(event) -> bool:
    """Strict check to ensure commands only run for the owner (outgoing messages from this account)."""
    return bool(event and event.out)

async def get_response(user_message: str, system_prompt: str = None, is_json: bool = False) -> str:
    if system_prompt is None:
        system_prompt = persona_manager.get_prompt("normal")
    return await gemini.get_response(user_message, system_prompt, is_json=is_json)

async def format_sender_name(sender, my_id: int) -> str:
    if not sender:
        return Text.UNKNOWN_SENDER
    if sender.id == my_id:
        return Text.ME_LABEL
    if hasattr(sender, 'first_name') and sender.first_name:
        name = sender.first_name
        if hasattr(sender, 'last_name') and sender.last_name:
            name += f" {sender.last_name}"
        return name
    if hasattr(sender, 'title') and sender.title:
        return sender.title
    return Text.UNKNOWN_SENDER

async def get_recent_chat_history(chat_id: int, limit: int = None, include_id: bool = False) -> str:
    """Fetches up to 30 recent messages with smart long-message segmentation and reset cutoff."""
    global my_info
    my_id = my_info.id if my_info else Config.OWNER_ID
    if limit is None:
        limit = Config.SHORT_TERM_MEMORY_LIMIT
    return await memory_manager.get_chat_history(client, chat_id, format_sender_name, my_id, limit=limit, include_id=include_id)

async def get_reply_chain(message):
    chain = []
    current_msg = message
    global my_info
    my_id = my_info.id if my_info else Config.OWNER_ID
    
    while current_msg:
        sender = await current_msg.get_sender()
        name = await format_sender_name(sender, my_id)
        text = current_msg.text or Text.NO_TEXT
        time_str = current_msg.date.strftime("%Y-%m-%d %H:%M:%S")
        
        formatted_msg = Text.CHAIN_TEMPLATE.format(
            time=time_str,
            sender=name,
            message=text
        )
        chain.append(formatted_msg)
        current_msg = await current_msg.get_reply_message()
    
    return list(reversed(chain))

def normalize_digits(text: str) -> str:
    """Normalizes Persian/Arabic digits, ZWNJ, and whitespace to standard ASCII format."""
    if not text:
        return ""
    mapping = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
    }
    cleaned = text.replace('\u200c', ' ').replace('\u00a0', ' ')
    for char, digit in mapping.items():
        cleaned = cleaned.replace(char, digit)
    return re.sub(r'\s+', ' ', cleaned).strip()

# ==========================================================
# 🎮 OUTGOING COMMAND HANDLERS
# ==========================================================

async def handle_help(event):
    await event.edit(Text.HELP)

async def handle_pal_on(event, mode="normal"):
    chat_id = event.chat_id
    pal_manager.activate(chat_id, mode=mode)
    try:
        await event.delete()
    except Exception:
        pass
    print(f"🔮 Stealth Pal ({mode.upper()} Mode) ACTIVATED for chat {chat_id}")

async def handle_pal_off(event, is_all=False):
    if is_all:
        count = pal_manager.deactivate_all()
        print(f"💤 Stealth Pal DEACTIVATED globally for all {count} chats")
    else:
        chat_id = event.chat_id
        pal_manager.deactivate(chat_id)
        print(f"💤 Stealth Pal DEACTIVATED for chat {chat_id}")
    try:
        await event.delete()
    except Exception:
        pass

async def calculate_dynamic_engage_duration(client, chat_id: int) -> int:
    """Calculates the best auto-engage duration based on chat speed (targeting ~5% bot presence)."""
    try:
        messages = await client.get_messages(chat_id, limit=50)
        if len(messages) < 10:
            return 20 # Fallback if there are too few messages
            
        oldest_msg = messages[-1]
        newest_msg = messages[0]
        
        timespan_seconds = (newest_msg.date - oldest_msg.date).total_seconds()
        timespan_minutes = timespan_seconds / 60.0
        
        if timespan_minutes <= 0:
            return 2
            
        mins_per_msg = timespan_minutes / len(messages)
        
        # Target: 1 bot message for every 20 human messages (5% presence)
        target_duration = int(mins_per_msg * 20)
        
        # Clamp between 2 and 120 minutes
        return max(2, min(target_duration, 120))
    except Exception as e:
        print(f"⚠️ Error calculating dynamic duration for {chat_id}: {e}")
        return 20 # Safe fallback

async def handle_auto_engage_on(event, duration=20):
    chat_id = event.chat_id
    if duration < 1:
        duration = 1
    pal_manager.activate_auto_engage(chat_id, duration)
    try:
        await event.delete()
    except Exception:
        pass
    print(f"🕵️ Auto-Engage (Lurker) ACTIVATED for chat {chat_id} with duration {duration}m")

async def handle_auto_engage_off(event, is_all=False):
    if is_all:
        count = pal_manager.deactivate_all_engages()
        print(f"🛑 Auto-Engage DEACTIVATED globally for all {count} chats")
    else:
        chat_id = event.chat_id
        pal_manager.deactivate_auto_engage(chat_id)
        print(f"🛑 Auto-Engage (Lurker) DEACTIVATED for chat {chat_id}")
    try:
        await event.delete()
    except Exception:
        pass

async def handle_assistant_on(event):
    chat_id = event.chat_id
    assistant_manager.activate_global(chat_id=chat_id)
    try:
        await event.delete()
    except Exception:
        pass
    print(f"💼 Universal Assistant Mode ACTIVATED for all DMs (un-muted {chat_id})")

async def handle_assistant_off(event, is_all=False):
    chat_id = event.chat_id
    if is_all:
        assistant_manager.deactivate_global()
        print(f"🛑 Universal Assistant Mode DEACTIVATED globally for all DMs")
    else:
        assistant_manager.mute_chat(chat_id)
        print(f"🤫 Assistant MUTED only in chat {chat_id} (All other DMs remain active)")
    try:
        await event.delete()
    except Exception:
        pass

async def handle_status(event):
    is_pal = pal_manager.is_active(event.chat_id)
    is_engage = pal_manager.is_auto_engage_active(event.chat_id)
    pal_count = pal_manager.get_active_count()
    engage_count = pal_manager.get_auto_engage_count()
    
    pal_status = Text.PAL_STATUS_ACTIVE if is_pal else Text.PAL_STATUS_INACTIVE
    engage_status = "🟢 **وضعیت تعامل خودکار:** در این چت **فعال** است." if is_engage else "⚪ **وضعیت تعامل خودکار:** در این چت **غیرفعال** است."
    
    if event.chat_id in assistant_manager.muted_chats:
        ast_status = "🟡 **دستیار در این چت:** 🤫 **متوقف شده** (برای سایر پیوی‌ها همچنان فعال است)"
    elif assistant_manager.dm_enabled:
        ast_status = "🟢 **دستیار شخصی (666):** برای **تمام پیوی‌ها (مخاطبان فعلی و آینده)** فعال است."
    else:
        ast_status = "⚪ **دستیار شخصی (666):** **غیرفعال** است."
    
    report = (
        f"📊 **گزارش وضعیت هوش مصنوعی:**\n\n"
        f"{pal_status}\n"
        f"📱 تعداد چت‌های فعال برای رفیق (777): `{pal_count}`\n\n"
        f"{engage_status}\n"
        f"🕵️ تعداد چت‌های فعال تعامل خودکار (engage): `{engage_count}`\n\n"
        f"{ast_status}"
    )
    msg = await event.edit(report)
    await asyncio.sleep(4)
    try:
        await msg.delete()
    except Exception:
        pass

async def handle_reset_memory(event):
    chat_id = event.chat_id
    memory_manager.reset_chat_memory(chat_id)
    try:
        await event.delete()
    except Exception:
        pass
    print(f"🧠 Short-term memory RESET for chat {chat_id}")

async def handle_factory_reset(event):
    from api_tracker import api_tracker
    api_tracker.factory_reset()
    memory_manager.factory_reset()
    pal_manager.factory_reset()
    assistant_manager.factory_reset()
    
    try:
        await event.delete()
    except Exception:
        pass
        
    msg = await event.respond("♻️ **سیستم با موفقیت ریست کارخانه شد!**\n\n✅ وضعیت تمام کلیدهای API صفر شد.\n✅ تمام چت‌های فعال غیرفعال شدند.\n✅ حافظه‌های بلندمدت و کوتاه‌مدت تمام گروه‌ها پاک شد.")
    await asyncio.sleep(5)
    try:
        await msg.delete()
    except Exception:
        pass

async def handle_purge(event, limit=None):
    chat_id = event.chat_id
    trigger_id = event.id
    try:
        await event.delete()
    except Exception:
        pass
    
    global my_info
    my_id = my_info.id if my_info else (await client.get_me()).id
    
    deleted_count = 0
    
    try:
        input_chat = await event.get_input_chat()
        search_limit = limit
        
        msg_scan_count = 0
        delete_streak_count = 0
        
        async for msg in client.iter_messages(input_chat, limit=search_limit):
            msg_scan_count += 1
            
            # Simulate human scrolling / reading through chat history
            if msg_scan_count % 25 == 0:
                import random
                await asyncio.sleep(random.uniform(0.5, 1.8))
                
            if msg.id == trigger_id:
                continue
            
            is_mine = False
            if msg.out:
                is_mine = True
            elif msg.sender_id and msg.sender_id == my_id:
                is_mine = True
            elif hasattr(msg, 'from_id') and getattr(msg.from_id, 'user_id', None) == my_id:
                is_mine = True
            
            if is_mine:
                # Human-like deletion: Delete ONE by ONE
                try:
                    await client.delete_messages(input_chat, [msg.id], revoke=True)
                    deleted_count += 1
                    delete_streak_count += 1
                    
                    # 1. Normal human tap delay
                    import random
                    await asyncio.sleep(random.uniform(1.2, 3.8))
                    
                    # 2. Human fatigue / distraction break
                    if delete_streak_count >= random.randint(7, 15):
                        print(f"🧘‍♂️ Human Purge: Taking a short break after {delete_streak_count} deletes...")
                        await asyncio.sleep(random.uniform(4.5, 9.5))
                        delete_streak_count = 0
                    
                except FloodWaitError as e:
                    print(f"⏳ FloodWait in Purge. Sleeping for {e.seconds}s...")
                    await asyncio.sleep(e.seconds + random.uniform(3.0, 7.0))
                    try:
                        await client.delete_messages(input_chat, [msg.id], revoke=True)
                        deleted_count += 1
                    except Exception:
                        pass
                except Exception:
                    pass
            
        print(f"🧹 Stealth Purged {deleted_count} messages (Ultra-Human Mode) from chat {chat_id}")
    except Exception as e:
        print(f"⚠️ Purge error in chat {chat_id}: {e}")

async def handle_custom_ask(event, user_instruction=""):
    reply_to_id = event.reply_to_msg_id
    chat_id = event.chat_id
    
    try:
        await event.delete()
    except Exception:
        pass
    
    if not user_instruction and not reply_to_id:
        return
    
    history_text = await get_recent_chat_history(chat_id)
    target_text = ""
    sender_name = "مخاطب"
    
    if reply_to_id:
        reply_msg = await event.get_reply_message()
        if reply_msg:
            target_text = reply_msg.text or Text.NO_TEXT
            sender = await reply_msg.get_sender()
            sender_name = await format_sender_name(sender, my_info.id if my_info else Config.OWNER_ID)
    
    now_persian = get_current_persian_datetime()
    ltm = memory_manager.get_long_term_summary(chat_id)
    ltm_context = f"\n[خلاصه سوابق مهم قبلی]:\n{ltm}\n" if ltm else ""
    
    prompt_input = Prompt.ASK_TEMPLATE.format(
        current_time=now_persian,
        long_term_context=ltm_context,
        history_text=history_text,
        sender=sender_name,
        target_text=target_text or "گفت‌وگوی جاری",
        user_instruction=user_instruction or "پاسخ طبیعی، خودمونی و مناسب بده.",
        owner_name=Config.OWNER_NAME
    )
    
    input_chat = await event.get_input_chat()
    async with global_ai_lock:
        async with ContinuousTyping(client, input_chat):
            response = await get_response(prompt_input, persona_manager.get_prompt("normal"))
            if response and response != Text.ERROR:
                human_typing_time = calculate_human_typing_delay(response)
                await asyncio.sleep(human_typing_time)
                await client.send_message(input_chat, response, reply_to=reply_to_id)
                print(f"⚡ Handled 111 in chat {chat_id}")

# ==========================================================
# 🎯 UNIFIED OUTGOING COMMAND DISPATCHER
# ==========================================================
@client.on(events.NewMessage(outgoing=True))
async def outgoing_command_dispatcher(event):
    if not is_owner(event):
        return
    raw_text = event.text or ""
    if not raw_text.strip():
        return
        
    norm = normalize_digits(raw_text).strip()
    norm_lower = norm.lower()

    # 1. HELP (888)
    if norm_lower == "888":
        await handle_help(event)
        return

    # 2. STATUS (555)
    if norm_lower == "555":
        await handle_status(event)
        return

    # 3. API STATS (101)
    if norm_lower == "101":
        from api_tracker import api_tracker
        stats_text = api_tracker.get_stats_report()
        try:
            await event.edit(stats_text)
        except Exception:
            await event.respond(stats_text)
        return

    # 3. RESET MEMORY (333)
    if norm_lower == "333":
        await handle_reset_memory(event)
        return

    # 4. GHOST PURGE (999 [limit])
    m_purge = re.match(r'^999(?:\s+(\d+))?$', norm_lower)
    if m_purge:
        limit = int(m_purge.group(1)) if m_purge.group(1) else None
        await handle_purge(event, limit)
        return

    # 5. CUSTOM ASK (111 <prompt>)
    m_ask = re.match(r'^111(?:\s+(.*))?$', norm, re.DOTALL)
    if m_ask:
        user_inst = (m_ask.group(1) or "").strip()
        await handle_custom_ask(event, user_inst)
        return

    # 6. AUTO ENGAGE OFF (777 engage off [all])
    m_eng_off = re.match(r'^777\s+engage\s+off(?:\s+(all))?$', norm_lower)
    if m_eng_off:
        scope = m_eng_off.group(1)
        await handle_auto_engage_off(event, is_all=(scope == "all"))
        return

    # 7. AUTO ENGAGE ON (777 engage [duration|auto])
    m_eng_on = re.match(r'^777\s+engage(?:\s+(auto|\d+))?$', norm_lower)
    if m_eng_on:
        val = m_eng_on.group(1)
        if not val or val == "auto":
            msg = await event.respond("⏳ در حال سنجش سرعت چت برای تنظیم هوشمند زمان تعامل...")
            duration = await calculate_dynamic_engage_duration(client, event.chat_id)
            try:
                await msg.delete()
            except Exception:
                pass
        else:
            duration = int(val)
        await handle_auto_engage_on(event, duration)
        return

    # 8. PAL OFF (000 [all])
    m_pal_off = re.match(r'^000(?:\s+(all))?$', norm_lower)
    if m_pal_off:
        scope = m_pal_off.group(1)
        await handle_pal_off(event, is_all=(scope == "all"))
        return

    # 9. PAL ON (777 [persona])
    m_pal_on = re.match(r'^777(?:\s+(.+))?$', norm_lower)
    if m_pal_on:
        mode = m_pal_on.group(1).strip() if m_pal_on.group(1) else "normal"
        await handle_pal_on(event, mode)
        return

    # 10. ASSISTANT ON (666)
    if norm_lower == "666":
        await handle_assistant_on(event)
        return

    # 11. ASSISTANT OFF (444 [all])
    m_ast_off = re.match(r'^444(?:\s+(all))?$', norm_lower)
    if m_ast_off:
        scope = m_ast_off.group(1)
        await handle_assistant_off(event, is_all=(scope == "all"))
        return

    # 12. FACTORY RESET (222)
    if norm_lower == "222":
        await handle_factory_reset(event)
        return

# ==========================================================
# 🚀 INCOMING: پردازش پیام‌های دریافتی (PAL & ASSISTANT MODES)
# ==========================================================

@client.on(events.NewMessage())
async def global_memory_tracker(event):
    """Tracks every incoming and outgoing message in active chats for accurate long-term summarization."""
    if not event.text:
        return
        
    chat_id = event.chat_id
    
    # Only track if the chat is actively monitored (Pal, Engage, or Assistant)
    is_tracked = (
        pal_manager.is_active(chat_id) or 
        pal_manager.is_auto_engage_active(chat_id) or 
        assistant_manager.is_active_for_chat(chat_id, is_private=event.is_private)
    )
    if not is_tracked:
        return
        
    global my_info
    my_id = my_info.id if my_info else Config.OWNER_ID
    
    memory_manager.record_message_and_check_summary(client, chat_id, gemini, format_sender_name, my_id)

# Concurrency management to prevent API spam and overlapping replies
# Changed to a GLOBAL lock per user request to process ALL messages strictly sequentially one by one across the entire bot
global_ai_lock = asyncio.Lock()
chat_latest_msg = {}

def get_chat_lock(chat_id):
    return global_ai_lock

@client.on(events.NewMessage(incoming=True))
async def incoming_message_handler(event):
    chat_id = event.chat_id
    
    global my_info
    my_id = my_info.id if my_info else Config.OWNER_ID
    
    # Ignore messages from myself
    if event.out or event.sender_id == my_id:
        return

    # Ignore messages from other bots to prevent endless AI-to-AI loops
    try:
        sender = await event.get_sender()
        if sender and getattr(sender, 'bot', False):
            return
    except Exception:
        pass

    # Determine active mode: Pal Mode has precedence for specifically activated chats
    if pal_manager.is_active(chat_id):
        mode = "pal"
    elif assistant_manager.is_active_for_chat(chat_id, is_private=event.is_private):
        mode = "assistant"
    else:
        # Neither mode is active for this chat
        return
    
    # For group chats: only respond if replied to me, or mentioned
    if event.is_group or event.is_channel:
        is_reply_to_me = False
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            if reply_msg:
                if reply_msg.out or reply_msg.sender_id == my_id or getattr(reply_msg.from_id, 'user_id', None) == my_id:
                    is_reply_to_me = True
        
        is_mentioned = False
        raw_lower = (event.raw_text or "").lower()
        if my_info and my_info.username and f"@{my_info.username.lower()}" in raw_lower:
            is_mentioned = True
        if my_info and my_info.first_name and my_info.first_name.lower() in raw_lower:
            is_mentioned = True
        if Config.OWNER_NAME and Config.OWNER_NAME.lower() in raw_lower:
            is_mentioned = True
                
        # If it's a group, only reply if directly addressed or explicitly mentioned/replied
        if not (is_reply_to_me or is_mentioned):
            return

    # Check incoming content
    incoming_text = event.text or ""
    if not incoming_text.strip():
        # Might be sticker/photo without caption
        return

    # Track the latest message ID for this chat to debounce rapid spam
    chat_latest_msg[chat_id] = event.id

    # Natural reading delay proportional to incoming text length (plus a bit of random jitter)
    base_reading_time = max(1.0, len(incoming_text) * 0.04) # e.g. 50 chars = 2 seconds reading
    reading_delay = min(base_reading_time, 8.0) # max 8 seconds reading time
    await asyncio.sleep(random.uniform(reading_delay, reading_delay + 1.0))
    
    # Check if mode was turned off while we were sleeping
    if mode == "pal" and not pal_manager.is_active(chat_id):
        return
    if mode == "assistant" and not assistant_manager.is_active_for_chat(chat_id, is_private=event.is_private):
        return

    lock = get_chat_lock(chat_id)
    async with lock:
        # If a newer message arrived from this chat while we were waiting/processing,
        # skip this event. The newer event's handler will process the combined history!
        if chat_latest_msg.get(chat_id, 0) > event.id:
            return

        # Double check after obtaining lock
        if mode == "pal" and not pal_manager.is_active(chat_id):
            return
        if mode == "assistant" and not assistant_manager.is_active_for_chat(chat_id, is_private=event.is_private):
            return

        input_chat = await event.get_input_chat()
        
        # Mark messages as read naturally
        try:
            await client.send_read_acknowledge(input_chat, max_id=event.id)
        except Exception:
            pass

        # Start continuous typing immediately at the top of the chat (DMs and groups)
        async with ContinuousTyping(client, input_chat):
            # Gather history, long-term memory, and sender info
            sender = await event.get_sender()
            sender_name = await format_sender_name(sender, my_id)
            history_text = await get_recent_chat_history(chat_id)
            now_persian = get_current_persian_datetime()
            ltm = memory_manager.get_long_term_summary(chat_id)
            ltm_context = f"\n[خلاصه سوابق مهم قبلی]:\n{ltm}\n" if ltm else ""
            
            if mode == "pal":
                pal_variant = pal_manager.get_mode(chat_id)
                prompt_input = Prompt.AUTOPILOT_TEMPLATE.format(
                    current_time=now_persian,
                    long_term_context=ltm_context,
                    history_text=history_text,
                    sender=sender_name,
                    target_text=incoming_text,
                    owner_name=Config.OWNER_NAME
                )
                system_prompt = persona_manager.get_prompt(pal_variant)
                print(f"🤖 Pal Autopilot ({pal_variant.upper()}) thinking & typing for chat {chat_id} (from {sender_name})...")
            else:
                prompt_input = Prompt.ASSISTANT_TEMPLATE.format(
                    current_time=now_persian,
                    long_term_context=ltm_context,
                    history_text=history_text,
                    sender=sender_name,
                    target_text=incoming_text,
                    owner_name=Config.OWNER_NAME
                )
                system_prompt = persona_manager.get_prompt("assistant")
                print(f"💼 Personal Assistant thinking & typing for chat {chat_id} (from {sender_name})...")
            
            response = await get_response(prompt_input, system_prompt)
            
            # Re-verify mode wasn't disabled during AI generation
            if mode == "pal" and not pal_manager.is_active(chat_id):
                print(f"🛑 Dropped reply for chat {chat_id} (Pal was deactivated via 000)")
                return
            if mode == "assistant" and not assistant_manager.is_active_for_chat(chat_id, is_private=event.is_private):
                print(f"🛑 Dropped reply for chat {chat_id} (Assistant was muted/deactivated)")
                return

            if response and response != Text.ERROR:
                human_typing_time = calculate_human_typing_delay(response)
                await asyncio.sleep(human_typing_time)
                
                # Final check before actual message dispatch
                if mode == "pal" and not pal_manager.is_active(chat_id):
                    return
                if mode == "assistant" and not assistant_manager.is_active_for_chat(chat_id, is_private=event.is_private):
                    return

                reply_target = event.id if (event.is_group or event.is_channel) else None
                await client.send_message(input_chat, response, reply_to=reply_target)
                if mode == "pal":
                    print(f"✅ Pal replied naturally in chat {chat_id}")
                else:
                    print(f"✅ Assistant replied politely in chat {chat_id}")
                    


auto_engage_schedule = {} # dict: chat_id -> (next_engage_timestamp, configured_duration_minutes)

async def auto_engage_loop():
    """Background task that manages auto-engage scheduling per chat."""
    global auto_engage_schedule
    while True:
        try:
            # Smart Dispatcher Loop: Wake up every 60 seconds
            await asyncio.sleep(60)
            
            global my_info
            if not my_info:
                continue
            my_id = my_info.id
            now_ts = datetime.now(timezone.utc).timestamp()
            
            # Clean up obsolete schedules
            for chat_id in list(auto_engage_schedule.keys()):
                if chat_id not in pal_manager.auto_engage_chats:
                    del auto_engage_schedule[chat_id]

            # Iterate through configured auto-engage chats and their durations
            for chat_id, duration_minutes in list(pal_manager.auto_engage_chats.items()):
                schedule_data = auto_engage_schedule.get(chat_id)
                
                # If we don't have a schedule for this chat yet, OR if the duration changed!
                if not schedule_data or schedule_data[1] != duration_minutes:
                    # Initial delay is randomized safely
                    min_delay = min(2, duration_minutes * 0.5) * 60
                    max_delay = duration_minutes * 60
                    auto_engage_schedule[chat_id] = (now_ts + random.uniform(min_delay, max_delay), duration_minutes)
                    
                next_time, _ = auto_engage_schedule[chat_id]
                    
                # Is it time to engage for this specific chat?
                if now_ts < next_time:
                    continue # Not time yet
                    
                # IT'S TIME! Reschedule for the next cycle immediately
                next_delay = random.uniform(duration_minutes * 0.75, duration_minutes * 1.25) * 60
                auto_engage_schedule[chat_id] = (now_ts + next_delay, duration_minutes)
                
                try:
                    # Verify auto-engage is still active
                    if not pal_manager.is_auto_engage_active(chat_id):
                        continue

                    # Check if I have sent a message recently to avoid talking too much
                    recent_my_msgs = await client.get_messages(chat_id, limit=30, from_user="me")
                    if recent_my_msgs:
                        last_mine = recent_my_msgs[0].date.replace(tzinfo=timezone.utc).timestamp()
                        # If I spoke recently (relative to the configured duration), skip
                        if now_ts - last_mine < (duration_minutes * 60 * 0.75):
                            continue # I already talked recently, skip engaging.
                    
                    # Also, only engage if there is actually some recent conversation!
                    latest_msgs = await client.get_messages(chat_id, limit=1)
                    if not latest_msgs:
                        continue
                    
                    # Prevent auto-engaging if the very last message in the chat was sent by me
                    if latest_msgs[0].out or latest_msgs[0].sender_id == my_id:
                        continue
                        
                    last_msg_time = latest_msgs[0].date.replace(tzinfo=timezone.utc).timestamp()
                    # A chat is dead if no one spoke in 30 mins OR 1.5x the configured duration
                    dead_threshold = max(30 * 60, duration_minutes * 60 * 1.5)
                    if now_ts - last_msg_time > dead_threshold:
                        continue # Chat is dead, don't randomly talk to nobody.
                    
                    if not pal_manager.is_auto_engage_active(chat_id):
                        continue

                    history_text = await get_recent_chat_history(chat_id, limit=30, include_id=True)
                    now_persian = get_current_persian_datetime()
                    ltm = memory_manager.get_long_term_summary(chat_id)
                    ltm_context = f"\n[خلاصه سوابق مهم قبلی]:\n{ltm}\n" if ltm else ""
                    
                    prompt_input = Prompt.AUTO_ENGAGE_TEMPLATE.format(
                        current_time=now_persian,
                        long_term_context=ltm_context,
                        history_text=history_text,
                        duration_minutes=duration_minutes,
                        owner_name=Config.OWNER_NAME
                    )
                    
                    response = await get_response(prompt_input, persona_manager.get_prompt("normal"), is_json=True)
                    if not response or response == Text.ERROR:
                        continue
                        
                    try:
                        # Extract JSON block
                        json_match = re.search(r'\{.*\}', response, re.DOTALL)
                        if json_match:
                            data = json.loads(json_match.group(0))
                            target_id = data.get("selected_id")
                            reply_text = data.get("reply_text")
                            
                            if target_id is not None and str(target_id).lower() != "null" and reply_text:
                                try:
                                    target_id = int(target_id)
                                except (ValueError, TypeError):
                                    print(f"⚠️ Invalid target_id from AI: {target_id}")
                                    continue
                                
                                # Prevent the AI from replying to its own messages!
                                target_msg = None
                                try:
                                    target_msgs = await client.get_messages(chat_id, ids=[target_id])
                                    if target_msgs:
                                        target_msg = target_msgs[0]
                                except Exception:
                                    pass
                                    
                                if target_msg and (target_msg.sender_id == my_id or target_msg.out):
                                    print(f"⚠️ AI tried to reply to its own message ({target_id}). Ignoring!")
                                    continue
                                
                                # Prevent the AI from replying to other bots!
                                if target_msg:
                                    try:
                                        target_sender = await target_msg.get_sender()
                                        if target_sender and getattr(target_sender, 'bot', False):
                                            print(f"⚠️ AI tried to reply to a bot ({target_id}). Ignoring!")
                                            continue
                                    except Exception:
                                        pass
                                
                                # Final check before sending auto engage message
                                if not pal_manager.is_auto_engage_active(chat_id):
                                    print(f"🛑 Dropped auto-engage in chat {chat_id} (Deactivated via 777 engage off)")
                                    continue

                                human_typing_time = calculate_human_typing_delay(reply_text)
                                input_chat = await client.get_input_entity(chat_id)
                                async with global_ai_lock:
                                    async with ContinuousTyping(client, input_chat):
                                        await asyncio.sleep(human_typing_time)
                                        if not pal_manager.is_auto_engage_active(chat_id):
                                            continue
                                        await client.send_message(input_chat, reply_text, reply_to=target_id)
                                        print(f"🕵️ Auto-Engaged naturally in chat {chat_id}")
                    except json.JSONDecodeError:
                        pass # Ignore if AI failed to output valid JSON
                        
                except Exception as e:
                    print(f"⚠️ Auto-Engage error in chat {chat_id}: {e}")
                    
        except Exception as e:
            print(f"⚠️ Auto-Engage Loop Error: {e}")
            await asyncio.sleep(60) # Sleep before retrying loop on fatal error

# ==========================================================
# 🌟 MAIN STARTUP
# ==========================================================
def main():
    global my_info
    client.start()
    my_info = client.loop.run_until_complete(client.get_me())
    
    # Start background loops
    client.loop.create_task(auto_engage_loop())
    
    print("=" * 50)
    print(f"👻 GhostGram (روح‌گرام) is ONLINE & READY!")
    print(f"👤 Logged in as: {my_info.first_name} (@{my_info.username}) [ID: {my_info.id}]")
    from api_tracker import MODELS_CONFIG
    top_model = MODELS_CONFIG[0]['name'] if MODELS_CONFIG else "Unknown"
    print(f"🧠 Primary Model: {top_model} (Auto-Cascading enabled)")
    print(f"📱 Active Pal Chats (777): {pal_manager.get_active_count()}")
    print(f"🕵️ Auto-Engage Chats (777 engage): {pal_manager.get_auto_engage_count()}")
    print(f"💼 Assistant Mode (666): {'ON (All DMs)' if assistant_manager.dm_enabled else 'OFF'}")
    print("🚀 Listening for secret codes (777, 777 engage, 666, 000, 444, 555, 333, 999, 111, 888)...")
    print("=" * 50)
    
    client.run_until_disconnected()

if __name__ == '__main__':
    main()

