"""Hilo de auditoría. Si se cae, el cobro y Mercado Pago siguen."""

from __future__ import annotations

import threading
import time

_lock = threading.Lock()
_pedir = threading.Event()
_estado = {"arrancado": False, "cache": [], "clave": None}


def snapshot(desde, hasta, forzar=False):
    """Copia en memoria. Si el hilo todavía no armó, arma una vez y no tumba la UI."""
    clave = (desde, hasta)
    with _lock:
        if not forzar and _estado["clave"] == clave and _estado["cache"]:
            return list(_estado["cache"])
    try:
        from src.motor_auditoria_digital.cruces.snapshot import armar

        filas = armar(desde, hasta)
    except Exception:
        filas = []
    with _lock:
        _estado["cache"] = filas
        _estado["clave"] = clave
    _pedir.set()
    return list(filas)


def _jornada():
    time.sleep(8)
    while True:
        try:
            from src.motor_auditoria_digital.consultas.tickets import volcar
            from src.motor_auditoria_digital.consultas.cobranzas import volcar as volcar_cob

            volcar()
            volcar_cob()
        except Exception:
            pass
        _pedir.wait(45)
        _pedir.clear()
        with _lock:
            clave = _estado["clave"]
        if not clave:
            continue
        try:
            from src.motor_auditoria_digital.cruces.snapshot import armar

            filas = armar(clave[0], clave[1])
        except Exception:
            continue
        with _lock:
            _estado["cache"] = filas
            _estado["clave"] = clave


def despertar():
    with _lock:
        _estado["cache"] = []
        _estado["clave"] = None
    _pedir.set()


def arrancar():
    with _lock:
        if _estado["arrancado"]:
            return
        _estado["arrancado"] = True
    threading.Thread(target=_jornada, daemon=True, name="auditoria_digital").start()
