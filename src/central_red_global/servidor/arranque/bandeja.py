"""Ventana + bandeja del proceso `--server` (con escritorio)."""

from __future__ import annotations

import os

from src.logger import logger
from src.central_red_global.servidor.arranque.servicios import encender_servicios_tienda
from src.central_red_global.servidor.puerto import mariadb_port_open, needs_mariadb
from src.utils.candados import (
    STORE_SERVER_WINDOW_TITLE,
    acquire_store_server_lock,
    focus_existing_store_server,
    get_store_server_pid,
    release_store_server_lock,
)


def run_store_server_app(app) -> int:
    from PyQt6.QtCore import QTimer, Qt
    from PyQt6.QtGui import QAction, QIcon
    from PyQt6.QtWidgets import (
        QApplication,
        QHBoxLayout,
        QLabel,
        QMenu,
        QMessageBox,
        QPushButton,
        QSystemTrayIcon,
        QVBoxLayout,
        QWidget,
    )

    from src.utils.qt_compat import qt_exec
    from src.utils.paths import get_resource_path

    if not acquire_store_server_lock():
        focus_existing_store_server()
        logger.info("Ya hay un Servidor de Tienda activo.")
        return 0

    encender_servicios_tienda(arrancar_mysqld=False)

    win = QWidget()
    win.setWindowTitle(STORE_SERVER_WINDOW_TITLE)
    win.setFixedSize(420, 220)
    win.setWindowFlags(
        Qt.WindowType.Window
        | Qt.WindowType.WindowMinimizeButtonHint
        | Qt.WindowType.WindowCloseButtonHint
    )

    lay = QVBoxLayout(win)
    lay.setContentsMargins(24, 20, 24, 20)
    lay.setSpacing(12)

    title = QLabel("Servidor de Tienda")
    title.setStyleSheet("font-size: 20px; font-weight: 900; color: #0F172A;")
    lay.addWidget(title)

    status = QLabel("Iniciando…")
    status.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")
    status.setWordWrap(True)
    lay.addWidget(status)

    detail = QLabel("MariaDB · API :8000 · Discovery UDP :37020 · Presencia maestra")
    detail.setStyleSheet("font-size: 11px; color: #64748B;")
    detail.setWordWrap(True)
    lay.addWidget(detail)

    row = QHBoxLayout()
    btn_hide = QPushButton("Ocultar en bandeja")
    btn_hide.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_stop = QPushButton("Apagar servidor")
    btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_stop.setStyleSheet(
        "QPushButton { background: #FEE2E2; color: #B91C1C; font-weight: 700; "
        "padding: 8px 12px; border-radius: 8px; border: 1px solid #FECACA; }"
    )
    row.addWidget(btn_hide)
    row.addWidget(btn_stop)
    lay.addLayout(row)

    tray = None
    icon_path = get_resource_path(os.path.join("src", "assets", "pos_icon.png"))
    app_icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

    if QSystemTrayIcon.isSystemTrayAvailable():
        tray = QSystemTrayIcon(app_icon, win)
        menu = QMenu()
        act_show = QAction("Mostrar servidor", win)
        act_show.triggered.connect(win.showNormal)
        act_quit = QAction("Apagar servidor de tienda", win)
        menu.addAction(act_show)
        menu.addSeparator()
        menu.addAction(act_quit)
        tray.setContextMenu(menu)
        tray.setToolTip("Cobro Fácil — Servidor de Tienda")
        tray.show()

        def _on_tray(reason):
            if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
                win.showNormal()
                win.raise_()

        tray.activated.connect(_on_tray)
        win._tray_quit_action = act_quit
    else:
        win.show()
        win._tray_quit_action = None

    def _refresh_status():
        online = mariadb_port_open() if needs_mariadb() else True
        pid = get_store_server_pid() or os.getpid()
        if online:
            status.setText(f"ONLINE — PID {pid}\nLa tienda es visible en la red (sin cajero).")
            status.setStyleSheet("font-size: 13px; font-weight: 700; color: #15803D;")
        else:
            status.setText(f"DEGRADADO — PID {pid}\nMariaDB no responde; reintentando…")
            status.setStyleSheet("font-size: 13px; font-weight: 700; color: #C2410C;")

    def _watchdog():
        if needs_mariadb() and not mariadb_port_open():
            logger.warning("Watchdog Servidor: MariaDB caída — reintentando start_server()")
            try:
                from src.services.mariadb_controller import mariadb_controller

                mariadb_controller.start_server()
            except Exception as e:
                logger.error(f"Watchdog MariaDB: {e}")
        try:
            from src.central_red_global.master_presence import ensure_master_lan_presence

            ensure_master_lan_presence()
        except Exception:
            pass
        _refresh_status()

    def _shutdown_store():
        resp = QMessageBox.question(
            win,
            "Apagar servidor de tienda",
            "¿Apagar el Servidor de Tienda?\n\n"
            "Se desconectarán las cajas y la cartelería de esta maestra.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return
        try:
            from src.cerebro_global.backup_cerebro.motor_backup import cerebro_backup as _cb

            try:
                _cb.tick_now(force_full=True)
            except Exception:
                pass
            try:
                _cb.stop()
            except Exception:
                pass
        except Exception:
            pass
        try:
            from src.ui_components.backup_flash import mostrar_flash_backup_dia

            mostrar_flash_backup_dia(win, "mariadb", "127.0.0.1")
        except Exception:
            try:
                from src.base_de_datos.autoblindaje_db import AutoBlindajeDB

                AutoBlindajeDB.finalizar_backup_del_dia("mariadb", "127.0.0.1")
            except Exception as e_bk:
                logger.warning(f"Backup al apagar servidor: {e_bk}")
        try:
            from src.central_red_global.network_engine import shutdown_network_engine

            shutdown_network_engine()
        except Exception:
            pass
        try:
            from src.central_red_global.lan_server import stop_lan_server

            stop_lan_server()
        except Exception:
            pass
        try:
            from src.services.mariadb_controller import mariadb_controller

            mariadb_controller.stop_server()
        except Exception:
            pass
        release_store_server_lock()
        if tray:
            tray.hide()
        QApplication.instance().quit(0)

    def _on_close(event):
        if tray and tray.isVisible():
            win.hide()
            tray.showMessage(
                "Servidor de Tienda",
                "Sigue activo en la bandeja. La red de la tienda no se detuvo.",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
            event.ignore()
        else:
            _shutdown_store()
            event.accept()

    win.closeEvent = _on_close  # type: ignore[method-assign]
    btn_hide.clicked.connect(win.hide)
    btn_stop.clicked.connect(_shutdown_store)
    if getattr(win, "_tray_quit_action", None) is not None:
        win._tray_quit_action.triggered.connect(_shutdown_store)

    timer = QTimer(win)
    timer.timeout.connect(_watchdog)
    timer.start(10000)
    QTimer.singleShot(200, _watchdog)

    win.show()
    win.raise_()
    if tray:
        tray.showMessage(
            "Servidor de Tienda activo",
            "MariaDB y red LAN en marcha. Podés minimizarlo a la bandeja.",
            QSystemTrayIcon.MessageIcon.Information,
            4000,
        )

    try:
        from src.cerebro_global.backup_cerebro import cerebro_backup

        cerebro_backup.start("mariadb", "127.0.0.1")
    except Exception as e_cb:
        logger.warning(f"No se pudo iniciar CerebroBackup: {e_cb}")

    try:
        from src.cerebro_global.carteleria_cerebro.sincronizador_carteleria import (
            sincronizador_carteleria,
        )

        sincronizador_carteleria.start()
    except Exception as e_sc:
        logger.warning(f"No se pudo iniciar SincronizadorCarteleria: {e_sc}")

    logger.info("Servidor de Tienda en ejecución (proceso dedicado).")
    return qt_exec(app)
