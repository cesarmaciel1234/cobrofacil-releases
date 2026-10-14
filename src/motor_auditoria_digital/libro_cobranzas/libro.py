"""Libro de cobranzas digitales (F6). La venta puede ser de otro mes; el cobro cuenta este mes."""

import json
import os
import threading

from src.utils.paths import get_base_path

RUTA = os.path.join(get_base_path(), "reportes", "cobranzas_digitales.json")
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
    if not filas:
        return
    try:
        with _LOCK:
            datos = _leer()
            for fila in filas:
                clave = str((fila or {}).get("id") or "").strip()
                if not clave:
                    continue
                from src.motor_auditoria_digital.consultas.ids import ticket_cobro

                datos[clave] = {
                    "id": clave,
                    "ticket_cobro": str((fila or {}).get("ticket_cobro") or ticket_cobro(clave)),
                    "fecha": str((fila or {}).get("fecha") or "")[:19],
                    "monto": float((fila or {}).get("monto") or 0),
                    "nombre": str((fila or {}).get("nombre") or "Cliente"),
                    "metodo": str((fila or {}).get("metodo") or ""),
                    "pago_id": str((fila or {}).get("pago_id") or ""),
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


def listar(desde, hasta):
    from src.motor_auditoria_digital.consultas.rango import en_rango

    salida = []
    try:
        with _LOCK:
            datos = _leer()
        for fila in datos.values():
            if not isinstance(fila, dict):
                continue
            if not en_rango(fila.get("fecha") or "", desde, hasta):
                continue
            salida.append(dict(fila))
        salida.sort(key=lambda r: r.get("fecha") or "", reverse=True)
    except Exception:
        return []
    return salida
