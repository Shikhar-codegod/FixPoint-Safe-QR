import re
import hmac
import hashlib
from django.conf import settings

def normalize_phone_number(phone: str) -> str:
    """
    Normalises phone number to standard E.164 format.
    Defaults to India (+91) for standard 10-digit mobile numbers.
    """
    if not phone or not isinstance(phone, str):
        raise ValueError("Phone number must be provided.")
    
    # Strip spaces, dashes, dots, parentheses
    cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone.strip())
    
    if cleaned.startswith('00'):
        cleaned = '+' + cleaned[2:]
    elif cleaned.startswith('0') and len(cleaned) == 11 and cleaned[1] in '6789':
        cleaned = '+91' + cleaned[1:]
    elif len(cleaned) == 10 and cleaned[0] in '56789':
        cleaned = '+91' + cleaned
    elif not cleaned.startswith('+') and len(cleaned) >= 11:
        cleaned = '+' + cleaned

    # Validate E.164 format: + followed by 7 to 15 digits, starting non-zero
    if not re.match(r'^\+[1-9]\d{6,14}$', cleaned):
        raise ValueError(
            f"Invalid phone number '{phone}'. Must be a valid E.164 phone number (e.g. +919876543210)."
        )
    return cleaned

def compute_phone_hash(normalized_phone: str) -> str:
    """
    Computes deterministic HMAC-SHA256 hash using a key derived from FIELD_ENCRYPTION_KEY.
    Ensures unique phone constraint per user without exposing plaintext in DB or logs.
    """
    key = getattr(settings, 'FIELD_ENCRYPTION_KEY', 'default-key').encode('utf-8')
    derived_salt = hashlib.sha256(b"fixpoint_phone_hash_salt:" + key).digest()
    return hmac.new(derived_salt, normalized_phone.encode('utf-8'), hashlib.sha256).hexdigest()

def mask_phone_number(phone: str) -> str:
    """
    Masks a phone number for safe display/logging, e.g. +919876543210 -> +91******3210.
    """
    if not phone:
        return ""
    if len(phone) <= 6:
        return "*" * len(phone)
    prefix_len = 3 if phone.startswith('+') else 2
    suffix_len = 4
    if len(phone) <= prefix_len + suffix_len:
        return phone[:prefix_len] + "*" * (len(phone) - prefix_len)
    masked_count = len(phone) - prefix_len - suffix_len
    return phone[:prefix_len] + ("*" * masked_count) + phone[-suffix_len:]
