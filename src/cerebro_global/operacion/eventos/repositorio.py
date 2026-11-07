"""Bitácora idempotente en JSON para validar el ecosistema sin tocar la base."""

from __future__ import annotations

import uuid
from datetime import datetime

from .archivo import guardar, leer

def registrar(*args, **kwargs) -> str | None:
    """Registra un hecho una sola vez; el mismo evento_id se puede reintentar.
    Soporta firmas:
      registrar(db, tipo, origen, cuerpo=None, evento_id=None)
      registrar(tipo, origen, cuerpo=None, evento_id=None)
    """
    if len(args) >= 2 and not isinstance(args[0], str):
        _db = args[0]
        tipo = str(args[1])
        origen = str(args[2]) if len(args) > 2 else kwargs.get("origen", "")
        cuerpo = args[3] if len(args) > 3 else kwargs.get("cuerpo", None)
        evento_id = args[4] if len(args) > 4 else kwargs.get("evento_id", None)
    else:
        tipo = str(args[0]) if args else kwargs.get("tipo", "")
        origen = str(args[1]) if len(args) > 1 else kwargs.get("origen", "")
        cuerpo = args[2] if len(args) > 2 else kwargs.get("cuerpo", None)
        evento_id = args[3] if len(args) > 3 else kwargs.get("evento_id", None)

    ident = str(evento_id or uuid.uuid4())
    datos = leer()
    if any(str(item.get("evento_id")) == ident for item in datos["eventos"]):
        return ident
    datos["eventos"].append({
        "evento_id": ident,
        "tipo": str(tipo),
        "origen": str(origen),
        "ocurrido_en": datetime.now().isoformat(timespec="seconds"),
        "cuerpo": dict(cuerpo or {}),
    })
    datos["eventos"] = datos["eventos"][-1000:]
    return ident if guardar(datos) else None


def listar(*args, **kwargs) -> list[dict]:
    """Soporta firmas:
      listar(db, limite=100)
      listar(limite=100)
    """
    if args and not isinstance(args[0], (int, float)):
        limite = args[1] if len(args) > 1 else kwargs.get("limite", 100)
    elif args:
        limite = args[0]
    else:
        limite = kwargs.get("limite", 100)
    return list(reversed((leer().get("eventos") or [])[-max(1, int(limite)):]))
