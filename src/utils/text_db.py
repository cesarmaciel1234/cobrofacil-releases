"""Helpers for text values stored in MariaDB (legacy utf8 / utf8mb3 columns)."""

import re

# Supplementary-plane characters (4-byte UTF-8) break utf8mb3 columns (MySQL error 1366).
_SUPPLEMENTARY_CHARS = re.compile(r"[\U00010000-\U0010ffff]")

# Prefijos con emoji en nombres de oferta (incompatible con columnas utf8 legacy de MariaDB).
_OFFER_NAME_TAGS = (
    "🔥 [OFERTA] ", "🔥 [OFERTA]", "[OFERTA] ", "[OFERTA]",
    "📦 [MAYOREO] ", "📦 [MAYOREO]", "🌟 ",
    "🎁 [COMBO] ", "🎁 [COMBO]",
)


def _coerce_text(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="ignore")
        except Exception:
            return ""
    if not isinstance(value, str):
        return str(value)
    return value


def safe_mariadb_text(value):
    """Return text safe for MariaDB utf8/utf8mb3 columns; strips emojis and other 4-byte chars."""
    if value is None:
        return value
    text = _coerce_text(value)
    for tag in _OFFER_NAME_TAGS:
        text = text.replace(tag, "")
    text = re.sub(r"^(?:oferta\s+de|oferta)\s+", "", text, flags=re.IGNORECASE).strip()
    text = _SUPPLEMENTARY_CHARS.sub("", text)
    text = "".join(ch for ch in text if len(ch.encode("utf-8")) <= 3)
    return text


def sanitize_venta_payload(venta_data, items):
    """Strip 4-byte UTF-8 from venta payload before MariaDB insert or offline queue."""
    if isinstance(venta_data, dict):
        cn = venta_data.get("cliente_nombre")
        if cn:
            venta_data["cliente_nombre"] = safe_mariadb_text(cn)
    for it in items or []:
        if not isinstance(it, dict):
            continue
        raw = it.get("nombre") or it.get("nombre_producto") or ""
        safe = safe_mariadb_text(raw)
        it["nombre"] = safe
        it["nombre_producto"] = safe


def sanitize_mariadb_params(params):
    """Recursively sanitize string values in query parameter tuples/lists."""
    if params is None:
        return None
    if isinstance(params, (list, tuple)):
        return type(params)(sanitize_mariadb_params(v) for v in params)
    if isinstance(params, dict):
        return {k: sanitize_mariadb_params(v) for k, v in params.items()}
    if isinstance(params, (str, bytes)):
        return safe_mariadb_text(params)
    return params
