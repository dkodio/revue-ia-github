"""Réduction des fuites courantes, sans prétendre détecter tous les secrets."""
import os
import re


def redact(text: str) -> str:
    for key, value in os.environ.items():
        if any(word in key for word in ("TOKEN", "SECRET", "PASSWORD", "API_KEY")) and len(value) >= 8:
            text = text.replace(value, "[SECRET_MASQUE]")
    text = re.sub(r"-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----", "[CLE_PRIVEE_MASQUEE]", text, flags=re.S)
    text = re.sub(r"(?i)((?:password|api_key|token|secret)\s*[=:]\s*)[\"']([^\"'\n]{8,})[\"']", r'\1"[SECRET_MASQUE]"', text)
    text = re.sub(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b", "[SECRET_MASQUE]", text)
    return text


def safe_markdown(text: str) -> str:
    # Les commentaires générés sont du texte, jamais du HTML ou des mentions actives.
    text = redact(text).replace("@", "＠")
    return re.sub(r"([\\`*_{}\[\]()<>#+.!|~-])", r"\\\1", text)


def sanitize(value):
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items()}
    return value
