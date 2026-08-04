"""Proceso Servidor de Tienda (independiente del cajero / lanzador).

Dueño de: MariaDB, API LAN, discovery UDP, NetworkEngine maestra, updater LAN.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time

from src.logger import logger
from src.utils.candados import (
    STORE_SERVER_WINDOW_TITLE,
    acquire_store_server_lock,
    focus_existing_store_server,
    get_store_server_pid,
    is_store_server_running,
    release_store_server_lock,
)


def _mariadb_port_open(host: str = "127.0.0.1", port: int = 3306, timeout: float = 0.8) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        ok = s.connect_ex((host, port)) == 0
        s.close()
        return ok
    except Exception:
        return False


def _build_server_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [os.path.abspath(sys.executable), "--server"]
    main_py = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "main.py"))
    return [sys.executable, main_py, "--server"]


def ensure_store_server_process(timeout_sec: float = 45.0) -> bool:
    """Si no hay servidor, lo lanza y espera MariaDB o el candado vivo."""
    try:
        from src.updater.silent_auto_updater import is_apply_guard_active
        if is_apply_guard_active():
            logger.info("ensure_store_server: update en curso — no se lanza Servidor.")
            return False
    except Exception:
        pass

    try:
        from src.central_red_global.master_presence import es_pc_maestra_local
        if not es_pc_maestra_local():
            logger.info("ensure_store_server: PC esclava — no se lanza Servidor de Tienda.")
            return False
    except Exception:
        pass

    if is_store_server_running():
        return True

    cmd = _build_server_command()
    logger.info(f"Arrancando Servidor de Tienda: {cmd}")
    try:
        flags = 0
        if sys.platform == "win32":
            # Proceso independiente: sobrevive al cierre del lanzador
            flags = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
            flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        from src.utils.paths import get_base_path

        subprocess.Popen(
            cmd,
            cwd=get_base_path(),
            creationflags=flags,
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
    except Exception as e:
        logger.error(f"No se pudo lanzar Servidor de Tienda: {e}")
        return False

    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if not is_store_server_running():
            time.sleep(0.4)
            continue
        if not _needs_mariadb() or _mariadb_port_open():
            logger.info("Servidor de Tienda ONLINE.")
            return True
        time.sleep(0.4)

    if is_store_server_running():
        logger.warning("Servidor de Tienda vivo pero MariaDB aún no responde en 3306.")
        return True
    logger.error("Timeout esperando Servidor de Tienda.")
    return False


def _needs_mariadb() -> bool:
    try:
        from src.config import config
        eng = str(config.get("db_engine", "sqlite")).lower()
        host = str(config.get("db_host", "") or "").lower()
        return eng == "mariadb" and host in ("", "localhost", "127.0.0.1")
    except Exception:
        return True


def is_store_server_online() -> bool:
    """ONLINE = proceso servidor vivo (y 3306 si aplica MariaDB local)."""
    if not is_store_server_running():
        return False
    if _needs_mariadb():
        return _mariadb_port_open()
    return True


def run_store_server_app(app) -> int:
    """UI mínima + servicios. `app` es QApplication ya creado."""
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

    # --- Servicios de tienda ---
    try:
        from src.services.mariadb_controller import mariadb_controller
        mariadb_controller._ensure_firewall()
    except Exception as e:
        logger.warning(f"Firewall servidor: {e}")

    try:
        from src.base_de_datos.database import db_manager
        db_manager._init_db()
    except Exception as e:
        logger.error(f"Init DB servidor: {e}")

    try:
        from src.central_red_global.lan_server import init_lan_server
        init_lan_server()
    except Exception as e:
        logger.warning(f"LAN server: {e}")

    try:
        from src.central_red_global.master_presence import ensure_master_lan_presence
        ensure_master_lan_presence()
    except Exception as e:
        logger.warning(f"Presencia maestra: {e}")

    # --- Ventana / bandeja ---
    win = QWidget()
    win.setWindowTitle(STORE_SERVER_WINDOW_TITLE)
    win.setFixedSize(420, 220)
    win.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowCloseButtonHint)

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
        # act_quit se conecta después de definir _shutdown_store
        win._tray_quit_action = act_quit
    else:
        win.show()
        win._tray_quit_action = None

    def _refresh_status():
        online = _mariadb_port_open() if _needs_mariadb() else True
        pid = get_store_server_pid() or os.getpid()
        if online:
            status.setText(f"ONLINE — PID {pid}\nLa tienda es visible en la red (sin cajero).")
            status.setStyleSheet("font-size: 13px; font-weight: 700; color: #15803D;")
        else:
            status.setText(f"DEGRADADO — PID {pid}\nMariaDB no responde; reintentando…")
            status.setStyleSheet("font-size: 13px; font-weight: 700; color: #C2410C;")

    def _watchdog():
        if _needs_mariadb() and not _mariadb_port_open():
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
        # El backup lo hace CerebroBackup en su propio hilo (no el watchdog)
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
        # Detener cerebro y sello final ANTES de apagar MariaDB
        try:
            from src.cerebro_global.backup_cerebro import cerebro_backup
            cerebro_backup.tick_now(force_full=True)
            cerebro_backup.stop()
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
        # Cerrar ventana = ocultar; apagar solo con botón / menú
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

    if not tray:
        win.show()
    else:
        win.hide()
        tray.showMessage(
            "Servidor de Tienda activo",
            "MariaDB y red LAN en marcha. Podés abrir el Lanzador cuando quieras.",
            QSystemTrayIcon.MessageIcon.Information,
            4000,
        )

    # Cerebro de backup 100% autónomo (cada 30 min; incremental si hay pocas ventas)
    try:
        from src.cerebro_global.backup_cerebro import cerebro_backup
        cerebro_backup.start("mariadb", "127.0.0.1")
    except Exception as e_cb:
        logger.warning(f"No se pudo iniciar CerebroBackup: {e_cb}")

    # Sync cartelería en el servidor (sin abrir cajero ni lanzador)
    try:
        from src.cerebro_global.carteleria_cerebro.sincronizador_carteleria import (
            sincronizador_carteleria,
        )
        sincronizador_carteleria.start()
    except Exception as e_sc:
        logger.warning(f"No se pudo iniciar SincronizadorCarteleria: {e_sc}")

    logger.info("Servidor de Tienda en ejecución (proceso dedicado).")
    return qt_exec(app)


# ── Arranque con Windows ────────────────────────────────────────────────────

def _startup_shortcut_path() -> str:
    appdata = os.environ.get("APPDATA", "")
    return os.path.join(
        appdata,
        "Microsoft",
        "Windows",
        "Start Menu",
        "Programs",
        "Startup",
        "CobroFacil_ServidorTienda.lnk",
    )


def set_windows_autostart(enabled: bool) -> bool:
    """Crea o elimina el acceso directo en Startup → `exe --server`."""
    if sys.platform != "win32":
        return False
    path = _startup_shortcut_path()
    try:
        if not enabled:
            if os.path.exists(path):
                os.remove(path)
            return True

        from src.utils.paths import get_base_path

        cmd = _build_server_command()
        target = cmd[0]
        args = subprocess.list2cmdline(cmd[1:])
        workdir = get_base_path()
        path_ps = path.replace("'", "''")
        target_ps = target.replace("'", "''")
        args_ps = args.replace("'", "''")
        work_ps = workdir.replace("'", "''")

        ps = (
            "$ws = New-Object -ComObject WScript.Shell; "
            f"$s = $ws.CreateShortcut('{path_ps}'); "
            f"$s.TargetPath = '{target_ps}'; "
            f"$s.Arguments = '{args_ps}'; "
            f"$s.WorkingDirectory = '{work_ps}'; "
            "$s.WindowStyle = 7; "
            "$s.Description = 'Cobro Facil Servidor de Tienda'; "
            "$s.Save()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            timeout=15,
        )
        return os.path.exists(path)
    except Exception as e:
        logger.error(f"Autostart Windows: {e}")
        return False


def is_windows_autostart_enabled() -> bool:
    return sys.platform == "win32" and os.path.exists(_startup_shortcut_path())
