import asyncio
import re
import json
from datetime import datetime, timezone
from telethon import TelegramClient, events
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

client = TelegramClient(Config.SESSION_NAME, Config.API_ID, Config.API_HASH)
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

# ==========================================================
# 📜 COMMAND: راهنما / HELP (888)
# ==========================================================
@client.on(events.NewMessage(outgoing=True, pattern=r'^888$'))
async def help_handler(event):
    if not is_owner(event):
        return
    await event.edit(Text.HELP)

# ==========================================================
# 🤖 COMMAND: روشن کردن رفیق (PAL ON / 777)
# ==========================================================
@client.on(events.NewMessage(outgoing=True, pattern=r'^777(?:\s+(?!engage\b)(.+))?$'))
async def pal_on_handler(event):
    if not is_owner(event):
        return
        
    mode_arg = event.pattern_match.group(1)
    if mode_arg:
        mode = mode_arg.strip().lower()
    else:
        mode = "normal"
        
    chat_id = event.chat_id
    pal_manager.activate(chat_id, mode=mode)
    
    # Instant stealth delete
    try:
        await event.delete()
    except Exception:
        pass
    print(f"🔮 Stealth Pal ({mode.upper()} Mode) ACTIVATED for chat {chat_id}")

# ==========================================================
# 💤 COMMAND: خاموش کردن رفیق (PAL OFF / 000)
# ==========================================================
@client.on(events.NewMessage(outgoing=True, pattern=r'^000(?:\s+(all))?$'))
async def pal_off_handler(event):
    if not is_owner(event):
        return
    
    scope_arg = event.pattern_match.group(1)
    if scope_arg == "all":
        count = pal_manager.deactivate_all()
        print(f"💤 Stealth Pal DEACTIVATED globally for all {count} chats")
    else:
        chat_id = event.chat_id
        pal_manager.deactivate(chat_id)
        print(f"💤 Stealth Pal DEACTIVATED for chat {chat_id}")
        
    # Instant stealth delete
    try:
        await event.delete()
    except Exception:
        pass

# ==========================================================
# 🕵️ COMMAND: پراکنش / تعامل خودکار (AUTO ENGAGE ON / 777 engage)
# ==========================================================
@client.on(events.NewMessage(outgoing=True, pattern=r'^777\s+engage(?:\s+(\d+))?$'))
async def auto_engage_on_handler(event):
    if not is_owner(event):
        return
    
    chat_id = event.chat_id
    duration = int(event.pattern_match.group(1)) if event.pattern_match.group(1) else 20
    if duration < 1:
        duration = 1
    
    pal_manager.activate_auto_engage(chat_id, duration)
    try:
        await event.delete()
    except Exception:
        pass
    print(f"🕵️ Auto-Engage (Lurker) ACTIVATED for chat {chat_id} with duration {duration}m")

# ==========================================================
# 🛑 COMMAND: خاموش کردن تعامل (AUTO ENGAGE OFF / 777 engage off)
# ==========================================================
@client.on(events.NewMessage(outgoing=True, pattern=r'^777\s+engage\s+off(?:\s+(all))?$'))
async def auto_engage_off_handler(event):
    if not is_owner(event):
        return
        
    scope = event.pattern_match.group(1)
    if scope == "all":
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

# ==========================================================
# 💼 COMMAND: روشن کردن دستیار شخصی (ASSISTANT ON / 666)
# ==========================================================
@client.on(events.NewMessage(outgoing=True, pattern=r'^666$'))
async def assistant_on_handler(event):
    if not is_owner(event):
        return
    chat_id = event.chat_id
    assistant_manager.activate_global(chat_id=chat_id)
    try:
        await event.delete()
    except Exception:
        pass
    print(f"💼 Universal Assistant Mode ACTIVATED for all DMs (un-muted {chat_id})")


# ==========================================================
# 🛑 COMMAND: خاموش کردن یا توقف دستیار شخصی (ASSISTANT OFF / 444)
# ==========================================================
@client.on(events.NewMessage(outgoing=True, pattern=r'^444(?:\s+(all))?$'))
async def assistant_off_handler(event):
    if not is_owner(event):
        return
    chat_id = event.chat_id
    scope_arg = event.pattern_match.group(1)
    
    if scope_arg == "all":
        assistant_manager.deactivate_global()
        print(f"🛑 Universal Assistant Mode DEACTIVATED globally for all DMs")
    else:
        # Default behavior: Stop assistant ONLY in this specific chat
        assistant_manager.mute_chat(chat_id)
        print(f"🤫 Assistant MUTED only in chat {chat_id} (All other DMs remain active)")
        
    try:
        await event.delete()
    except Exception:
        pass

# ==========================================================
# 📊 COMMAND: وضعیت (STATUS / 555)
# ==========================================================
@client.on(events.NewMessage(outgoing=True, pattern=r'^555$'))
async def status_handler(event):
    if not is_owner(event):
        return
    
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




# ==========================================================
# 🧠 COMMAND: ریست حافظه کوتاه‌مدت (RESET MEMORY / 333)
# ==========================================================
@client.on(events.NewMessage(outgoing=True, pattern=r'^333$'))
async def reset_memory_handler(event):
    if not is_owner(event):
        return
    chat_id = event.chat_id
    memory_manager.reset_chat_memory(chat_id)
    # Instant stealth delete
    try:
        await event.delete()
    except Exception:
        pass
    print(f"🧠 Short-term memory RESET for chat {chat_id}")

# ==========================================================
# 🧹 COMMAND: پاکسازی پیام‌های من (GHOST PURGE / 999)
# ==========================================================
@client.on(events.NewMessage(outgoing=True, pattern=r'^999(?:\s+(\d+))?$'))
async def purge_handler(event):
    if not is_owner(event):
        return
    
    limit_arg = event.pattern_match.group(1)
    limit = int(limit_arg) if limit_arg else None
    chat_id = event.chat_id
    
    # Instant delete trigger message for stealth
    trigger_id = event.id
    try:
        await event.delete()
    except Exception:
        pass
    
    global my_info
    my_id = my_info.id if my_info else (await client.get_me()).id
    
    deleted_count = 0
    message_ids = []
    
    try:
        input_chat = await event.get_input_chat()
        # If no limit specified, limit is None (searches entire history without cap)
        search_limit = limit
        
        async for msg in client.iter_messages(input_chat, limit=search_limit):
            if msg.id == trigger_id:
                continue
            
            # Check if message is sent by me (supporting all chat and supergroup types)
            is_mine = False
            if msg.out:
                is_mine = True
            elif msg.sender_id and msg.sender_id == my_id:
                is_mine = True
            elif hasattr(msg, 'from_id') and getattr(msg.from_id, 'user_id', None) == my_id:
                is_mine = True
            
            if is_mine:
                message_ids.append(msg.id)
            
            # Delete in batches of 50
            if len(message_ids) >= 50:
                try:
                    await client.delete_messages(input_chat, message_ids, revoke=True)
                    deleted_count += len(message_ids)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds + 1)
                    await client.delete_messages(input_chat, message_ids, revoke=True)
                    deleted_count += len(message_ids)
                except Exception as ex:
                    # If batch failed (e.g. contains message older than 48h in non-admin group), try individually
                    for mid in message_ids:
                        try:
                            await client.delete_messages(input_chat, [mid], revoke=True)
                            deleted_count += 1
                        except Exception:
                            pass
                message_ids = []
                await asyncio.sleep(0.2)
        
        # Delete remaining messages
        if message_ids:
            try:
                await client.delete_messages(input_chat, message_ids, revoke=True)
                deleted_count += len(message_ids)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds + 1)
                await client.delete_messages(input_chat, message_ids, revoke=True)
                deleted_count += len(message_ids)
            except Exception as ex:
                for mid in message_ids:
                    try:
                        await client.delete_messages(input_chat, [mid], revoke=True)
                        deleted_count += 1
                    except Exception:
                        pass
            
        print(f"🧹 Stealth Purged {deleted_count} messages from chat {chat_id}")
    except Exception as e:
        print(f"⚠️ Purge error in chat {chat_id}: {e}")

# ==========================================================
# 💬 COMMAND: پاسخ هوشمند سفارشی (SMART SPEAK / 111)
# ==========================================================
@client.on(events.NewMessage(outgoing=True, pattern=r'^111(?:\s+(.*))?$'))
async def custom_ask_handler(event):
    if not is_owner(event):
        return
    
    user_instruction = (event.pattern_match.group(1) or "").strip()
    reply_to_id = event.reply_to_msg_id
    chat_id = event.chat_id
    
    # Delete the command message instantly to keep it stealth
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
    async with ContinuousTyping(client, input_chat):
        response = await get_response(prompt_input, persona_manager.get_prompt("normal"))
        if response and response != Text.ERROR:
            human_typing_time = calculate_human_typing_delay(response)
            await asyncio.sleep(human_typing_time)
            await client.send_message(input_chat, response, reply_to=reply_to_id)
            print(f"⚡ Handled 111 / !بگو in chat {chat_id}")
            # Record message for rolling long-term memory summary check
            memory_manager.record_message_and_check_summary(client, chat_id, gemini, format_sender_name, my_info.id if my_info else Config.OWNER_ID)

# ==========================================================
# 🚀 INCOMING: پردازش پیام‌های دریافتی (PAL & ASSISTANT MODES)
# ==========================================================

# Concurrency management to prevent API spam and overlapping replies
chat_locks = {}
chat_latest_msg = {}

def get_chat_lock(chat_id):
    if chat_id not in chat_locks:
        chat_locks[chat_id] = asyncio.Lock()
    return chat_locks[chat_id]

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
    
    lock = get_chat_lock(chat_id)
    async with lock:
        # If a newer message arrived from this chat while we were waiting/processing,
        # skip this event. The newer event's handler will process the combined history!
        if chat_latest_msg.get(chat_id, 0) > event.id:
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
            
            if response and response != Text.ERROR:
                human_typing_time = calculate_human_typing_delay(response)
                await asyncio.sleep(human_typing_time)
                
                reply_target = event.id if (event.is_group or event.is_channel) else None
                await client.send_message(input_chat, response, reply_to=reply_target)
                if mode == "pal":
                    print(f"✅ Pal replied naturally in chat {chat_id}")
                else:
                    print(f"✅ Assistant replied politely in chat {chat_id}")
                    
                # Record message for rolling long-term memory summary check
                memory_manager.record_message_and_check_summary(client, chat_id, gemini, format_sender_name, my_id)


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
                    last_msg_time = latest_msgs[0].date.replace(tzinfo=timezone.utc).timestamp()
                    # A chat is dead if no one spoke in 30 mins OR 1.5x the configured duration
                    dead_threshold = max(30 * 60, duration_minutes * 60 * 1.5)
                    if now_ts - last_msg_time > dead_threshold:
                        continue # Chat is dead, don't randomly talk to nobody.
                    
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
                                
                                human_typing_time = calculate_human_typing_delay(reply_text)
                                input_chat = await client.get_input_entity(chat_id)
                                async with ContinuousTyping(client, input_chat):
                                    await asyncio.sleep(human_typing_time)
                                    await client.send_message(input_chat, reply_text, reply_to=target_id)
                                    print(f"🕵️ Auto-Engaged naturally in chat {chat_id}")
                                    memory_manager.record_message_and_check_summary(client, chat_id, gemini, format_sender_name, my_id)
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
    print(f"🧠 Model: {Config.MODEL_NAME}")
    print(f"📱 Active Pal Chats (777): {pal_manager.get_active_count()}")
    print(f"🕵️ Auto-Engage Chats (777 engage): {pal_manager.get_auto_engage_count()}")
    print(f"💼 Assistant Mode (666): {'ON (All DMs)' if assistant_manager.dm_enabled else 'OFF'}")
    print("🚀 Listening for secret codes (777, 777 engage, 666, 000, 444, 555, 333, 999, 111, 888)...")
    print("=" * 50)
    
    client.run_until_disconnected()

if __name__ == '__main__':
    main()

