import re
import hashlib

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_REGEX = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{10}\b')
URL_REGEX = re.compile(r'https?://\S+|www\.\S+')
HTML_TAG_REGEX = re.compile(r'<[^>]+>')
SIGNATURE_REGEX = re.compile(r'(?i)(--\s*\n.*|sent from my (iphone|android|galaxy)|regards,.*|cheers,.*|thanks and regards,.*)', re.DOTALL)
CARD_REGEX = re.compile(r'\b(?:\d[ -]*?){13,16}\b')

def clean_and_mask_text(raw_text: str) -> tuple[str, str]:
    """
    Cleans raw customer feedback:
    - Strips HTML tags, email signatures, URLs
    - Normalises whitespace
    - Masks PII (Emails, Phone numbers, Cards)
    Returns: (cleaned_text, detected_language)
    """
    if not raw_text or not isinstance(raw_text, str):
        return "", "en"

    # 1. Remove HTML tags
    text = HTML_TAG_REGEX.sub(" ", raw_text)

    # 2. Remove common email signatures
    text = SIGNATURE_REGEX.sub(" ", text)

    # 3. Remove URLs
    text = URL_REGEX.sub(" ", text)

    # 4. Mask PII
    text = CARD_REGEX.sub("[CARD_MASKED]", text)
    text = EMAIL_REGEX.sub("[EMAIL_MASKED]", text)
    text = PHONE_REGEX.sub("[PHONE_MASKED]", text)

    # 5. Normalise whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # 6. Basic language check
    lang = detect_simple_language(text)

    return text, lang

def detect_simple_language(text: str) -> str:
    """
    Lightweight heuristic language detector.
    Detects Devanagari (Hindi/Marathi) vs Latin/English script.
    """
    if not text:
        return "en"
    
    # Check for Devanagari Unicode block (\u0900-\u097F)
    devanagari_chars = re.findall(r'[\u0900-\u097F]', text)
    if len(devanagari_chars) > len(text) * 0.2:
        return "hi/mr"
    
    return "en"

def compute_content_hash(source_id: int, external_id: str | None, text: str) -> str:
    """
    Generates a deterministic SHA256 fingerprint for deduplication.
    """
    base = f"{source_id}::{(external_id or '').strip()}::{text.strip().lower()}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()
