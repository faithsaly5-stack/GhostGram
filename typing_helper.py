import asyncio
import random
from config import Config

def calculate_human_typing_delay(text: str) -> float:
    """
    Calculates a human-like, proportional typing duration based on message length,
    punctuation pauses, and natural variance.
    """
    if not text:
        return 1.2
    
    text = text.strip()
    length = len(text)
    
    # Non-linear character duration curve:
    # We increase the multiplier to make it slightly slower and more realistic for Farsi typing.
    # 50 chars ~ 4-5s | 150 chars ~ 8-10s | 500 chars ~ 16-18s
    base_time = (length ** 0.75) * 0.22
    
    # Natural punctuation pauses (commas, sentence breaks, question marks)
    punctuation_count = text.count('\n') + text.count('.') + text.count('!') + text.count('؟') + text.count('،')
    pause_time = min(punctuation_count * 0.4, 2.0)
    
    # Natural human variance/jitter (+/- 0.5s)
    jitter = random.uniform(-0.5, 0.8)
    
    total_delay = 1.5 + base_time + pause_time + jitter
    
    # Clamp within realistic limits
    return max(Config.MIN_TYPING_DELAY, min(total_delay, Config.MAX_TYPING_DELAY))


def ContinuousTyping(client, input_chat_or_id):
    """
    Returns an asynchronous context manager that ensures Telegram's '... is typing' action
    is continuously active at the top of the chat (both DMs and supergroups/groups)
    throughout the entire thinking + typing lifecycle.
    
    This leverages Telethon's native background task manager which flawlessly handles
    auto-cancellations and heartbeats.
    """
    return client.action(input_chat_or_id, 'typing')
