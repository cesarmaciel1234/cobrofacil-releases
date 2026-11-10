"""El lanzador despierta el servidor. El proceso lee si es maestra o esclava."""

from __future__ import annotations


def asegurar_servidor() -> None:
    from src.config import config
    from src.central_red_global.servidor import (
        ensure_store_server_process,
        is_store_server_online,
        is_os_autostart_enabled,
        set_os_autostart,
    )
    from src.central_red_global.servidor.oficio.agente import oficio, rearmar_arranque
    from src.updater.silent_auto_updater import end_apply_guard

    # 1. Asegurar arranque automático con Windows en segundo plano
    if config.get("auto_start_store_server", True):
        if not is_os_autostart_enabled():
            set_os_autostart(True)

    # 2. Si el servidor no está en ejecución / online, revivirlo inmediatamente
    if is_store_server_online():
        return
    end_apply_guard()
    ensure_store_server_process(timeout_sec=40.0)


def asegurar_servidor_si_maestra() -> None:
    asegurar_servidor()
