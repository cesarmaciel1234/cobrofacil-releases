"""Si la maestra está encendida y qué PCs están en la red.

Escucha el mismo aviso UDP que Nexus (puerto 37021) con el puerto compartido.
No abre MariaDB. El puerto 3306 solo se toca para ver si contesta.
"""

from __future__ import annotations

import json
import socket
import threading
import time

_PUERTO = 37021
_VENCE = 45.0
_candado = threading.Lock()
_pares: dict[str, tuple[str, str, float]] = {}
_prendido = False


def arrancar() -> None:
    """Un hilo escucha y otro avisa el nombre de esta PC. Se llama una sola vez."""
    global _prendido
    with _candado:
        if _prendido:
            return
        _prendido = True
    threading.Thread(target=_oir, name="presencia-oir", daemon=True).start()
    threading.Thread(target=_latir, name="presencia-latir", daemon=True).start()


def foto() -> dict:
    """La lee el hilo de la ventana. No toca Qt."""
    try:
        en_linea, destino, es_maestra = _maestra()
        return {
            "en_linea": en_linea,
            "destino": destino,
            "es_maestra": es_maestra,
            "pcs": _otras(),
        }
    except Exception:
        return {"en_linea": False, "destino": "", "es_maestra": False, "pcs": []}


def _maestra() -> tuple[bool, str, bool]:
    from src.central_red_global.master_presence import es_pc_maestra_local

    if es_pc_maestra_local():
        return _puerto_abierto("127.0.0.1"), socket.gethostname(), True
    from src.config import config

    host = str(config.get("db_host", "") or "").strip()
    if not host or host.lower() in ("localhost", "127.0.0.1"):
        return False, host, False
    return _puerto_abierto(host), host, False


def _puerto_abierto(host: str) -> bool:
    sonda = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sonda.settimeout(0.5)
    try:
        return sonda.connect_ex((host, 3306)) == 0
    except Exception:
        return False
    finally:
        sonda.close()


def nombres() -> list[tuple[str, str]]:
    """Nombre y rol de las otras PCs. Esta máquina no entra."""
    propio = socket.gethostname().strip().lower()
    ahora = time.time()
    with _candado:
        vivos = [
            (origen, visto)
            for origen, (_ip, _rol, visto) in _pares.items()
            if ahora - visto <= _VENCE
        ]
    salida: list[tuple[str, str]] = []
    vistos: set[str] = set()
    for origen, _visto in vivos:
        partes = str(origen).split("|")
        nombre = (partes[0] if partes else origen).strip()
        if not nombre or nombre.lower() == propio or nombre.lower() in vistos:
            continue
        vistos.add(nombre.lower())
        rol = partes[1].strip() if len(partes) > 1 else ""
        salida.append((nombre, rol))
    return salida


def _otras() -> list[tuple[str, str]]:
    """Nombre de PC y rol, para la pastilla. Esta máquina no entra en la lista."""
    return [
        (f"{nombre} ({rol})" if rol else nombre, "")
        for nombre, rol in nombres()
    ]


def _anotar(origen: str, ip: str) -> None:
    if not origen:
        return
    with _candado:
        rol = origen.split("|")[1] if "|" in origen else ""
        _pares[origen] = (ip, rol, time.time())


def _oir() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", _PUERTO))
        sock.settimeout(1.0)
    except Exception:
        sock.close()
        return
    try:
        while True:
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                continue
            except Exception:
                continue
            try:
                payload = json.loads(data.decode("utf-8"))
            except Exception:
                continue
            origen = str(payload.get("origen") or "")
            _anotar(origen, addr[0] if addr else "")
            tipo = str(payload.get("tipo") or "")
            datos = payload.get("datos") if isinstance(payload.get("datos"), dict) else {}
            if tipo == "CONFIRMAR":
                try:
                    from src.central_red_global.servidor.pareja.acuse import responder

                    responder(addr, (datos or {}).get("ids") or [])
                except Exception:
                    pass
            elif tipo == "ESPEJO_LISTO":
                try:
                    from src.base_de_datos.offline_sync import offline_sync_manager

                    offline_sync_manager.soltar_confirmados((datos or {}).get("ids") or [])
                except Exception:
                    pass
            elif tipo in ("DATOS", "PRECIOS_ACTUALIZADOS"):
                datos = payload.get("datos") if isinstance(payload.get("datos"), dict) else {}
                _seguir_titular(str((datos or {}).get("server_ip") or ""))
                _pedir_copia()
    finally:
        sock.close()


def _pedir_copia() -> None:
    """Solo la esclava baja la copia. No reescribe la grilla de la tienda."""
    try:
        from src.central_red_global.master_presence import es_pc_maestra_local

        if es_pc_maestra_local():
            return
        from src.central_red_global.servidor.oficio.agente import pedir_reparto

        pedir_reparto()
    except Exception:
        pass


def _seguir_titular(ip: str) -> None:
    """La titular dijo su IP de ahora. Si cambió, esta esclava la sigue."""
    if not ip:
        return
    try:
        from src.central_red_global.servidor.pareja.buscar import adoptar

        adoptar(ip)
    except Exception:
        pass


def _latir() -> None:
    while True:
        try:
            from src.central_red_global.servidor.pareja.reserva import rol_latido

            rol = rol_latido()
        except Exception:
            from src.central_red_global.master_presence import es_pc_maestra_local

            rol = "maestra" if es_pc_maestra_local() else "esclava"
        origen = f"{socket.gethostname()}|{rol}|servidor"
        payload = json.dumps(
            {"origen": origen, "tipo": "HEARTBEAT", "datos": {"role": rol}, "ts": time.time()},
            ensure_ascii=False,
        ).encode("utf-8")
        try:
            saliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            saliente.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            saliente.sendto(payload, ("255.255.255.255", _PUERTO))
            saliente.close()
        except Exception:
            pass
        time.sleep(10)
