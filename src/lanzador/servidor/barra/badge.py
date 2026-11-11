"""Pastilla ONLINE / ESCLAVA / OFFLINE (con arranque asíncrono al hacer clic)."""

from __future__ import annotations

import threading

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel


class _BadgeSignal(QObject):
    refreshed = pyqtSignal()


def crear_badge(parent, on_click):
    lbl = QLabel("Servidor: …")
    lbl.setStyleSheet(
        "font-size: 10px; font-weight: 800; color: #64748B; background: #F1F5F9; "
        "border: 1px solid #E2E8F0; border-radius: 8px; padding: 4px 10px;"
    )
    lbl.setCursor(Qt.PointingHandCursor)
    lbl.setToolTip("Clic: mostrar / asegurar Servidor de Tienda")
    sig = _BadgeSignal(lbl)
    sig.refreshed.connect(lambda: pintar_badge(lbl))
    lbl._badge_signal = sig
    lbl._starting_async = False
    lbl.mousePressEvent = lambda e: on_click()
    return lbl


def pintar_badge(lbl: QLabel) -> None:
    if getattr(lbl, "_starting_async", False):
        return
    from src.central_red_global.master_presence import es_pc_maestra_local
    from src.central_red_global.servidor import is_store_server_online
    from src.utils.candados import get_store_server_pid

    online = is_store_server_online()
    pid = get_store_server_pid()
    if not es_pc_maestra_local():
        from src.utils.candados import is_store_server_running

        vivo = is_store_server_running() and online
        lbl.setText("Espejo: activo" if vivo else "Espejo: apagado")
        lbl.setStyleSheet(
            "font-size: 10px; font-weight: 800; color: #1E3A8A; background: #DBEAFE; "
            "border: 1px solid #93C5FD; border-radius: 8px; padding: 4px 10px;"
            if vivo
            else "font-size: 10px; font-weight: 800; color: #9A3412; background: #FFEDD5; "
            "border: 1px solid #FDBA74; border-radius: 8px; padding: 4px 10px;"
        )
        lbl.setToolTip(
            "Esta PC es esclava. El servidor mantiene el espejo y no abre MariaDB."
        )
        return
    if online:
        lbl.setText("Servidor: ONLINE" + (f" · {pid}" if pid else ""))
        lbl.setStyleSheet(
            "font-size: 10px; font-weight: 800; color: #15803D; background: #DCFCE7; "
            "border: 1px solid #86EFAC; border-radius: 8px; padding: 4px 10px;"
        )
    else:
        lbl.setText("Servidor: OFFLINE")
        lbl.setStyleSheet(
            "font-size: 10px; font-weight: 800; color: #B91C1C; background: #FEE2E2; "
            "border: 1px solid #FECACA; border-radius: 8px; padding: 4px 10px;"
        )


def _launch_server_async(lbl: QLabel) -> None:
    if getattr(lbl, "_starting_async", False):
        return
    lbl._starting_async = True

    def _worker():
        try:
            from src.central_red_global.servidor import ensure_store_server_process
            from src.lanzador.servidor.pulso import reset_watchdog_backoff
            from src.updater.silent_auto_updater import end_apply_guard

            reset_watchdog_backoff()
            end_apply_guard()
            ensure_store_server_process(timeout_sec=40.0)
        finally:
            lbl._starting_async = False
            sig = getattr(lbl, "_badge_signal", None)
            if sig is not None:
                sig.refreshed.emit()

    threading.Thread(target=_worker, name="badge-start-server", daemon=True).start()


def al_clic_badge(parent, lbl: QLabel) -> None:
    from src.central_red_global.master_presence import es_pc_maestra_local
    from src.central_red_global.servidor import is_store_server_online
    from src.utils.candados import focus_existing_store_server

    if not es_pc_maestra_local():
        from src.utils.candados import is_store_server_running

        if is_store_server_running() and is_store_server_online():
            focus_existing_store_server()
            pintar_badge(lbl)
        else:
            lbl.setText("Espejo: arrancando…")
            _launch_server_async(lbl)
        return

    if is_store_server_online():
        focus_existing_store_server()
        pintar_badge(lbl)
    else:
        lbl.setText("Servidor: arrancando…")
        _launch_server_async(lbl)
