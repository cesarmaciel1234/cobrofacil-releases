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


def _servicio_windows_estado() -> dict:
    try:
        from src.central_red_global.servidor.servicio_windows.gestor import estado_servicio_windows

        return estado_servicio_windows()
    except Exception:
        return {"instalado": False, "en_ejecucion": False, "pid": None}


def pintar_badge(lbl: QLabel) -> None:
    if getattr(lbl, "_starting_async", False):
        return
    from src.central_red_global.master_presence import es_pc_maestra_local
    from src.central_red_global.servidor import is_store_server_online
    from src.utils.candados import get_store_server_pid

    online = is_store_server_online()
    pid = get_store_server_pid()
    svc_up = bool(_servicio_windows_estado().get("en_ejecucion"))
    if not es_pc_maestra_local():
        from src.utils.candados import is_store_server_running

        vivo = is_store_server_running() and online
        lbl.setText(("Espejo: activo · Svc" if svc_up else "Espejo: activo") if vivo else "Espejo: apagado")
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
        pref = "Servidor: Svc" if svc_up else "Servidor: ONLINE"
        lbl.setText(pref + (f" · {pid}" if pid else ""))
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
                try:
                    sig.refreshed.emit()
                except RuntimeError:
                    pass

    threading.Thread(target=_worker, name="badge-start-server", daemon=True).start()


def _mostrar_monitor_servicio(parent, lbl: QLabel, est: dict, es_maestra: bool) -> None:
    import os
    from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel as QLbl, QPushButton, QTextEdit, QVBoxLayout
    from src.utils.paths import get_base_path
    from src.utils.qt_compat import qt_exec

    dlg = QDialog(parent)
    dlg.setWindowTitle("Cobro Fácil — Servicio Windows (Session 0)")
    dlg.setMinimumSize(620, 380)
    lay = QVBoxLayout(dlg)

    rol_txt = "Maestra (MariaDB + LAN)" if es_maestra else "Esclava (Espejo continuo)"
    hdr = QLbl(f"Servicio: CobroFacil_ServidorTienda  ·  PID {est.get('pid') or '-'}  ·  {rol_txt}")
    hdr.setStyleSheet("font-weight: 800; font-size: 12px; color: #0F172A;")
    lay.addWidget(hdr)

    log_path = os.path.join(get_base_path(), "logs", "servidor_fondo.log")
    txt = QTextEdit()
    txt.setReadOnly(True)
    txt.setStyleSheet("font-family: Consolas; font-size: 11px; background: #0F172A; color: #E2E8F0;")
    try:
        if os.path.isfile(log_path):
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()[-35:]
            txt.setPlainText("".join(lines) or "(sin registros recientes)")
        else:
            txt.setPlainText("(log aún no generado)")
    except OSError as e:
        txt.setPlainText(f"No se pudo leer el log: {e}")
    lay.addWidget(txt)

    btns = QHBoxLayout()
    btn_close = QPushButton("Cerrar")
    btn_close.clicked.connect(dlg.accept)
    btns.addStretch()
    btns.addWidget(btn_close)
    lay.addLayout(btns)

    qt_exec(dlg)
    pintar_badge(lbl)


def al_clic_badge(parent, lbl: QLabel) -> None:
    from src.central_red_global.master_presence import es_pc_maestra_local
    from src.central_red_global.servidor import is_store_server_online
    from src.utils.candados import focus_existing_store_server

    es_maestra = es_pc_maestra_local()
    est_svc = _servicio_windows_estado()

    if not es_maestra:
        from src.utils.candados import is_store_server_running

        if is_store_server_running() and is_store_server_online():
            if est_svc.get("en_ejecucion"):
                _mostrar_monitor_servicio(parent, lbl, est_svc, False)
            else:
                focus_existing_store_server()
                pintar_badge(lbl)
        else:
            lbl.setText("Espejo: arrancando…")
            _launch_server_async(lbl)
        return

    if is_store_server_online():
        if est_svc.get("en_ejecucion"):
            _mostrar_monitor_servicio(parent, lbl, est_svc, True)
        else:
            focus_existing_store_server()
            pintar_badge(lbl)
    else:
        lbl.setText("Servidor: arrancando…")
        _launch_server_async(lbl)
