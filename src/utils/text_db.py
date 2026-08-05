"""Helpers for text values stored in MariaDB (legacy utf8 / utf8mb3 columns)."""

import re

# Supplementary-plane characters (4-byte UTF-8) break utf8mb3 columns (MySQL error 1366).
_SUPPLEMENTARY_CHARS = re.compile(r"[\U00010000-\U0010ffff]")

# Prefijos con emoji en nombres de oferta (incompatible con columnas utf8 legacy de MariaDB).
_OFFER_NAME_TAGS = (
    "🔥 [OFERTA] ", "🔥 [OFERTA]", "[OFERTA] ", "[OFERTA]",
    "📦 [MAYOREO] ", "📦 [MAYOREO]", "🌟 ",
)


def safe_mariadb_text(value):
    """Return text safe for MariaDB utf8/utf8mb3 columns; strips emojis and other 4-byte chars."""
    if value is None:
        return value
    if not isinstance(value, str):
        value = str(value)
    text = value
    for tag in _OFFER_NAME_TAGS:
        text = text.replace(tag, "")
    text = re.sub(r"^(?:oferta\s+de|oferta)\s+", "", text, flags=re.IGNORECASE).strip()
    text = _SUPPLEMENTARY_CHARS.sub("", text)
    text = "".join(ch for ch in text if ord(ch) <= 0xFFFF)
    return text.strip()


def ascii_safe_mariadb_text(value):
    """Fallback for utf8mb3 columns when emojis/accents still trigger MySQL error 1366."""
    text = safe_mariadb_text(value)
    if text is None:
        return text
    return text.encode("ascii", "ignore").decode("ascii").strip()


def sanitize_mariadb_params(params):
    """Recursively sanitize string values in query parameter tuples/lists."""
    if params is None:
        return None
    if isinstance(params, (list, tuple)):
        return type(params)(sanitize_mariadb_params(v) for v in params)
    if isinstance(params, str):
        return safe_mariadb_text(params)
    return params
