"""Helpers to keep text compatible with legacy MariaDB utf8 (3-byte) columns."""
import re

_EMOJI_PREFIX_TAGS = (
    "🔥 [OFERTA] ",
    "🔥 [OFERTA]",
    "[OFERTA] ",
    "[OFERTA]",
    "📦 [MAYOREO] ",
    "📦 [MAYOREO]",
    "🌟 ",
    "🏷️ ",
)


def sanitize_mariadb_text(value) -> str:
    """Strip UI emoji prefixes and chars that need 4-byte UTF-8 (utf8mb3-incompatible)."""
    text = str(value or "")
    for tag in _EMOJI_PREFIX_TAGS:
        text = text.replace(tag, "")
    text = re.sub(r"^(?:oferta\s+de|oferta)\s+", "", text, flags=re.IGNORECASE).strip()
    return "".join(ch for ch in text if len(ch.encode("utf-8")) <= 3)
