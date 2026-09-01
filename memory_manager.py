import os
import json
import asyncio
from datetime import datetime, timezone
from config import Config
from text import Text
from logger import logger

class MemoryManager:
    def __init__(self, state_file=Config.MEMORY_STATE_FILE):
        self.state_file = state_file
        self.reset_cutoffs = {}           # chat_id -> timestamp (float)
        self.long_term_memories = {}      # chat_id -> summary string
        self.message_counts = {}          # chat_id -> int
        self.last_summarized_msg_ids = {} # chat_id -> int (watermark message id)
        self.owner_last_active_time = {}  # chat_id -> timestamp (float)
        self.memory_limit = Config.SHORT_TERM_MEMORY_LIMIT
        self.summary_interval = Config.LONG_TERM_SUMMARY_INTERVAL
        self.max_segment_chars = Config.MAX_MESSAGE_SEGMENT_CHARS
        self.max_ltm_chars = Config.MAX_LONG_TERM_SUMMARY_CHARS
        self._chat_locks = {}
        self._bg_tasks = set()
        self.load_state()

    def _get_chat_lock(self, chat_id: int) -> asyncio.Lock:
        chat_id = int(chat_id)
        if chat_id not in self._chat_locks:
            self._chat_locks[chat_id] = asyncio.Lock()
        return self._chat_locks[chat_id]

    def load_state(self):
        """Loads memory reset timestamps, long-term summaries, and watermarks from disk."""
        if os.path.exists(self.state_file) and os.path.getsize(self.state_file) > 0:
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.reset_cutoffs = {int(k): float(v) for k, v in data.get("reset_cutoffs", {}).items()}
                        self.long_term_memories = {int(k): str(v) for k, v in data.get("long_term_memories", {}).items()}
                        self.message_counts = {int(k): int(v) for k, v in data.get("message_counts", {}).items()}
                        self.last_summarized_msg_ids = {int(k): int(v) for k, v in data.get("last_summarized_msg_ids", {}).items()}
                        self.owner_last_active_time = {int(k): float(v) for k, v in data.get("owner_last_active_time", {}).items()}
            except Exception as e:
                logger.error(f"⚠️ Error loading memory state: {e}", exc_info=True)
                self.reset_cutoffs = {}
                self.long_term_memories = {}
                self.message_counts = {}
                self.last_summarized_msg_ids = {}
                self.owner_last_active_time = {}
        else:
            self.reset_cutoffs = {}
            self.long_term_memories = {}
            self.message_counts = {}
            self.last_summarized_msg_ids = {}
            self.owner_last_active_time = {}


    def save_state(self):
        """Atomically persists all memory states and watermarks to disk (Debounced to 3 seconds)."""
        import threading
        if not hasattr(self, '_write_lock'):
            self._write_lock = threading.Lock()
            self._save_timer = None
            
        # 1. Snapshot the dictionaries synchronously to prevent race conditions during write
        self._latest_snapshot = {
            "reset_cutoffs": self.reset_cutoffs.copy(),
            "long_term_memories": self.long_term_memories.copy(),
            "message_counts": self.message_counts.copy(),
            "last_summarized_msg_ids": self.last_summarized_msg_ids.copy(),
            "owner_last_active_time": self.owner_last_active_time.copy()
        }
        
        # If a save is already scheduled within the next 3 seconds, let it naturally pick up the latest snapshot
        if self._save_timer is not None and self._save_timer.is_alive():
            return
            
        def _write_task():
            with self._write_lock:
                try:
                    data = getattr(self, '_latest_snapshot', {})
                    tmp_file = f"{self.state_file}.tmp"
                    with open(tmp_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    os.replace(tmp_file, self.state_file)
                except Exception as e:
                    logger.error(f"⚠️ Error saving memory state: {e}", exc_info=True)

        self._save_timer = threading.Timer(3.0, _write_task)
        self._save_timer.start()

    def reset_chat_memory(self, chat_id: int):
        """Sets the memory cutoff to now, clears long-term summary, count, and watermarks for this chat."""
        chat_id = int(chat_id)
        now_ts = datetime.now(timezone.utc).timestamp()
        self.reset_cutoffs[chat_id] = now_ts
        self.long_term_memories[chat_id] = ""
        self.message_counts[chat_id] = 0
        self.last_summarized_msg_ids[chat_id] = 0
        self.owner_last_active_time[chat_id] = now_ts
        self.save_state()
        return True

    def factory_reset(self):
        """Globally clears all memory (short-term and long-term) for all chats."""
        self.reset_cutoffs.clear()
        self.long_term_memories.clear()
        self.message_counts.clear()
        self.last_summarized_msg_ids.clear()
        self.owner_last_active_time.clear()
        if hasattr(self, 'virtual_messages'):
            self.virtual_messages.clear()
        self.save_state()
        logger.info("♻️ Memory Manager has been factory reset.")

    def get_cutoff_timestamp(self, chat_id: int) -> float:
        return self.reset_cutoffs.get(int(chat_id), 0.0)

    def get_long_term_summary(self, chat_id: int) -> str:
        """Returns the long-term compressed summary if available."""
        return self.long_term_memories.get(int(chat_id), "").strip()

    def update_owner_activity(self, chat_id: int):
        import time
        self.owner_last_active_time[int(chat_id)] = time.time()
        self.save_state()

    def get_owner_last_active_time(self, chat_id: int) -> float:
        return self.owner_last_active_time.get(int(chat_id), 0.0)

    def truncate_segment(self, text: str, max_chars: int = None) -> str:
        """
        If a message is too long, intelligently truncates it to the first appropriate segment.
        Finds natural sentence/phrase boundaries.
        Delegated to text_processing module.
        """
        from text_processing import truncate_text_segment
        if max_chars is None:
            max_chars = self.max_segment_chars
        return truncate_text_segment(text, max_chars)

    def add_virtual_message(self, chat_id: int, msg_id: int, text: str):
        """Maps a real Telegram message ID to a virtual text (e.g. AI Voice Note text)."""
        if not hasattr(self, 'virtual_messages'):
            self.virtual_messages = {}
        if chat_id not in self.virtual_messages:
            self.virtual_messages[chat_id] = {}
        
        self.virtual_messages[chat_id][msg_id] = text
        
        # Prevent memory leak by keeping only the last 50 virtual messages per chat
        if len(self.virtual_messages[chat_id]) > 50:
            oldest_key = next(iter(self.virtual_messages[chat_id]))
            del self.virtual_messages[chat_id][oldest_key]

    def get_virtual_text(self, chat_id: int, msg_id: int) -> str:
        """Retrieves transcribed text for a message ID if it exists."""
        if hasattr(self, 'virtual_messages'):
            return self.virtual_messages.get(int(chat_id), {}).get(int(msg_id), "")
        return ""

    async def get_chat_history(self, client, chat_id: int, format_sender_fn, my_id: int, limit: int = None, include_id: bool = False) -> str:
        """
        Fetches up to 30 recent messages respecting the reset cutoff, formatting reply context, and truncating segments.
        Optionally includes message ID for targeted replies (auto-engage).
        """
        if limit is None:
            limit = self.memory_limit
            
        cutoff_ts = self.get_cutoff_timestamp(chat_id)
        messages = []
        
        try:
            async for msg in client.iter_messages(chat_id, limit=limit):
                text = msg.text
                if not text and hasattr(self, 'virtual_messages') and chat_id in self.virtual_messages and msg.id in self.virtual_messages[chat_id]:
                    text = self.virtual_messages[chat_id][msg.id]
                    
                if not text:
                    continue
                
                msg_ts = msg.date.replace(tzinfo=timezone.utc).timestamp()
                if msg_ts <= cutoff_ts:
                    break
                
                sender = await msg.get_sender()
                name = await format_sender_fn(sender, my_id)
                time_str = msg.date.strftime("%H:%M")
                
                # Context disambiguation: Check if this message was in reply to someone
                reply_info = ""
                if msg.is_reply:
                    try:
                        reply_msg = await msg.get_reply_message()
                        if reply_msg:
                            r_sender = await reply_msg.get_sender()
                            r_name = await format_sender_fn(r_sender, my_id)
                            reply_info = f" (در پاسخ به {r_name})"
                    except Exception:
                        pass
                
                cleaned_content = self.truncate_segment(text, self.max_segment_chars)
                
                if include_id:
                    messages.append(f"(ID: {msg.id}) [{time_str}] {name}{reply_info}: {cleaned_content}")
                else:
                    messages.append(f"[{time_str}] {name}{reply_info}: {cleaned_content}")
                
        except Exception as e:
            logger.error(f"⚠️ Error reading memory for chat {chat_id}: {e}", exc_info=True)

        if not messages:
            return "گفت‌وگوی قبلی وجود ندارد (حافظه تازه است)."
            
        return "\n".join(reversed(messages))

    def record_message_and_check_summary(self, client, chat_id: int, gemini, format_sender_fn, my_id: int):
        """
        Increments message counter for this chat. When it reaches 30,
        schedules a background task to summarize and compress memory.
        """
        current_count = self.message_counts.get(chat_id, 0) + 1
        self.message_counts[chat_id] = current_count
        
        if current_count >= self.summary_interval:
            self.message_counts[chat_id] = 0
            self.save_state()
            # Run summarization in background without blocking current message
            task = asyncio.create_task(
                self.summarize_and_compress(client, chat_id, gemini, format_sender_fn, my_id)
            )
            self._bg_tasks.add(task)
            task.add_done_callback(self._bg_tasks.discard)

    async def summarize_and_compress(self, client, chat_id: int, gemini, format_sender_fn, my_id: int):
        """
        Summarizes recent messages up to 30 using watermark tracking (no missed messages, no duplicates),
        merges with existing long-term memory while protecting permanent facts against context decay.
        """
        chat_id = int(chat_id)
        lock = self._get_chat_lock(chat_id)
        
        # If another summarization is already active for this chat, skip to avoid overlapping runs
        if lock.locked():
            return
            
        async with lock:
            try:
                logger.info(f"🧠 Consolidating Long-Term Memory for chat {chat_id} (Watermarked 30-msg batch)...")
                cutoff_ts = self.get_cutoff_timestamp(chat_id)
                last_watermark = self.last_summarized_msg_ids.get(chat_id, 0)
                
                # Fetch up to Config.LONG_TERM_SUMMARY_SCAN_LIMIT messages since last watermark. If bot was offline, older messages are intentionally dropped.
                fetched_msgs = []
                iter_kwargs = {"limit": Config.LONG_TERM_SUMMARY_SCAN_LIMIT}
                if last_watermark > 0:
                    iter_kwargs["min_id"] = last_watermark
                    
                async for msg in client.iter_messages(chat_id, **iter_kwargs):
                    text = msg.text
                    if not text and hasattr(self, 'virtual_messages') and chat_id in self.virtual_messages and msg.id in self.virtual_messages[chat_id]:
                        text = self.virtual_messages[chat_id][msg.id]
                        
                    if not text:
                        continue
                        
                    msg_ts = msg.date.replace(tzinfo=timezone.utc).timestamp()
                    if msg_ts <= cutoff_ts:
                        break
                    fetched_msgs.append((msg, text))
                
                # If no new messages above watermark or cutoff, skip
                if not fetched_msgs:
                    print(f"ℹ️ No new unsummarized messages for chat {chat_id}.")
                    return
                
                # Sliding Window: Keep the 30 newest messages untouched in short-term memory
                if len(fetched_msgs) <= self.memory_limit:
                    print(f"ℹ️ Not enough messages to summarize (sliding window of {self.memory_limit}).")
                    return
                
                msgs_to_summarize = fetched_msgs[self.memory_limit:]
                
                # Update watermark to the newest message ID that is ACTUALLY being summarized
                newest_msg_id = max(m[0].id for m in msgs_to_summarize)
                
                # Format fetched messages
                formatted_lines = []
                for msg_tuple in reversed(msgs_to_summarize):
                    msg, text = msg_tuple
                    sender = await msg.get_sender()
                    name = await format_sender_fn(sender, my_id)
                    time_str = msg.date.strftime("%H:%M")
                    cleaned_content = self.truncate_segment(text, self.max_segment_chars)
                    formatted_lines.append(f"[{time_str}] {name}: {cleaned_content}")
                    
                history_text = "\n".join(formatted_lines)
                if not history_text.strip():
                    return
                
                existing_summary = self.get_long_term_summary(chat_id)
                
                if not existing_summary:
                    prompt = f"""
متن زیر مکالمه اخیر در تلگرام است (تا ۳۰ پیام اخیر):
{history_text}

وظیفه:
اطلاعات مهم، کلیدی، اسامی، توافق‌ها و تصمیمات اساسی این گفتگو را در ۲ الی ۴ خط بسیار فشرده و متراکم (بولتی یا کلمات کلیدی) استخراج کن.
خروجی باید بسیار خلاصه، مفید، کم‌حجم و کاملاً متنی باشد. هیچ توضیح اضافی ننویس.
"""
                else:
                    prompt = f"""
حافظه و سوابق قبلی گفتگو:
{existing_summary}

پیام‌های جدید گفتگو:
{history_text}

وظیفه:
سوابق قبلی و پیام‌های جدید را با هم ادغام و فشرده‌سازی کن.
قوانین اکید:
۱. اسامی، تصمیمات، توافقات و فکت‌های کلیدی قبلی نباید حذف شوند (جلوگیری از فراموشی اطلاعات کلیدی).
۲. اطلاعات جدید را با قبلی ترکیب کن و یک خلاصه فوق‌العاده کوتاه، متراکم و حداکثر در ۳ الی ۴ خط ارائه بده.
۳. خروجی باید کاملاً متنی، بدون مقدمه و بدون هیچ توضیح اضافی باشد.
"""

                new_summary = await gemini.get_response(
                    prompt, 
                    "تو یک سیستم فشرده‌ساز و حافظه‌نگار هوشمند هستی. خروجی فقط نکات فشرده.", 
                    start_model="CHEAPEST"
                )
                if new_summary and new_summary != Text.ERROR:
                    new_summary = new_summary.strip()
                    
                    # Check if it exceeds max size; if so, do a secondary compression pass
                    if len(new_summary) > self.max_ltm_chars:
                        compress_prompt = f"متن زیر را به صورت فوق‌العاده فشرده در حداکثر ۳ خط بازنویسی کن تا حجم بسیار کمی بگیرد:\n{new_summary}"
                        compacted = await gemini.get_response(
                            compress_prompt, 
                            "فشرده‌ساز متنی.", 
                            start_model="CHEAPEST"
                        )
                        if compacted and compacted != Text.ERROR:
                            new_summary = compacted.strip()
                            
                    self.long_term_memories[chat_id] = new_summary
                    self.last_summarized_msg_ids[chat_id] = newest_msg_id
                    self.save_state()
                    print(f"✅ Long-Term Memory updated for chat {chat_id} (Watermark: {newest_msg_id}, {len(new_summary)} chars):\n{new_summary}")
                    
            except Exception as e:
                print(f"⚠️ Error during long-term memory summarization: {e}")

# Global singleton instance
memory_manager = MemoryManager()
