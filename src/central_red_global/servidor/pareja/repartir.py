"""La titular empuja el espejo. Las esclavas lo bajan; ella no espera a que pregunten."""

from __future__ import annotations

import logging
import socket
import threading
import time

logger = logging.getLogger("oficio_servidor")

_hilo: threading.Thread | None = None


def _ip_propia() -> str:
    try:
        sonda = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sonda.connect(("8.8.8.8", 80))
        ip = sonda.getsockname()[0]
        sonda.close()
        return ip
    except Exception:
        return ""


def prender() -> None:
    """Cada minuto la titular avisa su IP y que hay espejo nuevo. Solo en la maestra."""
    global _hilo
    if _hilo is not None and _hilo.is_alive():
        return

    def _vuelta() -> None:
        time.sleep(30)
        while True:
            try:
                from src.central_red_global.master_presence import es_pc_maestra_local

                if not es_pc_maestra_local():
                    time.sleep(60)
                    continue
                from src.central_red_global.sync_tienda.aviso_tv.avisar import repartir_desde_maestra

                repartir_desde_maestra(_ip_propia())
            except Exception as e:
                logger.warning("pareja  no se pudo repartir el espejo: %s", e)
            time.sleep(60)

    _hilo = threading.Thread(target=_vuelta, name="oficio-reparto", daemon=True)
    _hilo.start()
    logger.info("pareja  la titular reparte el espejo")
