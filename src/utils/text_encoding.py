"""Helpers for text that must fit legacy MariaDB utf8 (3-byte) columns."""


def mariadb_safe_text(value) -> str:
    """Drop UTF-8 code points that need 4 bytes (emojis, etc.) for utf8 columns."""
    if value is None:
        return ""
    return "".join(c for c in str(value) if len(c.encode("utf-8")) <= 3)
