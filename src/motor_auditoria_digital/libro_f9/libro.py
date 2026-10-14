"""Libro de cobros F9. Si falla el disco, la caja igual cerró la venta."""

import json
import os
import threading
from datetime import datetime

from src.utils.paths import get_base_path

RUTA = os.path.join(get_base_path(), "reportes", "f9_manuales.json")
_LOCK = threading.RLock()


def _leer():
    if not os.path.exists(RUTA):
        return {}
    try:
        with open(RUTA, encoding="utf-8") as archivo:
            datos = json.load(archivo)
        return datos if isinstance(datos, dict) else {}
    except Exception:
        return {}


def _guardar(datos):
    os.makedirs(os.path.dirname(RUTA), exist_ok=True)
    with open(RUTA, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)


def hay(ticket):
    clave = str(ticket or "").strip()
    return bool(clave) and clave in _leer()


def lista():
    return dict(_leer())


def anotar(ticket, monto=0, metodo=""):
    clave = str(ticket or "").strip()
    if not clave:
        return

    def _trabajo():
        try:
            with _LOCK:
                datos = _leer()
                if clave in datos:
                    return
                datos[clave] = {
                    "ticket": clave,
                    "monto": float(monto or 0),
                    "metodo": str(metodo or ""),
                    "cuando": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                _guardar(datos)
            try:
                from src.motor_auditoria_digital.empleado import despertar
                despertar()
            except Exception:
                pass
        except Exception:
            pass

    threading.Thread(target=_trabajo, daemon=True, name="f9-libro").start()
