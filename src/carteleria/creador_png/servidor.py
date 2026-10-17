"""Servidor local HTML del Creador PNG."""

from __future__ import annotations

import json
import logging
import socket
import threading
import time
import urllib.request

PUERTOS = (5000, 5055, 5056, 5057)
_HOST = "127.0.0.1"
_puerto = PUERTOS[0]
_started = False
_lock = threading.Lock()
_error = ""
_httpd = None


def url_base() -> str:
    return f"http://{_HOST}:{_puerto}"


def _es_nuestro(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://{_HOST}:{port}/api/ping", timeout=0.4) as res:
            if res.status != 200:
                return False
            data = json.loads(res.read().decode())
            return data.get("app") == "creador_png"
    except Exception:
        return False


def _puerto_libre(port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((_HOST, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def _run(port: int):
    global _error, _httpd
    try:
        logging.getLogger("werkzeug").setLevel(logging.ERROR)
        from src.carteleria.creador_png.app import app
        from werkzeug.serving import make_server

        _httpd = make_server(_HOST, port, app, threaded=True)
        _httpd.serve_forever()
    except OSError as exc:
        # 233: tubería rota (exe / Cursor sin consola). Si el ping ya responde, no es fallo.
        if getattr(exc, "winerror", None) == 233 or exc.errno == 233:
            if _es_nuestro(port):
                return
        _error = str(exc)
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
            threading.Thread(target=_run, args=(elegido,), name="creador-png", daemon=True).start()
            _started = True
        for _ in range(80):
            if _es_nuestro(_puerto):
                return url_base()
            if _error:
                break
            time.sleep(0.1)
        fallo = _error or "timeout al levantar el servidor"
        _started = False
    raise RuntimeError(
        "No se pudo iniciar el Creador PNG.\n"
        f"({fallo})"
    )
