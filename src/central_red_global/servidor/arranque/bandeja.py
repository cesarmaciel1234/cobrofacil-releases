"""Ventana + bandeja del proceso `--server` (con escritorio)."""

from __future__ import annotations

import os

from src.logger import logger
from src.central_red_global.servidor.arranque.servicios import encender_servicios_tienda
from src.central_red_global.servidor.puerto import mariadb_port_open, needs_mariadb
from src.utils.candados import (
    acquire_store_server_lock,
    focus_existing_store_server,
    get_store_server_pid,
    release_store_server_lock,
)


def run_store_server_app(app) -> int:
    # Si la última ventana se oculta, Qt cierra el proceso. La bandeja tiene que seguir.
    app.setQuitOnLastWindowClosed(False)
    try:
        from src.central_red_global.servidor.autostart.windows import asegurar_nombre_aviso

        asegurar_nombre_aviso()
    except Exception:
        pass
    from PyQt6.QtCore import QTimer
    from PyQt6.QtGui import QAction
    from PyQt6.QtWidgets import (
        QApplication,
        QMenu,
        QSystemTrayIcon,
    )

    from src.utils.qt_compat import qt_exec

    if not acquire_store_server_lock():
        focus_existing_store_server()
        logger.info("Ya hay un Servidor de Tienda activo.")
        return 0

    from src.central_red_global.servidor.oficio.agente import (
        cumplir_esclava,
        oficio,
        vigila_mariadb,
    )

    try:
        from src.central_red_global.servidor.pareja.promover import ceder_si_hay_otra

        ceder_si_hay_otra()
    except Exception as e_ceder:
        logger.warning(f"No se pudo ceder la titularidad: {e_ceder}")

    if vigila_mariadb():
        encender_servicios_tienda(arrancar_mysqld=False)
    else:
        cumplir_esclava()

    from src.central_red_global.servidor.ventana import armar_lienzo, hoja_menu, icono_bandeja

    esclava = oficio() == "esclava"
    partes = armar_lienzo(esclava)
    win = partes["win"]
    poner_estado = partes["poner_estado"]
    consola = partes["consola"]
    btn_hide = partes["btn_hide"]
    btn_stop = partes["btn_stop"]
    consola.enganchar()
    consola.escribir(
        "consola en línea  ·  "
        + ("esclava, sin MariaDB local" if esclava else "maestra, tienda en esta PC")
    )

    tray = None
    app_icon = icono_bandeja(esclava)
    win.setWindowIcon(app_icon)

    if QSystemTrayIcon.isSystemTrayAvailable():
        tray = QSystemTrayIcon(app_icon, win)
        menu = QMenu()
        menu.setStyleSheet(hoja_menu())
        act_show = QAction("Mostrar espejo" if esclava else "Mostrar servidor", win)
        act_show.triggered.connect(lambda: _mostrar())
        act_quit = QAction("Apagar espejo" if esclava else "Apagar servidor", win)
        menu.addAction(act_show)
        menu.addSeparator()
        menu.addAction(act_quit)
        tray.setContextMenu(menu)
        tray.setToolTip(
            "Cobro Fácil — Espejo"
            if oficio() == "esclava"
            else "Cobro Fácil — Servidor de Tienda"
        )
        tray.show()

        def _on_tray(reason):
            if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
                _mostrar()

        tray.activated.connect(_on_tray)
        win._tray_quit_action = act_quit
    else:
        win.show()
        win._tray_quit_action = None

    def _refresh_status():
        pid = get_store_server_pid() or os.getpid()
        if oficio() == "esclava":
            poner_estado(f"ESCLAVA  ·  PID {pid}  ·  espejo en marcha", "esclava")
            return
        online = mariadb_port_open() if needs_mariadb() else True
        if online:
            poner_estado(f"ONLINE  ·  PID {pid}  ·  tienda visible en la red", "ok")
        else:
            poner_estado(f"DEGRADADO  ·  PID {pid}  ·  MariaDB no responde", "aviso")

    def _watchdog():
        if not vigila_mariadb():
            try:
                cumplir_esclava()
            except Exception:
                pass
            _refresh_status()
            return
        if needs_mariadb() and not mariadb_port_open():
            logger.warning("Watchdog Servidor: MariaDB caída — reintentando start_server()")
            try:
                from src.services.mariadb_controller import mariadb_controller

                mariadb_controller.start_server()
                from src.base_de_datos.database import db
                if getattr(db, "db_engine_type", "sqlite") == "sqlite":
                    db.reconectar_mariadb("127.0.0.1")
                    db._create_tables()
                    db._migrate_db()
            except Exception as e:
                logger.error(f"Watchdog MariaDB: {e}")
        try:
            from src.central_red_global.master_presence import ensure_master_lan_presence

            ensure_master_lan_presence()
        except Exception:
            pass
        _refresh_status()

    def _shutdown_store():
        from src.central_red_global.servidor.ventana.clave import pedir_clave

        aviso = (
            "El espejo deja de refrescarse. La última copia queda."
            if not vigila_mariadb()
            else "Se desconectan las cajas de esta maestra."
        )
        if not win.isVisible():
            _mostrar()
        if not pedir_clave(win, aviso):
            logger.info("Apagado cancelado.")
            return
        logger.info("Clave aceptada. Apagando el servidor.")
        if not vigila_mariadb():
            release_store_server_lock()
            if tray:
                tray.hide()
            QApplication.instance().quit()
            return
        try:
            from src.cerebro_global.backup_cerebro.ritmo.motor_backup import cerebro_backup as _cb

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
        QApplication.instance().quit()

    def _mostrar():
        try:
            consola.reanudar()
        except Exception:
            pass
        win.showNormal()
        win.raise_()
        win.activateWindow()

    def _ocultar():
        # La X no apaga y no espera a la base. El conteo corre en otro hilo.
        # hide() adentro de closeEvent deja la ventana blanca: Windows no termina el cierre.
        try:
            consola.pausar()
        except Exception:
            pass
        win.hide()
        if tray:
            tray.showMessage(
                "Servidor Cobro Fácil",
                "Sigue en la bandeja. La copia no se detuvo."
                if esclava
                else "Sigue activo en la bandeja. La red de la tienda no se detuvo.",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )

    def _al_cerrar():
        QTimer.singleShot(0, _ocultar)

    def _si_piden_frente():
        from src.utils.candados import STORE_SERVER_SHOW_PATH

        if not os.path.isfile(STORE_SERVER_SHOW_PATH):
            return
        try:
            os.remove(STORE_SERVER_SHOW_PATH)
        except OSError:
            pass
        _mostrar()

    win._al_cerrar = _al_cerrar
    reloj_frente = QTimer(win)
    reloj_frente.timeout.connect(_si_piden_frente)
    reloj_frente.start(200)
    btn_hide.clicked.connect(_ocultar)
    btn_stop.clicked.connect(_shutdown_store)
    if getattr(win, "_tray_quit_action", None) is not None:
        win._tray_quit_action.triggered.connect(_shutdown_store)

    timer = QTimer(win)
    timer.timeout.connect(_watchdog)
    timer.start(10000)
    QTimer.singleShot(200, _watchdog)

    win.show()
    win.raise_()
    win.activateWindow()
    if tray:
        tray.showMessage(
            "Servidor Cobro Fácil",
            "Ventana abierta. Ocultar en bandeja lo deja junto al reloj."
            if esclava
            else "MariaDB y red LAN en marcha. Podés minimizarlo a la bandeja.",
            QSystemTrayIcon.MessageIcon.Information,
            4000,
        )

    if vigila_mariadb():
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

        try:
            from src.central_red_global.servidor.pareja.repartir import prender

            prender()
        except Exception as e_re:
            logger.warning(f"No se pudo repartir el espejo: {e_re}")

    logger.info("Servidor de Tienda en ejecución (proceso dedicado).")
    return qt_exec(app)
