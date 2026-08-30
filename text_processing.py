import re
import html
import emoji

# ==========================================================
# 📥 INBOUND TEXT PROCESSING (Telegram -> Bot)
# ==========================================================

def normalize_digits(text: str) -> str:
    """Normalizes Persian/Arabic digits and whitespace to standard ASCII format.
    Used for parsing inbound user commands reliably."""
    if not text:
        return ""
    
    mapping = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
    }
    
    cleaned = text.replace('\u00a0', ' ')
    for char, digit in mapping.items():
        cleaned = cleaned.replace(char, digit)
        
    # Strip invisible directional marks that break command parsing, instead of whitelisting characters
    cleaned = re.sub(r'[\u200b-\u200f\u202a-\u202e\u2066-\u2069]', '', cleaned)
    
    return re.sub(r'\s+', ' ', cleaned).strip()

def truncate_text_segment(text: str, max_chars: int) -> str:
    """
    If a text segment is too long, intelligently truncates it to the first appropriate natural boundary.
    Finds natural sentence/phrase boundaries like punctuation and line breaks.
    Used during inbound memory assembly.
    """
    if not text:
        return ""

    text = text.strip()
    if len(text) <= max_chars:
        return text

    segment = text[:max_chars]
    for delimiter in ["\n", ".\n", ". ", "؟", "!", "،", " - ", " "]:
        last_pos = segment.rfind(delimiter, int(max_chars * 0.5))
        if last_pos != -1:
            return segment[:last_pos].strip() + "..."
    
    return segment.strip() + "..."


# ==========================================================
# 📤 OUTBOUND TEXT PROCESSING (Bot -> Telegram)
# ==========================================================

def clean_outbound_text(raw_text: str) -> str:
    """Cleans AI responses before sending them out to Telegram."""
    if not raw_text:
        return ""
    try:
        clean_text = html.unescape(raw_text)
        
        # Security: Strip ALL emojis before sending, as requested.
        clean_text = emoji.replace_emoji(clean_text, replace='')
        
        # Security: Prevent Prompt Injection from triggering our own command handlers.
        # If the AI's response starts with one of our command prefixes, we prepend an 
        # invisible Zero-Width Space (\u200B) to it. This prevents it from matching the 
        # '^' anchor in main.py, completely neutralizing the attack without mangling text.
        if re.match(r'^\s*(777|888|555|101|333|999|998|111|000|666|444|222)\b', clean_text):
            clean_text = '\u200B' + clean_text
            
        # Convert ZWNJ (نیم‌فاصله) to space for casual human-like style
        clean_text = clean_text.replace('\u200c', ' ')
        
        # Limit consecutive newlines without destroying code indentation
        clean_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', clean_text).strip()
        
        clean_text = clean_text.rstrip('.…۔')
        
        # Safety net: If the AI only sent dots and we stripped them all, return a default string
        if not clean_text:
            return "موردی برای نمایش وجود ندارد."

        return clean_text
    except Exception as e:
        print(f"⚠️ Text cleaning error: {e}")
        return raw_text
