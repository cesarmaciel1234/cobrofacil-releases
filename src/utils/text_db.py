"""Helpers for text values stored in MariaDB (legacy utf8 / utf8mb3 columns)."""


def safe_mariadb_text(value):
    """Return text safe for MariaDB utf8/utf8mb3 columns; strips emojis and other 4-byte chars."""
    if value is None:
        return value
    if not isinstance(value, str):
        value = str(value)
    # Fuera del BMP (p. ej. 🔥 U+1F525) → UTF-8 de 4 bytes → error 1366 en columnas utf8 legacy.
    return "".join(ch for ch in value if ord(ch) <= 0xFFFF)


def sanitize_mariadb_params(params):
    """Recursively sanitize string values in query parameter tuples/lists."""
    if params is None:
        return None
    if isinstance(params, (list, tuple)):
        return type(params)(sanitize_mariadb_params(v) for v in params)
    if isinstance(params, str):
        return safe_mariadb_text(params)
    return params
