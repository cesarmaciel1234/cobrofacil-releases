"""El lanzador despierta el servidor si esta PC es maestra."""

from __future__ import annotations


def asegurar_servidor_si_maestra() -> None:
    from src.config import config
    from src.central_red_global.master_presence import es_pc_maestra_local
    from src.central_red_global.servidor import (
        ensure_store_server_process,
        is_store_server_online,
    )
    from src.updater.silent_auto_updater import end_apply_guard

    if not config.get("auto_start_store_server", True):
        return
    if not es_pc_maestra_local():
        return
    if is_store_server_online():
        return
    end_apply_guard()
    ensure_store_server_process(timeout_sec=40.0)
