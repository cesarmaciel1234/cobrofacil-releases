"""Forma un plan reproducible sin ejecutar ninguna acción externa."""

from __future__ import annotations

import uuid
from datetime import datetime


def construir(panorama: dict | None, politica: dict | None) -> dict:
    politica = politica or {}
    return {
        "plan_id": f"plan-{uuid.uuid4()}",
        "creado_en": datetime.now().isoformat(timespec="seconds"),
        "estado": "BORRADOR",
        "politica": {
            "codigo": politica.get("codigo") or "COMPRA_AUTONOMA",
            "version": int(politica.get("version") or 1),
        },
        "acciones": list((panorama or {}).get("acciones") or []),
        "resumen": {
            "total": int((panorama or {}).get("total") or 0),
            "modo": str((panorama or {}).get("modo") or "borrador"),
        },
    }
