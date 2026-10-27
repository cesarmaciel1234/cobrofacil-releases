"""El lanzador despierta el servidor. El proceso lee si es maestra o esclava."""

from __future__ import annotations


def asegurar_servidor() -> None:
    from src.config import config
    from src.central_red_global.servidor import (
        ensure_store_server_process,
        is_store_server_online,
    )
    from src.central_red_global.servidor.oficio.agente import oficio, rearmar_arranque
    from src.updater.silent_auto_updater import end_apply_guard

    if not config.get("auto_start_store_server", True):
        if oficio() != "esclava" or config.get("agente_esclava_ofrecido"):
            return
        config.set("auto_start_store_server", True)
        config.set("agente_esclava_ofrecido", True)
        rearmar_arranque()
    if is_store_server_online():
        return
    end_apply_guard()
    ensure_store_server_process(timeout_sec=40.0)


def asegurar_servidor_si_maestra() -> None:
    asegurar_servidor()
