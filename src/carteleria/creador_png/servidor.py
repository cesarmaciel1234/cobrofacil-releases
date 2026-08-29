"""Servidor local HTML del Creador PNG."""

from __future__ import annotations

import json
import socket
import threading
import time
import urllib.request

PUERTOS = (5000, 5055, 5056, 5057)
_puerto = PUERTOS[0]
_started = False
_lock = threading.Lock()
_error = ""


def url_base() -> str:
    return f"http://127.0.0.1:{_puerto}"


def _es_nuestro(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=0.4) as res:
            if res.status != 200:
                return False
            data = json.loads(res.read().decode())
            return data.get("app") == "creador_png"
    except Exception:
        return False


def _puerto_libre(port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def _run(port: int):
    global _error
    try:
        from src.carteleria.creador_png.app import app
        app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False, threaded=True)
    except Exception as exc:
        _error = str(exc)


def asegurar_servidor() -> str:
    global _started, _error, _puerto
    for port in PUERTOS:
        if _es_nuestro(port):
            _puerto = port
            return url_base()
    with _lock:
        for port in PUERTOS:
            if _es_nuestro(port):
                _puerto = port
                return url_base()
        if not _started:
            elegido = next((p for p in PUERTOS if _puerto_libre(p)), None)
            if elegido is None:
                raise RuntimeError("No hay puerto libre para el Creador PNG.")
            _error = ""
            _puerto = elegido
            threading.Thread(target=_run, args=(elegido,), daemon=True).start()
            _started = True
        for _ in range(60):
            if _es_nuestro(_puerto):
                return url_base()
            if _error:
                break
            time.sleep(0.1)
        _started = False
    raise RuntimeError(
        "No se pudo iniciar el Creador PNG.\n"
        f"({_error or 'timeout al levantar el servidor'})"
    )
