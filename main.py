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
from human_behavior import ContinuousTyping, calculate_human_typing_delay
from time_utils import get_current_persian_datetime
from text_processing import normalize_digits, clean_outbound_text
from logger import logger
import random
import time

session_target = StringSession(Config.SESSION_STRING) if Config.SESSION_STRING else Config.SESSION_NAME
client = TelegramClient(session_target, Config.API_ID, Config.API_HASH)
my_info = None

def is_owner(event) -> bool:
    """Strict check to ensure commands only run for the owner (outgoing messages from this account)."""
    return bool(event and event.out)

async def get_response(user_message: str, system_prompt: str = None, is_json: bool = False, start_model: str = None) -> str:
    if system_prompt is None:
        system_prompt = persona_manager.get_prompt("normal")
    return await gemini.get_response(user_message, system_prompt, is_json=is_json, start_model=start_model)

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
        text = current_msg.text
        if not text:
            text = memory_manager.get_virtual_text(current_msg.chat_id, current_msg.id)
        if not text:
            text = Text.NO_TEXT
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
# 🎮 OUTGOING COMMAND HANDLERS
# ==========================================================

async def handle_help(event):
    await event.edit(Text.get_help())

async def handle_pal_on(event, mode="normal"):
    chat_id = event.chat_id
    pal_manager.activate(chat_id, mode=mode)
    try:
        await event.delete()
    except Exception:
        pass
    logger.info(f"🔮 Stealth Pal ({mode.upper()} Mode) ACTIVATED for chat {chat_id}")

async def handle_pal_off(event, is_all=False):
    if is_all:
        count = pal_manager.deactivate_all()
        logger.info(f"💤 Stealth Pal DEACTIVATED globally for all {count} chats")
    else:
        chat_id = event.chat_id
        pal_manager.deactivate(chat_id)
        logger.info(f"💤 Stealth Pal DEACTIVATED for chat {chat_id}")
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
        logger.error(f"⚠️ Error calculating dynamic duration for {chat_id}: {e}", exc_info=True)
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
    logger.info(f"🕵️ Auto-Engage (Lurker) ACTIVATED for chat {chat_id} with duration {duration}m")

async def handle_auto_engage_off(event, is_all=False):
    if is_all:
        count = pal_manager.deactivate_all_engages()
        logger.info(f"🛑 Auto-Engage DEACTIVATED globally for all {count} chats")
    else:
        chat_id = event.chat_id
        pal_manager.deactivate_auto_engage(chat_id)
        logger.info(f"🛑 Auto-Engage (Lurker) DEACTIVATED for chat {chat_id}")
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
    logger.info(f"💼 Universal Assistant Mode ACTIVATED for all DMs (un-muted {chat_id})")

async def handle_assistant_off(event, is_all=False):
    chat_id = event.chat_id
    if is_all:
        assistant_manager.deactivate_global()
        logger.info(f"🛑 Universal Assistant Mode DEACTIVATED globally for all DMs")
    else:
        assistant_manager.mute_chat(chat_id)
        logger.info(f"🤫 Assistant MUTED only in chat {chat_id} (All other DMs remain active)")
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
    logger.info(f"🧠 Short-term memory RESET for chat {chat_id}")

async def handle_view_memory(event, is_all=False):
    try:
        await event.delete()
    except Exception:
        pass

    if is_all:
        memories = memory_manager.long_term_memories
        if not memories:
            msg = await event.respond("📭 **هیچ حافظه بلندمدتی در سیستم ثبت نشده است.**")
            await asyncio.sleep(5)
            try:
                await msg.delete()
            except Exception:
                pass
            return
            
        report_chunks = []
        current_chunk = "🧠 **گزارش کل حافظه بلندمدت (تمام چت‌ها):**\n"
        
        # Build chunks respecting Telegram's 4096 char limit
        for chat_id, summary in memories.items():
            if not summary.strip():
                continue
            
            try:
                entity = await client.get_entity(chat_id)
                name = getattr(entity, 'title', None) or getattr(entity, 'first_name', None) or str(chat_id)
            except Exception:
                name = str(chat_id)
                
            entry = f"\n🔹 **چت:** {name} (`{chat_id}`)\n📝 **خلاصه:** {summary}\n" + ("─"*20)
            
            if len(current_chunk) + len(entry) > 3800:
                report_chunks.append(current_chunk)
                current_chunk = entry
            else:
                current_chunk += entry
                
        if current_chunk.strip():
            report_chunks.append(current_chunk)
            
        for chunk in report_chunks:
            if chunk.strip():
                await event.respond(chunk)
                await asyncio.sleep(0.5)
    else:
        chat_id = event.chat_id
        summary = memory_manager.get_long_term_summary(chat_id)
        if summary:
            await event.respond(f"🧠 **حافظه بلندمدت این چت:**\n\n{summary}")
        else:
            msg = await event.respond("📭 **هیچ حافظه بلندمدتی برای این چت ثبت نشده است.**")
            await asyncio.sleep(5)
            try:
                await msg.delete()
            except Exception:
                pass

async def handle_factory_reset(event):
    from api_tracker import api_tracker
    from voice_manager import voice_manager
    api_tracker.factory_reset()
    memory_manager.factory_reset()
    pal_manager.factory_reset()
    assistant_manager.factory_reset()
    voice_manager.factory_reset()
    
    # Rock-solid log deletion: Release file locks, delete, and reattach
    import os
    import glob
    import logging
    from logging.handlers import RotatingFileHandler
    from config import Config
    from logger import logger
    
    # 1. Close and remove existing file handlers to release Windows file locks
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
            logger.removeHandler(handler)
            
    # 2. Safely delete all log files and backups
    log_pattern = os.path.join(Config.PROFILE_DIR, "*.log*")
    for log_file in glob.glob(log_pattern):
        try:
            os.remove(log_file)
        except Exception:
            pass
            
    # 3. Spin up a fresh file handler so the bot can keep logging!
    try:
        new_log_file = os.path.join(Config.PROFILE_DIR, "ghostgram.log")
        fh = RotatingFileHandler(new_log_file, maxBytes=Config.LOG_MAX_BYTES, backupCount=Config.LOG_BACKUP_COUNT, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception as e:
        print(f"Failed to restart file logger after nuke: {e}")
    try:
        await event.delete()
    except Exception:
        pass
        
    msg = await event.respond("♻️ **سیستم با موفقیت ریست کارخانه شد!**\n\n✅ وضعیت تمام کلیدهای API صفر شد.\n✅ تمام چت‌های فعال غیرفعال شدند.\n✅ حافظه‌های بلندمدت و کوتاه‌مدت تمام گروه‌ها پاک شد.\n✅ تمامی لاگ‌های سیستم با موفقیت حذف شدند.")
    await asyncio.sleep(5)
    try:
        await msg.delete()
    except Exception:
        pass

async def handle_purge(event, limit=None, search_only_mine=False):
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
        # We don't restrict iter_messages limit, we stop when we delete enough of OUR messages
        search_limit = None
        
        msg_scan_count = 0
        delete_streak_count = 0
        
        iter_kwargs = {"limit": search_limit}
        if search_only_mine:
            iter_kwargs["from_user"] = "me"
            
        async for msg in client.iter_messages(input_chat, **iter_kwargs):
            msg_scan_count += 1
            
            if msg_scan_count > Config.GHOST_PURGE_SCAN_LIMIT:
                logger.info(f"😴 Human Purge: Reached scrolling fatigue limit ({Config.GHOST_PURGE_SCAN_LIMIT}). Stopping scan.")
                break
            
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
                        logger.info(f"🧘‍♂️ Human Purge: Taking a short break after {delete_streak_count} deletes...")
                        await asyncio.sleep(random.uniform(4.5, 9.5))
                        delete_streak_count = 0
                    
                except FloodWaitError as e:
                    logger.info(f"⏳ FloodWait in Purge. Sleeping for {e.seconds}s...")
                    await asyncio.sleep(e.seconds + random.uniform(3.0, 7.0))
                    try:
                        await client.delete_messages(input_chat, [msg.id], revoke=True)
                        deleted_count += 1
                    except Exception:
                        pass
                except Exception:
                    pass
                
                if limit is not None and deleted_count >= limit:
                    break
            
        logger.info(f"🧹 Stealth Purged {deleted_count} messages (Ultra-Human Mode) from chat {chat_id}")
    except Exception as e:
        logger.error(f"⚠️ Purge error in chat {chat_id}: {e}", exc_info=True)

async def handle_custom_ask(event, user_instruction=""):
    reply_to_id = event.reply_to_msg_id
    chat_id = event.chat_id
    
    try:
        await event.delete()
    except Exception:
        pass

    history_text = await get_recent_chat_history(chat_id)
    target_text = ""
    sender_name = "مخاطب"
    
    if reply_to_id:
        reply_msg = await event.get_reply_message()
        if reply_msg:
            target_text = reply_msg.text
            if not target_text:
                target_text = memory_manager.get_virtual_text(chat_id, reply_msg.id)
                
            # --- ON DEMAND TRANSCRIPTION ---
            if not target_text and getattr(reply_msg, "media", None):
                if getattr(reply_msg, 'voice', None) or getattr(reply_msg, 'video_note', None) or getattr(reply_msg, 'audio', None) or (getattr(reply_msg, 'document', None) and getattr(reply_msg.document, 'mime_type', '').startswith('audio/')):
                    msg_wait = await client.send_message('me', "⏳ **در حال استخراج متن از فایل رسانه برای تحلیل... (Stealth)**")
                    import os
                    from speech_to_text import transcribe_audio_file
                    os.makedirs("scratch", exist_ok=True)
                    audio_path = await reply_msg.download_media(file="scratch/")
                    if audio_path:
                        transcribed = await transcribe_audio_file(audio_path, Config.GEMINI_API_KEYS)
                        try:
                            os.remove(audio_path)
                        except:
                            pass
                        if transcribed:
                            if transcribed.startswith("Error"):
                                logger.warning(f"Voice note transcription failed: {transcribed}")
                            else:
                                target_text = f"[Voice Note] {transcribed}"
                                memory_manager.add_virtual_message(chat_id, reply_msg.id, target_text)
                    try:
                        await msg_wait.delete()
                    except:
                        pass
            
            if not target_text:
                target_text = Text.NO_TEXT
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
        owner_first_name=Config.OWNER_FIRST_NAME
    )
    
    input_chat = await event.get_input_chat()
    async with global_ai_lock:
        async with ContinuousTyping(client, input_chat):
            pal_variant = pal_manager.get_mode(chat_id) if pal_manager.is_active(chat_id) else "normal"
            response = await get_response(prompt_input, persona_manager.get_prompt(pal_variant))
            if response and response != Text.ERROR:
                # 111 is an explicit admin command. Skip human typing delay for snappy responses!
                await client.send_message(input_chat, response, reply_to=reply_to_id)
                logger.info(f"⚡ Handled 111 in chat {chat_id}")

async def handle_text_to_speech(event, user_inst):
    try:
        await event.delete()
    except Exception:
        pass

    from voice_manager import voice_manager
    voice_name = voice_manager.get_current_voice()
    
    reply_to_id = event.reply_to_msg_id
    chat_id = event.chat_id
    
    if not user_inst and not reply_to_id:
        return
        
    history_text = await get_recent_chat_history(chat_id)
    target_text = ""
    sender_name = "مخاطب"
    
    if reply_to_id:
        reply_msg = await event.get_reply_message()
        if reply_msg:
            target_text = reply_msg.text
            if not target_text:
                target_text = memory_manager.get_virtual_text(chat_id, reply_msg.id)
                
            # --- ON DEMAND TRANSCRIPTION ---
            if not target_text and getattr(reply_msg, "media", None):
                if getattr(reply_msg, 'voice', None) or getattr(reply_msg, 'video_note', None) or getattr(reply_msg, 'audio', None) or (getattr(reply_msg, 'document', None) and getattr(reply_msg.document, 'mime_type', '').startswith('audio/')):
                    msg_wait = await client.send_message('me', "⏳ **در حال استخراج متن از فایل رسانه برای تحلیل... (Stealth)**")
                    import os
                    from speech_to_text import transcribe_audio_file
                    os.makedirs("scratch", exist_ok=True)
                    audio_path = await reply_msg.download_media(file="scratch/")
                    if audio_path:
                        transcribed = await transcribe_audio_file(audio_path, Config.GEMINI_API_KEYS)
                        try:
                            os.remove(audio_path)
                        except:
                            pass
                        if transcribed and not transcribed.startswith("Error"):
                            target_text = f"[Voice Note] {transcribed}"
                            memory_manager.add_virtual_message(chat_id, reply_msg.id, target_text)
                    try:
                        await msg_wait.delete()
                    except:
                        pass
            
            if not target_text:
                target_text = Text.NO_TEXT
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
        user_instruction=user_inst or "پاسخ طبیعی، خودمونی و مناسب بده.",
        owner_first_name=Config.OWNER_FIRST_NAME
    )
    
    input_chat = await event.get_input_chat()
    async with global_ai_lock:
        pal_variant = pal_manager.get_mode(chat_id) if pal_manager.is_active(chat_id) else "normal"
        text = await get_response(prompt_input, persona_manager.get_prompt(pal_variant))
        if text == Text.ERROR:
            text = ""
                
    if not text:
        logger.warning("TTS failed: No text generated.")
        if event.chat_id == my_info.id:
            msg = await event.respond("❌ **متنی برای تبدیل به صدا یافت نشد یا تولید نشد.**\n\n💡 *راهنما:* `809 <متن>` *یا روی یک پیام ریپلای کنید.*")
            await asyncio.sleep(6)
            try:
                await msg.delete()
            except Exception:
                pass
        return

    try:
        from text_to_speech import generate_voice_message
        keys = Config.GEMINI_API_KEYS
        ogg_path = await generate_voice_message(text, keys, voice_name=voice_name)
        
        if ogg_path.startswith("Error"):
            logger.error(f"TTS Error: {ogg_path}")
            if event.chat_id == my_info.id:
                await event.respond(f"❌ **خطا در ساخت صدا:**\n`{ogg_path}`", reply_to=reply_to_id)
        else:
            global last_ai_voice_time
            import time
            last_ai_voice_time = time.time()
            
            try:
                sent_msg = await client.send_file(
                    event.chat_id, 
                    ogg_path, 
                    voice_note=True, 
                    reply_to=reply_to_id
                )
                # Inject the AI's generated response into stealth virtual memory mapped to the real message ID!
                memory_manager.add_virtual_message(chat_id, sent_msg.id, f"[Voice Note] {text}")
            except Exception as media_err:
                if "You cannot send voices" in str(media_err) or "SendMediaRequest" in str(media_err):
                    logger.warning(f"Voice restricted in chat {event.chat_id}, falling back to text.")
                    sent_msg = await event.respond(f"🎤 *(Voice restricted in this chat, sending text instead)*\n\n{text}", reply_to=reply_to_id)
                    memory_manager.add_virtual_message(chat_id, sent_msg.id, text)
                else:
                    raise media_err
            
    except Exception as e:
        logger.error(f"❌ **خطای غیرمنتظره در TTS:**\n`{str(e)}`")
        if event.chat_id == my_info.id:
            await event.respond(f"❌ **خطای غیرمنتظره در TTS:**\n`{str(e)}`")
    finally:
        import os
        if 'ogg_path' in locals() and ogg_path and not ogg_path.startswith("Error") and os.path.exists(ogg_path):
            try:
                os.remove(ogg_path)
            except Exception:
                pass

async def handle_voice_settings(event, val_str):
    try:
        await event.delete()
    except Exception:
        pass
        
    from voice_manager import voice_manager, VOICES
    
    if val_str:
        try:
            idx = int(val_str)
            if voice_manager.set_voice(idx):
                msg = await event.respond(f"✅ **صدای پیش‌فرض با موفقیت تغییر کرد به:** `{voice_manager.get_current_voice()}`")
            else:
                msg = await event.respond(f"❌ **شماره صدا نامعتبر است (بین ۱ تا {len(VOICES)}).**")
        except ValueError:
            logger.warning("Invalid voice number provided.")
            if event.chat_id == my_info.id:
                msg = await event.respond("❌ **لطفاً فقط یک عدد صحیح وارد کنید.**")
                await asyncio.sleep(4)
                try:
                    await msg.delete()
                except Exception:
                    pass
            return
            
        await asyncio.sleep(4)
        try:
            await msg.delete()
        except Exception:
            pass
        return
        
    # List voices
    text = "🎙️ **تنظیمات صدای ربات (TTS)**\n\n"
    text += f"صدای فعلی: `{voice_manager.get_current_voice()}`\n\n"
    for i, v in enumerate(VOICES, 1):
        text += f"`{i}. {v}`\n"
    text += "\n💡 *برای انتخاب صدا، کافیست شماره آن را بفرستید:*\n`810 5`"
    
    msg = await event.respond(text)
    await asyncio.sleep(15)
    try:
        await msg.delete()
    except Exception:
        pass

async def handle_transcribe(event):
    try:
        await event.delete()
    except Exception:
        pass

    reply_msg = await event.get_reply_message()
    if not reply_msg or not getattr(reply_msg, "media", None):
        logger.warning("STT failed: Not a media message.")
        if event.chat_id == my_info.id:
            msg = await event.respond("❌ **لطفاً این دستور را روی یک پیام صوتی، آهنگ یا ویدیو ریپلای کنید.**")
            await asyncio.sleep(4)
            try:
                await msg.delete()
            except Exception:
                pass
        return

    try:
        file_path = await reply_msg.download_media("temp_transcribe")
        if not file_path:
            logger.error("STT failed: Could not download media file.")
            if event.chat_id == my_info.id:
                await event.respond("❌ **خطا در دانلود فایل!**", reply_to=reply_msg.id)
            return
            
        from speech_to_text import transcribe_audio_file
        
        keys = Config.GEMINI_API_KEYS
        transcript = await transcribe_audio_file(file_path, keys)
        
        if transcript.startswith("Error"):
            logger.error(f"STT Processing Error: {transcript}")
            if event.chat_id == my_info.id:
                await event.respond(f"❌ **خطا در پردازش:**\n`{transcript}`", reply_to=reply_msg.id)
        else:
            if not transcript.strip():
                transcript = "⚠️ هیچ صدایی تشخیص داده نشد یا فایل کاملاً بی‌صدا بود."
                
            if len(transcript) < 4000:
                await event.respond(transcript, reply_to=reply_msg.id)
            else:
                # Split and send chunks
                chunk_size = 4000
                for i in range(0, len(transcript), chunk_size):
                    await event.respond(transcript[i:i+chunk_size], reply_to=reply_msg.id)
            
    except Exception as e:
        logger.error(f"Unexpected error in STT command: {e}", exc_info=True)
        if event.chat_id == my_info.id:
            await event.respond(f"❌ **خطای غیرمنتظره:**\n`{str(e)}`", reply_to=reply_msg.id)
    finally:
        import os
        if 'file_path' in locals() and file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

async def handle_voice_changer(event):
    from voice_manager import voice_manager
    import os
    from speech_to_text import transcribe_audio_file
    from text_to_speech import generate_voice_message
    
    try:
        await event.delete()
    except Exception:
        pass
        
    reply_to_id = event.reply_to_msg_id
    
    try:
        os.makedirs("scratch", exist_ok=True)
        audio_path = await event.download_media(file="scratch/")
        if audio_path:
            keys = Config.GEMINI_API_KEYS
            transcript = await transcribe_audio_file(audio_path, keys)
            try:
                os.remove(audio_path)
            except Exception:
                pass
                
            if transcript and not transcript.startswith("Error") and transcript.strip():
                voice_name = voice_manager.get_current_voice()
                ogg_path = await generate_voice_message(transcript, keys, voice_name=voice_name)
                
                if not ogg_path.startswith("Error"):
                    global last_ai_voice_time
                    import time
                    last_ai_voice_time = time.time()
                    
                    try:
                        await client.send_file(
                            event.chat_id,
                            ogg_path,
                            voice_note=True,
                            reply_to=reply_to_id
                        )
                    except Exception as media_err:
                        if "You cannot send voices" in str(media_err) or "SendMediaRequest" in str(media_err):
                            logger.warning(f"Voice restricted in chat {event.chat_id}, falling back to text.")
                            await event.respond(f"🎤 *(Voice restricted in this chat, sending text instead)*\n\n{transcript}", reply_to=reply_to_id)
                        else:
                            raise media_err
                    
                    try:
                        os.remove(ogg_path)
                    except Exception:
                        pass
    except Exception as e:
        logger.error(f"⚠️ Voice Changer Error: {e}", exc_info=True)

# ==========================================================
# 🎯 UNIFIED OUTGOING COMMAND DISPATCHER
# ==========================================================
last_ai_voice_time = 0

@client.on(events.NewMessage(outgoing=True))
async def outgoing_command_dispatcher(event):
    if not is_owner(event):
        return
        
    # --- VOICE CHANGER INTERCEPTION ---
    from voice_manager import voice_manager
    import time
    global last_ai_voice_time
    
    if getattr(event, 'voice', None) and voice_manager.voice_changer_active:
        # Simple rate limiter for voice commands (from Config)
        if time.time() - last_ai_voice_time < Config.AI_VOICE_COOLDOWN_SECONDS:
            return 
        await handle_voice_changer(event)
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

    # 3.5. VIEW MEMORY (303 [all])
    m_view_mem = re.match(r'^303(?:\s+(all))?$', norm_lower)
    if m_view_mem:
        scope = m_view_mem.group(1)
        await handle_view_memory(event, is_all=(scope == "all"))
        return

    # 4. RESET MEMORY (333)
    if norm_lower == "333":
        await handle_reset_memory(event)
        return

    # 4. GHOST PURGE (999 [limit])
    m_purge = re.match(r'^999(?:\s+(\d+))?$', norm_lower)
    if m_purge:
        limit = int(m_purge.group(1)) if m_purge.group(1) else None
        await handle_purge(event, limit)
        return

    # 4.5. SMART GHOST PURGE (998 [limit]) - Only searches your messages
    m_smart_purge = re.match(r'^998(?:\s+(\d+))?$', norm_lower)
    if m_smart_purge:
        limit = int(m_smart_purge.group(1)) if m_smart_purge.group(1) else None
        await handle_purge(event, limit, search_only_mine=True)
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
        
    # 7.5 VOICE CHANGER TOGGLE (811)
    if norm_lower == "811":
        from voice_manager import voice_manager
        is_active = voice_manager.toggle_voice_changer()
        status = "✅ فعال" if is_active else "❌ غیرفعال"
        msg = await event.respond(f"🎙️ **حالت Voice Changer:** {status}")
        await asyncio.sleep(4)
        try:
            await msg.delete()
            await event.delete()
        except Exception:
            pass
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

    # 13. TRANSCRIBE (808)
    if norm_lower == "808":
        await handle_transcribe(event)
        return

    # 14. SMART VOICE REPLY (809)
    m_tts = re.match(r'^809(?:\s+(.*))?$', norm, re.DOTALL)
    if m_tts:
        user_inst = (m_tts.group(1) or "").strip()
        await handle_text_to_speech(event, user_inst)
        return

    # 15. VOICE SETTINGS (810)
    m_vsettings = re.match(r'^810(?:\s+(\d+))?$', norm_lower)
    if m_vsettings:
        val = m_vsettings.group(1)
        await handle_voice_settings(event, val)
        return

# ==========================================================
# 🚀 INCOMING: پردازش پیام‌های دریافتی (PAL & ASSISTANT MODES)
# ==========================================================

@client.on(events.NewMessage())
async def global_memory_tracker(event):
    """Tracks every incoming and outgoing message in active chats for accurate long-term summarization."""
    if not event.text and not getattr(event.message, 'voice', None) and not getattr(event.message, 'audio', None):
        return
        
    pass
        
    chat_id = event.chat_id
    
    # Only track if the chat is actively monitored (Pal, Engage, or Assistant)
    is_tracked = (
        pal_manager.is_active(chat_id) or 
        pal_manager.is_auto_engage_active(chat_id) or 
        assistant_manager.is_active_for_chat(chat_id, is_private=event.is_private)
    )
    if not is_tracked:
        logger.debug(f"[MEMORY] Chat {chat_id} is not actively tracked. Ignoring.")
        return
        
    global my_info
    my_id = my_info.id if my_info else Config.OWNER_ID
    
    import time
    if event.out or getattr(event, 'sender_id', None) == my_id:
        memory_manager.update_owner_activity(chat_id)
    else:
        if event.is_group or event.is_channel:
            last_active = memory_manager.get_owner_last_active_time(chat_id)
            # Check if 30 minutes (from Config) passed since user's last message
            if time.time() - last_active > Config.AUTO_ENGAGE_INTERVAL_MINUTES * 60:
                logger.debug(f"[MEMORY] Ignored message in {chat_id} (Owner inactive for 30m).")
                return # Ignore message (owner is not actively participating)
                
    pass
    memory_manager.record_message_and_check_summary(client, chat_id, gemini, format_sender_name, my_id)

# Concurrency management to prevent API spam and overlapping replies
# Changed to a GLOBAL lock per user request to process ALL messages strictly sequentially one by one across the entire bot
global_ai_lock = asyncio.Lock()

replied_message_ids = {}

def mark_as_replied(chat_id, msg_id):
    if msg_id:
        key = (chat_id, msg_id)
        # Re-insert to push it to the end (newest) if it already existed
        if key in replied_message_ids:
            del replied_message_ids[key]
        replied_message_ids[key] = True
        
        # Enforce max size (FIFO)
        if len(replied_message_ids) > 2000:
            oldest_key = next(iter(replied_message_ids))
            del replied_message_ids[oldest_key]

def is_already_replied(chat_id, msg_id):
    return (chat_id, msg_id) in replied_message_ids

@client.on(events.UserUpdate)
async def user_update_handler(event):
    if getattr(event, 'typing', False):
        import human_behavior
        human_behavior.update_typing_status(event.chat_id, getattr(event, 'user_id', None))

def get_chat_lock(chat_id):
    return global_ai_lock

@client.on(events.NewMessage(incoming=True))
async def incoming_message_handler(event):
    chat_id = event.chat_id
    logger.debug(f"[LIFECYCLE] New incoming message detected in {chat_id}.")
    
    global my_info
    my_id = my_info.id if my_info else Config.OWNER_ID
    
    # Ignore messages from myself
    if event.out or event.sender_id == my_id:
        logger.debug(f"[LIFECYCLE] Dropped message in {chat_id} (Sender is self).")
        return

    # Ignore messages from other bots to prevent endless AI-to-AI loops
    try:
        sender = await event.get_sender()
        if sender and getattr(sender, 'bot', False):
            logger.debug(f"[LIFECYCLE] Dropped message in {chat_id} (Sender is a bot).")
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
        logger.debug(f"[LIFECYCLE] Dropped message in {chat_id} (No active mode).")
        return
        
    logger.debug(f"[LIFECYCLE] Message accepted for processing in {chat_id} under mode: {mode}.")
    
    # For group chats: only respond if replied to me, or mentioned (text only for mentions)
    incoming_text_raw = event.text or ""
    is_reply_to_me = False
    is_mentioned = False
    
    if event.is_group or event.is_channel:
        if event.is_reply:
            try:
                reply_msg = await event.get_reply_message()
                if reply_msg:
                    if reply_msg.out or reply_msg.sender_id == my_id or getattr(reply_msg.from_id, 'user_id', None) == my_id:
                        is_reply_to_me = True
            except Exception:
                pass
        
        raw_lower = incoming_text_raw.lower()
        if my_info and my_info.username and f"@{my_info.username.lower()}" in raw_lower:
            is_mentioned = True
        if my_info and my_info.first_name and my_info.first_name.lower() in raw_lower:
            is_mentioned = True
        if Config.OWNER_FIRST_NAME and Config.OWNER_FIRST_NAME.lower() in raw_lower:
            is_mentioned = True
                
        # If it's a group, only reply if directly addressed or explicitly mentioned/replied
        if not (is_reply_to_me or is_mentioned):
            logger.debug(f"[LIFECYCLE] Dropped group message in {chat_id} (Not addressed/mentioned).")
            return

    # 🎙️ Audio processing ONLY for DMs or explicitly addressed group messages
    incoming_text = incoming_text_raw
    
    if not incoming_text.strip():
        # In Telethon, event itself has .voice, .audio, .video_note, and .document shortcuts
        if getattr(event, 'voice', None) or getattr(event, 'video_note', None) or getattr(event, 'audio', None) or (getattr(event, 'document', None) and getattr(event.document, 'mime_type', '').startswith('audio/')):
            logger.info(f"🎙️ Intercepted addressed media in chat {chat_id}! Downloading...")
            import os
            from speech_to_text import transcribe_audio_file
            
            # Download and transcribe
            os.makedirs("scratch", exist_ok=True)
            audio_path = await event.download_media(file="scratch/")
            
            if audio_path:
                logger.info(f"🎙️ Downloaded to {audio_path}. Transcribing...")
                transcribed = await transcribe_audio_file(audio_path, Config.GEMINI_API_KEYS)
                try:
                    os.remove(audio_path)
                except:
                    pass
                    
                if transcribed and not transcribed.startswith("Error"):
                    logger.info(f"🎙️ Transcription success: {transcribed}")
                    incoming_text = f"[Voice Note] {transcribed}"
                    # Inject into stealth virtual memory!
                    memory_manager.add_virtual_message(chat_id, event.message.id, incoming_text)
                else:
                    logger.warning(f"⚠️ Transcription failed: {transcribed}")
                    return
        else:
            # Might be sticker/photo without caption
            return

    # Track the latest message ID for this specific user in this chat to debounce rapid spam
    import human_behavior
    sender_id = event.sender_id
    human_behavior.update_latest_message(chat_id, sender_id, event.id)

    # Smart Waiting & Batching Logic
    should_abort = await human_behavior.simulate_reading_and_batching(event, incoming_text)
    if should_abort:
        return
    
    # Check if mode was turned off while we were sleeping
    if mode == "pal" and not pal_manager.is_active(chat_id):
        return
    if mode == "assistant" and not assistant_manager.is_active_for_chat(chat_id, is_private=event.is_private):
        return

    lock = get_chat_lock(chat_id)
    async with lock:
        # If a newer message arrived from this user in this chat while we were waiting/processing,
        # skip this event. The newer event's handler will process the combined history!
        if human_behavior.is_superseded(chat_id, sender_id, event.id):
            return

        # Double check after obtaining lock
        if mode == "pal" and not pal_manager.is_active(chat_id):
            return
        if mode == "assistant" and not assistant_manager.is_active_for_chat(chat_id, is_private=event.is_private):
            return
            
        if is_already_replied(chat_id, event.id):
            return

        input_chat = await event.get_input_chat()
        
        # Mark messages as read naturally
        try:
            await client.send_read_acknowledge(input_chat, max_id=event.id)
        except Exception:
            pass

        # Start continuous typing immediately at the top of the chat (DMs and groups)
        try:
            async with ContinuousTyping(client, input_chat):
                # Gather history, long-term memory, and sender info
                try:
                    sender = await event.get_sender()
                except Exception:
                    sender = None
                sender_name = await format_sender_name(sender, my_id)
                history_text = await get_recent_chat_history(chat_id)
                now_persian = get_current_persian_datetime()
                ltm = memory_manager.get_long_term_summary(chat_id)
                ltm_context = f"\n[خلاصه سوابق مهم قبلی]:\n{ltm}\n" if ltm else ""
                
                logger.debug(f"[LIFECYCLE] Assembling Gemini prompt for chat {chat_id} (Mode: {mode}). History length: {len(history_text)}")
                
                if mode == "pal":
                    pal_variant = pal_manager.get_mode(chat_id)
                    prompt_input = Prompt.AUTOPILOT_TEMPLATE.format(
                        current_time=now_persian,
                        long_term_context=ltm_context,
                        history_text=history_text,
                        sender=sender_name,
                        target_text=incoming_text,
                        owner_first_name=Config.OWNER_FIRST_NAME
                    )
                    system_prompt = persona_manager.get_prompt(pal_variant)
                    logger.info(f"🤖 Pal Autopilot ({pal_variant.upper()}) thinking & typing for chat {chat_id} (from {sender_name})...")
                else:
                    prompt_input = Prompt.ASSISTANT_TEMPLATE.format(
                        current_time=now_persian,
                        long_term_context=ltm_context,
                        history_text=history_text,
                        sender=sender_name,
                        target_text=incoming_text,
                        owner_first_name=Config.OWNER_FIRST_NAME
                    )
                    system_prompt = persona_manager.get_prompt("assistant")
                    logger.info(f"💼 Personal Assistant thinking & typing for chat {chat_id} (from {sender_name})...")
                
                
                start_time = time.time()
                logger.debug(f"[LIFECYCLE] Prompting Gemini API... (Models: {Config.GEMINI_MODELS})")
                response = await get_response(prompt_input, system_prompt)
                elapsed = time.time() - start_time
                logger.debug(f"[LIFECYCLE] Gemini replied in {elapsed:.2f}s. Response length: {len(response)}")
                
                # Re-verify mode wasn't disabled during AI generation
                if mode == "pal" and not pal_manager.is_active(chat_id):
                    logger.info(f"🛑 Dropped reply for chat {chat_id} (Pal was deactivated via 000)")
                    return
                if mode == "assistant" and not assistant_manager.is_active_for_chat(chat_id, is_private=event.is_private):
                    logger.info(f"🛑 Dropped reply for chat {chat_id} (Assistant was muted/deactivated)")
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
                    mark_as_replied(chat_id, event.id)
                    if mode == "pal":
                        logger.info(f"✅ Pal replied naturally in chat {chat_id}")
                    else:
                        logger.info(f"✅ Assistant replied politely in chat {chat_id}")
        except Exception as e:
            logger.error(f"⚠️ Error in incoming_message_handler execution for chat {chat_id}: {e}", exc_info=True)
                    


auto_engage_schedule = {} # dict: chat_id -> (next_engage_timestamp, configured_duration_minutes)

async def auto_engage_loop():
    """Background task that manages auto-engage scheduling per chat."""
    global auto_engage_schedule
    while True:
        try:
            # Smart Dispatcher Loop: Wake up based on config
            await asyncio.sleep(Config.AUTO_ENGAGE_LOOP_INTERVAL_SECONDS)
            now = datetime.now(timezone.utc).timestamp()
            
            global my_info
            if not my_info:
                continue
            my_id = my_info.id
            
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
                    auto_engage_schedule[chat_id] = (now + random.uniform(min_delay, max_delay), duration_minutes)
                    
                next_time, _ = auto_engage_schedule[chat_id]
                    
                # Is it time to engage for this specific chat?
                if now < next_time:
                    continue # Not time yet
                    
                # IT'S TIME! Reschedule for the next cycle immediately
                next_delay = random.uniform(duration_minutes * 0.75, duration_minutes * 1.25) * 60
                auto_engage_schedule[chat_id] = (now + next_delay, duration_minutes)
                
                try:
                    # Verify auto-engage is still active
                    if not pal_manager.is_auto_engage_active(chat_id):
                        continue

                    # Check if I have sent a message recently to avoid talking too much
                    recent_my_msgs = await client.get_messages(chat_id, limit=Config.SHORT_TERM_MEMORY_LIMIT, from_user="me")
                    if recent_my_msgs:
                        last_mine = recent_my_msgs[0].date.replace(tzinfo=timezone.utc).timestamp()
                        # If I spoke recently (relative to the configured duration), skip
                        if now - last_mine < (duration_minutes * 60 * 0.75):
                            logger.debug(f"[LIFECYCLE] Auto-Engage skipped in {chat_id} (I spoke recently).")
                            continue # I already talked recently, skip engaging.
                    
                    # Also, only engage if there is actually some recent conversation!
                    latest_msgs = await client.get_messages(chat_id, limit=1)
                    if not latest_msgs:
                        continue
                    
                    # Prevent auto-engaging if the very last message in the chat was sent by me
                    latest_msg = latest_msgs[0]
                    if latest_msg.out or latest_msg.sender_id == my_id:
                        continue
                        
                    # 🚀 EARLY EXIT: Don't burn API tokens if we already replied to this message
                    if is_already_replied(chat_id, latest_msg.id):
                        logger.debug(f"[LIFECYCLE] Auto-Engage skipped in {chat_id} (Latest message already replied to).")
                        continue
                        
                    # 🚀 EARLY EXIT: Don't burn API tokens auto-engaging with other bots
                    try:
                        latest_sender = await latest_msg.get_sender()
                        if latest_sender and getattr(latest_sender, 'bot', False):
                            logger.debug(f"[LIFECYCLE] Auto-Engage skipped in {chat_id} (Latest message is from a bot).")
                            continue
                    except Exception:
                        pass
                        
                    last_msg_time = latest_msgs[0].date.replace(tzinfo=timezone.utc).timestamp()
                    # A chat is dead if no one spoke in 30 mins OR 1.5x the configured duration
                    dead_threshold = max(30 * 60, duration_minutes * 60 * 1.5)
                    if now - last_msg_time > dead_threshold:
                        logger.debug(f"[LIFECYCLE] Auto-Engage skipped in {chat_id} (Chat is dead).")
                        continue # Chat is dead, don't randomly talk to nobody.
                    
                    if not pal_manager.is_auto_engage_active(chat_id):
                        continue

                    # Provide the chat context for AI to formulate response
                    history_text = await get_recent_chat_history(chat_id, limit=Config.SHORT_TERM_MEMORY_LIMIT, include_id=True)
                    valid_ids = re.findall(r'\(ID:\s*(\d+)\)', history_text)
                    valid_ids_str = ", ".join(valid_ids) if valid_ids else "هیچکدام"
                    
                    now_persian = get_current_persian_datetime()
                    ltm = memory_manager.get_long_term_summary(chat_id)
                    ltm_context = f"\n[خلاصه سوابق مهم قبلی]:\n{ltm}\n" if ltm else ""
                    
                    prompt_input = Prompt.AUTO_ENGAGE_TEMPLATE.format(
                        current_time=now_persian,
                        long_term_context=ltm_context,
                        history_text=history_text,
                        valid_ids_str=valid_ids_str,
                        duration_minutes=duration_minutes,
                        owner_first_name=Config.OWNER_FIRST_NAME
                    )
                    
                    # Dynamically get the active persona instead of assuming 'normal'
                    pal_variant = pal_manager.get_mode(chat_id)
                    system_prompt = persona_manager.get_prompt(pal_variant)
                    
                    logger.debug(f"[LIFECYCLE] Auto-Engage prompting Gemini for chat {chat_id}...")
                    response = await get_response(prompt_input, system_prompt, is_json=True, start_model="CHEAPEST")
                    logger.debug(f"[LIFECYCLE] Auto-Engage Gemini response received (Length: {len(response or '')})")
                    if not response or response == Text.ERROR:
                        continue
                        
                    try:
                        # Extract JSON block
                        json_match = re.search(r'\{.*\}', response, re.DOTALL)
                        if json_match:
                            data = json.loads(json_match.group(0))
                            target_id = data.get("selected_id")
                            reply_text = data.get("reply_text")
                            if reply_text:
                                reply_text = clean_outbound_text(reply_text)
                            
                            if target_id is not None and str(target_id).lower() != "null" and reply_text:
                                try:
                                    target_id = int(target_id)
                                except (ValueError, TypeError):
                                    logger.warning(f"⚠️ Invalid target_id from AI: {target_id}")
                                    continue
                                
                                # Prevent the AI from replying to its own messages!
                                target_msg = None
                                try:
                                    target_msgs = await client.get_messages(chat_id, ids=[target_id])
                                    if target_msgs:
                                        target_msg = target_msgs[0]
                                except Exception:
                                    pass
                                    
                                if not target_msg:
                                    logger.warning(f"⚠️ Auto-engage target message ({target_id}) not found or hallucinated. Ignoring!")
                                    continue
                                    
                                if target_msg.sender_id == my_id or target_msg.out:
                                    logger.warning(f"⚠️ AI tried to reply to its own message ({target_id}). Ignoring!")
                                    continue
                                
                                # Prevent the AI from replying to other bots!
                                try:
                                    target_sender = await target_msg.get_sender()
                                    if target_sender and getattr(target_sender, 'bot', False):
                                        logger.warning(f"⚠️ AI tried to reply to a bot ({target_id}). Ignoring!")
                                        continue
                                except Exception:
                                    pass
                                
                                # Final check before sending auto engage message
                                if not pal_manager.is_auto_engage_active(chat_id):
                                    logger.info(f"🛑 Dropped auto-engage in chat {chat_id} (Deactivated via 777 engage off)")
                                    continue
                                    
                                if is_already_replied(chat_id, target_id):
                                    logger.warning(f"⚠️ Dropped auto-engage in chat {chat_id} (Already replied to target_id {target_id} before)")
                                    continue

                                human_typing_time = calculate_human_typing_delay(reply_text)
                                input_chat = await client.get_input_entity(chat_id)
                                async with global_ai_lock:
                                    async with ContinuousTyping(client, input_chat):
                                        await asyncio.sleep(human_typing_time)
                                        if not pal_manager.is_auto_engage_active(chat_id):
                                            continue
                                            
                                        # Check again after sleep to prevent race conditions with the normal reply handler
                                        if is_already_replied(chat_id, target_id):
                                            logger.warning(f"⚠️ Dropped auto-engage in chat {chat_id} (Already replied while typing)")
                                            continue
                                            
                                        await client.send_message(input_chat, reply_text, reply_to=target_id)
                                        mark_as_replied(chat_id, target_id)
                                        logger.info(f"🕵️ Auto-Engaged naturally in chat {chat_id}")
                    except json.JSONDecodeError:
                        pass # Ignore if AI failed to output valid JSON
                        
                except Exception as e:
                    logger.error(f"⚠️ Auto-Engage error in chat {chat_id}: {e}", exc_info=True)
                    
        except Exception as e:
            logger.critical(f"🔥 FATAL ERROR in auto-engage task: {e}")
            await asyncio.sleep(Config.FATAL_ERROR_RETRY_SECONDS) # Sleep before retrying loop on fatal error

# ==========================================================
# 🌟 MAIN STARTUP
# ==========================================================
def main():
    global my_info
    client.start()
    my_info = client.loop.run_until_complete(client.get_me())
    
    # Start background loops
    client.loop.create_task(auto_engage_loop())
    
    logger.info("=" * 50)
    logger.info(f"👻 GhostGram (روح‌گرام) is ONLINE & READY!")
    logger.info(f"👤 Logged in as: {my_info.first_name} (@{my_info.username}) [ID: {my_info.id}]")
    from api_tracker import MODELS_CONFIG
    top_model = MODELS_CONFIG[0]['name'] if MODELS_CONFIG else "Unknown"
    logger.info(f"🧠 Primary Model: {top_model} (Auto-Cascading enabled)")
    logger.info(f"📱 Active Pal Chats (777): {pal_manager.get_active_count()}")
    logger.info(f"🕵️ Auto-Engage Chats (777 engage): {pal_manager.get_auto_engage_count()}")
    logger.info(f"💼 Assistant Mode (666): {'ON (All DMs)' if assistant_manager.dm_enabled else 'OFF'}")
    logger.info("🚀 Listening for secret codes (777, 777 engage, 666, 000, 444, 555, 333, 999, 111, 888)...")
    logger.info("=" * 50)
    
    # Block and listen for messages indefinitely
    client.run_until_disconnected()
    
def master_launcher():
    import sys
    import os
    import subprocess
    import time
    import glob
    
    # If a specific profile is requested, just run normally as a worker
    if "--profile" in sys.argv or os.getenv("TELEAGENT_PROFILE"):
        main()
        return

    # Otherwise, act as Master Process
    processes = []
    
    # 1. Start all profiles found in the profiles/ directory
    if os.path.exists("profiles"):
        for p_name in os.listdir("profiles"):
            profile_path = os.path.join("profiles", p_name)
            env_path = os.path.join(profile_path, ".env")
            
            # A profile is valid if it has a .env file
            if os.path.isdir(profile_path) and os.path.exists(env_path):
                logger.info(f"🚀 [MASTER] Launching PROFILE: {p_name}...")
                env_copy = os.environ.copy()
                env_copy["TELEAGENT_PROFILE"] = p_name
                p = subprocess.Popen([sys.executable, "main.py", "--profile", p_name], env=env_copy)
                processes.append(p)
                
    if not processes:
        if os.getenv("API_ID") and os.getenv("API_HASH"):
            logger.info("🚀 [MASTER] Cloud Mode Detected! No profiles found, but environment variables exist. Running single bot...")
            main()
            return
            
        logger.error("❌ [MASTER] No profiles found! Please run 'run.bat' or 'python setup.py' to configure a bot.")
        return
        
    logger.info(f"🌟 [MASTER] Running {len(processes)} bot(s) concurrently. Press Ctrl+C to stop all.")
    try:
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        logger.info("\n🛑 [MASTER] Shutting down all bots gracefully...")
        for p in processes:
            p.terminate()
        time.sleep(2)

if __name__ == '__main__':
    master_launcher()


