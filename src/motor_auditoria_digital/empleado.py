"""Hilo de auditoría. Si se cae, el cobro y Mercado Pago siguen."""

from __future__ import annotations

import threading
import time

_arrancado = False
_cache = []
_clave = None
_lock = threading.Lock()
_pedir = threading.Event()


def snapshot(desde, hasta, forzar=False):
    """Copia en memoria. Si el hilo todavía no armó, arma una vez y no tumba la UI."""
    global _cache, _clave
    clave = (desde, hasta)
    with _lock:
        if not forzar and _clave == clave and _cache:
            return list(_cache)
    try:
        from src.motor_auditoria_digital.cruces.snapshot import armar

        filas = armar(desde, hasta)
    except Exception:
        filas = []
    with _lock:
        _cache = filas
        _clave = clave
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
            clave = _clave
        if not clave:
            continue
        try:
            from src.motor_auditoria_digital.cruces.snapshot import armar

            filas = armar(clave[0], clave[1])
        except Exception:
            continue
        with _lock:
            _cache = filas
            _clave = clave


def despertar():
    global _cache, _clave
    with _lock:
        _cache = []
        _clave = None
    _pedir.set()


def arrancar():
    global _arrancado
    if _arrancado:
        return
    _arrancado = True
    threading.Thread(target=_jornada, daemon=True, name="auditoria_digital").start()
