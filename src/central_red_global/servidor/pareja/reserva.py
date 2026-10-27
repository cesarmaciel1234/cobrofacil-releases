"""La segunda maestra. Una esclava guarda el espejo y contesta en la red. No abre MariaDB."""

from __future__ import annotations

import json
import logging
import socket
import threading
import time

logger = logging.getLogger("oficio_servidor")

_hilo: threading.Thread | None = None
_anuncio: threading.Thread | None = None
_avisado = False


def _pares() -> list[tuple[str, str]]:
    from src.central_red_global.servidor.ventana.presencia import nombres

    return nombres()


def candidatas() -> list[str]:
    """Esta PC y las esclavas que laten. La titular no entra."""
    nombres = [nombre for nombre, rol in _pares() if rol in ("", "esclava", "reserva")]
    propio = socket.gethostname().strip()
    if propio and propio not in nombres:
        try:
            from src.central_red_global.master_presence import es_pc_maestra_local

            if not es_pc_maestra_local():
                nombres.append(propio)
        except Exception:
            nombres.append(propio)
    return nombres


def elegida() -> str:
    """Con varias esclavas, la de nombre más bajo queda de reserva. Si no hay, no se inventa otra."""
    nombres = [n for n in candidatas() if n]
    if not nombres:
        return ""
    return sorted(nombres, key=str.lower)[0]


def soy() -> bool:
    try:
        from src.central_red_global.master_presence import es_pc_maestra_local

        if es_pc_maestra_local():
            return False
    except Exception:
        return False
    return elegida().lower() == socket.gethostname().strip().lower()


def rol_latido() -> str:
    try:
        from src.central_red_global.master_presence import es_pc_maestra_local

        if es_pc_maestra_local():
            return "maestra"
    except Exception:
        pass
    return "reserva" if soy() else "esclava"


def _ip_propia() -> str:
    try:
        sonda = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sonda.connect(("8.8.8.8", 80))
        ip = sonda.getsockname()[0]
        sonda.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return ""


def _titular() -> str:
    try:
        from src.config import config

        return str(config.get("db_host", "") or "").strip()
    except Exception:
        return ""


def _contestar() -> None:
    """Responde el descubrimiento. La titular sigue siendo la que tiene MariaDB."""
    from src.central_red_global.servidor.pareja.buscar import PUERTO

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", PUERTO))
        sock.settimeout(1.0)
    except Exception as e:
        logger.warning("pareja  la reserva no pudo oir el descubrimiento: %s", e)
        sock.close()
        return
    try:
        while True:
            try:
                data, addr = sock.recvfrom(2048)
            except socket.timeout:
                continue
            except Exception:
                continue
            if data != b"PUNPRO_DISCOVER" or not soy():
                continue
            aviso = {
                "hostname": socket.gethostname(),
                "server_ip": _ip_propia(),
                "titular_ip": _titular(),
                "mode": "MAESTRA",
                "reserva": True,
                "db_engine": "espejo",
                "servicio": "tienda",
            }
            try:
                sock.sendto(json.dumps(aviso).encode("utf-8"), addr)
            except Exception:
                pass
    finally:
        sock.close()


def prender() -> None:
    """La esclava elegida empieza a contestar. La titular no entra acá."""
    global _hilo, _anuncio, _avisado
    if _anuncio is None or not _anuncio.is_alive():
        _anuncio = threading.Thread(target=_contestar, name="pareja-reserva", daemon=True)
        _anuncio.start()

    def _vuelta() -> None:
        global _avisado
        time.sleep(25)
        while True:
            try:
                if soy() and not _avisado:
                    logger.info("pareja  esta pc es la reserva")
                    _avisado = True
                if not soy():
                    _avisado = False
                from src.central_red_global.servidor.pareja.promover import vigilar

                vigilar()
            except Exception as e:
                logger.warning("pareja  no se pudo elegir reserva: %s", e)
            time.sleep(20)

    if _hilo is None or not _hilo.is_alive():
        _hilo = threading.Thread(target=_vuelta, name="oficio-pareja", daemon=True)
        _hilo.start()
