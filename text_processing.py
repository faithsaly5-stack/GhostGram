import re
import html
import emoji

# ==========================================================
# 📥 INBOUND TEXT PROCESSING (Telegram -> Bot)
# ==========================================================

def normalize_digits(text: str) -> str:
    """Normalizes Persian/Arabic digits, ZWNJ, and whitespace to standard ASCII format.
    Used for parsing inbound user commands reliably."""
    if not text:
        return ""
    text = emoji.demojize(text) 
    mapping = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
    }
    cleaned = text.replace('\u00a0', ' ')
    for char, digit in mapping.items():
        cleaned = cleaned.replace(char, digit)
    allowed_pattern = re.compile(r'[^a-zA-Z0-9\u0600-\u06FF\u200c\s\.,!\?؟،؛:;\'"()\[\]{}<>_\-+=*&%$#@|\\/~^`]+')
    cleaned = allowed_pattern.sub(' ', cleaned)
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
        clean_text = emoji.replace_emoji(raw_text, replace='')
        clean_text = html.unescape(clean_text)
        clean_text = re.sub(r'<[^>]+>', '', clean_text)
        
        # Convert ZWNJ (نیم‌فاصله) to space for casual human-like style
        clean_text = clean_text.replace('\u200c', ' ')
        clean_text = re.sub(r'[ \t]+', ' ', clean_text)
        clean_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', clean_text).strip()
        clean_text = clean_text.rstrip('.…۔')
        # Safety net: If the AI only sent dots and we stripped them all, return a default string to prevent Telegram crash.
        if not clean_text:
            return "موردی برای نمایش وجود ندارد." # Or any fallback message like "?"

        return clean_text
    except Exception as e:
        print(f"⚠️ Text cleaning error: {e}")
        return raw_text
