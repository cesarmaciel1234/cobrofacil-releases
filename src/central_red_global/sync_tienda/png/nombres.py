"""Nombres y multipart de PNG de vitrina."""

from __future__ import annotations

import os


def sanitizar_nombre_png(nombre: str) -> str:
    raw = os.path.basename(str(nombre or "producto.png")).strip()
    for ch in '/\\:*?"<>|':
        raw = raw.replace(ch, "")
    raw = raw.replace(" ", "_").strip("._") or "producto"
    if not raw.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        raw += ".png"
    return raw


def extraer_png_multipart(content_type: str, body: bytes):
    if "multipart/form-data" not in (content_type or "").lower():
        return None, None
    import email

    wrapped = (
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
        + body
    )
    msg = email.message_from_bytes(wrapped)
    for part in msg.walk():
        name = part.get_filename()
        if not name:
            continue
        payload = part.get_payload(decode=True)
        if payload:
            return name, payload
    return None, None
