import asyncio
import random
import time
from config import Config

# ==========================================================
# 🧠 HUMAN SIMULATION STATE
# ==========================================================
_chat_latest_msg = {}
_chat_typing_status = {}
MAX_BEHAVIOR_TRACKER_ENTRIES = 3000

def update_latest_message(chat_id: int, sender_id: int, msg_id: int):
    """Tracks the latest message ID for a specific user to debounce rapid spam."""
    if len(_chat_latest_msg) > MAX_BEHAVIOR_TRACKER_ENTRIES:
        # Prune oldest entries to guarantee strictly bounded memory
        keys_to_prune = list(_chat_latest_msg.keys())[:MAX_BEHAVIOR_TRACKER_ENTRIES // 4]
        for k in keys_to_prune:
            _chat_latest_msg.pop(k, None)
            
    user_key = (chat_id, sender_id) if sender_id else (chat_id, "unknown")
    _chat_latest_msg[user_key] = msg_id

def update_typing_status(chat_id: int, user_id: int = None):
    """Updates the last known time a user was seen actively typing."""
    if len(_chat_typing_status) > MAX_BEHAVIOR_TRACKER_ENTRIES:
        keys_to_prune = list(_chat_typing_status.keys())[:MAX_BEHAVIOR_TRACKER_ENTRIES // 4]
        for k in keys_to_prune:
            _chat_typing_status.pop(k, None)
            
    t = time.time()
    if chat_id:
        _chat_typing_status[chat_id] = t
    if user_id:
        _chat_typing_status[user_id] = t

def is_superseded(chat_id: int, sender_id: int, current_msg_id: int) -> bool:
    """Checks if a newer message has arrived from this user in this chat."""
    user_key = (chat_id, sender_id) if sender_id else (chat_id, "unknown")
    return _chat_latest_msg.get(user_key, 0) > current_msg_id

# ==========================================================
# ⏱️ READING & BATCHING LOGIC (DEBOUNCE)
# ==========================================================
async def simulate_reading_and_batching(event, incoming_text: str) -> bool:
    """
    Simulates human reading speed, watches for active typing, and handles debouncing.
    Returns True if this thread should ABORT (because a newer message arrived), False otherwise.
    """
    chat_id = event.chat_id
    sender_id = getattr(event, 'sender_id', None)
    user_key = (chat_id, sender_id) if sender_id else (chat_id, "unknown")
    is_private = getattr(event, 'is_private', False)

    if is_private:
        # Voice Note Listening Simulation vs Text Reading Speed
        is_voice = incoming_text.startswith("[Voice Note]")
        if is_voice:
            # Simulate listening to the audio. 
            # Average speaking speed is ~12 chars per second.
            # We cap at configured seconds (simulates listening at ~1.5x-2.0x speed for very long notes)
            simulated_listen_time = len(incoming_text) / 12.0
            reading_delay = min(simulated_listen_time, Config.MAX_VOICE_LISTEN_DELAY_SECONDS)
        else:
            # Fast text reading (~25 chars per sec). Capped at 6s for responsiveness.
            base_reading_time = 1.5 + (len(incoming_text) / 25.0)
            reading_delay = min(base_reading_time, 6.0)
            
        await asyncio.sleep(reading_delay)
        
        start_wait_time = time.time()
        while True:
            # If a newer message arrived from this user, abort (batching: newer message takes over)
            if _chat_latest_msg.get(user_key, 0) > event.id:
                return True
                
            # Safety ceiling: avoid waiting longer than configured seconds under any circumstance
            if time.time() - start_wait_time > Config.MAX_DEBOUNCE_WAIT_SECONDS:
                break
                
            # Check if user is typing (activity within last 7 seconds)
            last_typing_time = max(_chat_typing_status.get(chat_id, 0), _chat_typing_status.get(sender_id, 0) if sender_id else 0)
            if time.time() - last_typing_time < 7.0:
                await asyncio.sleep(2.0)
                continue
                
            # Not typing. Wait a brief "thinking gap" in case they are about to type
            await asyncio.sleep(2.5)
            
            # Final check before proceeding
            if _chat_latest_msg.get(user_key, 0) > event.id:
                return True
            last_typing_time = max(_chat_typing_status.get(chat_id, 0), _chat_typing_status.get(sender_id, 0) if sender_id else 0)
            if time.time() - last_typing_time < 7.0:
                continue # They started typing again during the gap!
                
            break # Ready to process the batch!
    else:
        # For Groups: Snappier fixed window to batch consecutive messages
        is_voice = incoming_text.startswith("[Voice Note]")
        if is_voice:
            simulated_listen_time = len(incoming_text) / 12.0
            reading_delay = min(simulated_listen_time, 20.0)
        else:
            base_reading_time = 1.5 + (len(incoming_text) / 30.0)
            reading_delay = min(base_reading_time, 4.0)
            
        await asyncio.sleep(reading_delay + random.uniform(1.0, 2.5)) # Base delay + jitter
        
        if _chat_latest_msg.get(user_key, 0) > event.id:
            return True

    return False

# ==========================================================
# ✍️ TYPING SIMULATION LOGIC
# ==========================================================
def calculate_human_typing_delay(text: str) -> float:
    """
    Calculates a human-like, proportional typing duration based on message length,
    punctuation pauses, and natural variance.
    Uses a piecewise linear function to match real fast-typist WPM (60-80 WPM),
    while strictly capping extremely long AI essays to prevent UX frustration.
    """
    if not text:
        return 1.2
    
    text = text.strip()
    length = len(text)
    
    # Piecewise curve mapping length to realistic typing time (excluding pauses)
    if length < 20:
        base_time = 1.5 + (length * 0.1)             # 1.5s -> 3.5s
    elif length < 100:
        base_time = 3.5 + ((length - 20) * 0.08)     # 3.5s -> 9.9s
    else:
        base_time = 9.9 + ((length - 100) * 0.04)    # 9.9s -> 25.9s (for 500 chars)
    
    # Natural punctuation pauses
    punctuation_count = text.count('\n') + text.count('.') + text.count('!') + text.count('؟') + text.count('،')
    pause_time = min(punctuation_count * 0.25, 3.0)
    
    # Natural human variance/jitter
    jitter = random.uniform(-0.5, 1.5)
    
    total_delay = base_time + pause_time + jitter
    
    # Strict maximum cap: Never wait more than max typing delay to send a message.
    return max(Config.MIN_TYPING_DELAY, min(total_delay, Config.MAX_TYPING_DELAY))

def ContinuousTyping(client, input_chat_or_id):
    """
    Returns an asynchronous context manager that ensures Telegram's '... is typing' action
    is continuously active at the top of the chat throughout the entire lifecycle.
    """
    return client.action(input_chat_or_id, 'typing')
