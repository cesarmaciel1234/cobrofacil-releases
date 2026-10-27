"""Libro local de tickets digitales. No borra historia. Si no hay red, queda lo último asentado."""

import json
import os
import threading

from src.utils.paths import get_base_path

RUTA = os.path.join(get_base_path(), "reportes", "tickets_digitales.json")
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


def fusionar(filas, avisar=False):
    """Suma o actualiza tickets. No saca uno que ya estaba. Si el disco falla, no lanza."""
    if not filas:
        return
    try:
        with _LOCK:
            datos = _leer()
            for venta in filas:
                nro = str((venta or {}).get("ticket") or "").strip()
                if not nro:
                    continue
                est = str((venta or {}).get("estado") or "COMPLETADA").upper().strip()
                canc = bool((venta or {}).get("cancelado") or est in ("CANCELADA", "ANULADA", "CANCELADO", "ANULADO"))
                datos[nro] = {
                    "ticket": nro,
                    "fecha": str((venta or {}).get("fecha") or "")[:19],
                    "monto": float((venta or {}).get("monto") or 0),
                    "metodo": str((venta or {}).get("metodo") or ""),
                    "clase": str((venta or {}).get("clase") or "digital"),
                    "estado": "CANCELADA" if canc else est,
                    "cancelado": canc,
                }
            _guardar(datos)
        if avisar:
            try:
                from src.motor_auditoria_digital.empleado import despertar

                despertar()
            except Exception:
                pass
    except Exception:
        pass


def marcar_cancelado(ticket: str, avisar: bool = True):
    """Marca un ticket como CANCELADA en el libro local."""
    ticket = str(ticket or "").strip()
    if not ticket:
        return
    try:
        with _LOCK:
            datos = _leer()
            if ticket in datos and isinstance(datos[ticket], dict):
                datos[ticket]["estado"] = "CANCELADA"
                datos[ticket]["cancelado"] = True
                _guardar(datos)
            else:
                datos[ticket] = {
                    "ticket": ticket,
                    "fecha": "",
                    "monto": 0.0,
                    "metodo": "",
                    "clase": "digital",
                    "estado": "CANCELADA",
                    "cancelado": True,
                }
                _guardar(datos)
        if avisar:
            try:
                from src.motor_auditoria_digital.empleado import despertar

                despertar()
            except Exception:
                pass
    except Exception:
        pass


def listar(desde, hasta, clases=("digital",)):
    from src.motor_auditoria_digital.consultas.rango import en_rango

    salida = []
    try:
        with _LOCK:
            datos = _leer()
        for venta in datos.values():
            if not isinstance(venta, dict):
                continue
            if str(venta.get("clase") or "digital") not in clases:
                continue
            if not en_rango(venta.get("fecha") or "", desde, hasta):
                continue
            salida.append(dict(venta))
        salida.sort(key=lambda r: r.get("fecha") or "", reverse=True)
    except Exception:
        return []
    return salida
