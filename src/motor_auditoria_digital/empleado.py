"""Hilo de auditoría. Si se cae, el cobro y Mercado Pago siguen."""

from __future__ import annotations

import threading

_lock = threading.Lock()
_pedir = threading.Event()
_estado = {"arrancado": False, "cache": [], "clave": None, "pedido": None, "listo": False, "gen": 0}


def generacion():
    with _lock:
        return int(_estado.get("gen") or 0)


def snapshot(desde, hasta, forzar=False):
    """Cruce listo. Si no está, lo arma en quien llama. La pantalla usa pedir()."""
    clave = (desde, hasta)
    with _lock:
        if not forzar and _estado.get("clave") == clave and _estado.get("listo") and _estado["cache"]:
            return list(_estado["cache"])
    try:
        from src.motor_auditoria_digital.cruces.snapshot import armar

        filas = armar(desde, hasta) or []
    except Exception:
        filas = []
    with _lock:
        _estado["cache"] = filas
        _estado["clave"] = clave
        _estado["pedido"] = clave
        _estado["listo"] = True
        _estado["gen"] = int(_estado.get("gen") or 0) + 1
    return list(filas)


def pedir(desde, hasta, forzar=False):
    """No arma en la ventana. Devuelve la copia de ese período, o vacía si todavía no está."""
    clave = (desde, hasta)
    with _lock:
        if not forzar and _estado.get("clave") == clave and _estado.get("listo"):
            return list(_estado["cache"])
        previa = list(_estado["cache"]) if _estado.get("clave") == clave else []
        _estado["pedido"] = clave
    _pedir.set()
    arrancar()
    return previa


def _publicar(clave):
    try:
        from src.motor_auditoria_digital.cruces.snapshot import armar

        filas = armar(clave[0], clave[1]) or []
    except Exception:
        filas = []
    with _lock:
        if _estado.get("pedido") != clave:
            return
        _estado["cache"] = filas
        _estado["clave"] = clave
        _estado["listo"] = True
        _estado["gen"] = int(_estado.get("gen") or 0) + 1


def _volcar_libros():
    try:
        from src.motor_auditoria_digital.consultas.tickets import volcar
        from src.motor_auditoria_digital.consultas.cobranzas import volcar as volcar_cob

        volcar()
        volcar_cob()
    except Exception:
        pass


def _jornada():
    while True:
        llego = _pedir.wait(45)
        if not llego:
            _volcar_libros()
            with _lock:
                clave = _estado.get("clave")
                if clave and _estado.get("listo"):
                    _estado["pedido"] = clave
                    _estado["listo"] = False
            if clave:
                _publicar(clave)
            continue
        while True:
            _pedir.clear()
            with _lock:
                clave = _estado.get("pedido")
            if not clave:
                break
            _publicar(clave)
            if not _pedir.is_set():
                break


def despertar():
    with _lock:
        clave = _estado.get("clave") or _estado.get("pedido")
        _estado["listo"] = False
        if clave:
            _estado["pedido"] = clave
    _pedir.set()


def arrancar():
    with _lock:
        if _estado["arrancado"]:
            return
        _estado["arrancado"] = True
    threading.Thread(target=_jornada, daemon=True, name="auditoria_digital").start()
