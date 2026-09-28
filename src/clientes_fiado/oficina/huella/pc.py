"""Quién, dónde y cuándo. Todo lo que firma un evento de cliente sale de acá."""

from __future__ import annotations

import hashlib
import itertools
import re
import secrets
import socket
import uuid
from datetime import datetime

_pc: str | None = None
_secuencia = itertools.count()


def _guid_maquina() -> str:
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as k:
            return str(winreg.QueryValueEx(k, "MachineGuid")[0])
    except Exception:
        return str(uuid.getnode())


def pc_id() -> str:
    """
    `NOMBREPC-XXXX`: el nombre de Windows más 4 letras de la huella de la máquina.
    `config.pc_id` lo fija a mano. No cambia entre reinicios.
    """
    global _pc
    if _pc:
        return _pc
    try:
        from src.config import config

        fijo = str(config.get("pc_id", "") or "").strip()
    except Exception:
        fijo = ""
    if fijo:
        _pc = fijo[:60]
        return _pc
    host = re.sub(r"[^A-Za-z0-9_]", "", socket.gethostname() or "PC").upper()[:20] or "PC"
    corto = hashlib.sha1(_guid_maquina().encode("utf-8")).hexdigest()[:4].upper()
    _pc = f"{host}-{corto}"
    return _pc


def usuario() -> str:
    try:
        from src.config import config

        u = config.current_user or {}
        return str(u.get("username") or u.get("nombre") or "sistema").strip()[:80] or "sistema"
    except Exception:
        return "sistema"


def caja() -> str:
    try:
        from src.config import config

        return str(config.get("caja_id", "") or "")[:10]
    except Exception:
        return ""


def ahora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def nuevo_uid() -> str:
    """ID único de un cliente: PC + fecha y hora + 6 hex al azar. Dice dónde y cuándo nació."""
    return f"{pc_id()}-{datetime.now():%Y%m%d%H%M%S}-{secrets.token_hex(3)}"


def nuevo_evento() -> str:
    """Ordenable: dentro de una PC, el orden alfabético es el orden en que pasaron."""
    return f"{pc_id()}-{datetime.now():%Y%m%d%H%M%S%f}-{next(_secuencia) % 10000:04d}{secrets.token_hex(2)}"
