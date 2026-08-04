from src.utils.qt_compat import qt_exec
import sys
import os

# Añadir el directorio raíz al path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.qt_dpi import configure_process_dpi, configure_qt_application_attributes
from src.utils.qt_compat import set_share_opengl_contexts, qt_exec

configure_process_dpi()

import traceback
import threading
import time
import logging
import urllib3

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Desactivar aceleración por hardware para evitar deadlocks del chatbot Chromium
sys.argv.append('--disable-gpu')
sys.argv.append('--disable-software-rasterizer')

from PyQt6.QtCore import QTimer, QCoreApplication

configure_qt_application_attributes()
# Vital: configurar antes de importar QApplication y QtWebEngineWidgets
set_share_opengl_contexts()

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon

import argparse
from src.utils.candados import PerfilLocker, acquire_master_launcher_lock
from src.base_de_datos.autoblindaje_db import AutoBlindajeDB
from src.base_de_datos.motor_flash_transacciones import motor_flash
from src.inicio_y_perfiles.perfil_pantalla import PerfilPantalla

def global_excepthook(exc_type, exc_value, exc_traceback):
    try:
        from src.logger import logger
        try:
            from src.services.auto_heal import try_auto_heal
            heal = try_auto_heal(
                f"{exc_type.__name__}: {exc_value}",
                exc=exc_value,
                traceback_text="".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
            )
            if heal.healed:
                logger.warning(
                    "Excepción curada en runtime (%s): %s",
                    heal.action,
                    exc_value,
                )
                with open("crash.log", "w", encoding="utf-8") as f:
                    traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
        except Exception:
            pass
        logger.error("Excepción global no capturada:", exc_info=(exc_type, exc_value, exc_traceback))
        with open("crash.log", "w", encoding="utf-8") as f:
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
        # El handler GitHubReportHandler encola el ERROR; refuerzo CRITICAL explícito.
        try:
            from src.services.github_error_reporter import queue_error_report
            queue_error_report(
                f"{exc_type.__name__}: {exc_value}",
                level="CRITICAL",
                source="global_excepthook",
                exc_info=(exc_type, exc_value, exc_traceback),
                skip_heal=True,
            )
        except Exception:
            pass
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_traceback)
sys.excepthook = global_excepthook

# Nota: Los módulos pesados se cargan dentro de launch_app para acelerar el inicio.

# Variables globales para mantener viva la ventana principal y estado
main_window = None
app_exit_event = threading.Event()

def launch_app(direct_role=None):
    global main_window

    try:
        from src.updater.silent_auto_updater import apply_pending_update_on_startup
        apply_pending_update_on_startup()
    except Exception:
        pass
    
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    if not getattr(app, "_network_engine_shutdown_hook", False):
        from src.central_red_global.network_engine import shutdown_network_engine
        app.aboutToQuit.connect(shutdown_network_engine)
        app._network_engine_shutdown_hook = True
    
    # Tras reinicio 888: cerrar ventanas/diálogos que hayan quedado abiertos
    if main_window is not None:
        try:
            main_window.hide()
            main_window.close()
        except Exception:
            pass
        main_window = None
    for w in app.topLevelWidgets():
        try:
            w.hide()
            w.close()
        except Exception:
            pass
    app.processEvents()
    
    # FORZAR ESTILO FUSION (VITAL PARA QUE LOS SCROLLBARS ACEPTEN CSS EN WINDOWS)
    app.setStyle('Fusion')

    from src.utils.qt_dpi import apply_app_screen_adaptation
    apply_app_screen_adaptation(app)
    
    is_direct = bool(direct_role)

    # --- SPLASH SCREEN MODERNA (DISEÑO 2026) ---
    if not is_direct:
        from src.inicio_y_perfiles.pantallaentrada import CobroFacilSplash
        splash = CobroFacilSplash()
        splash.show()
        app.processEvents()
        
        def update_status(text, progress_val=None):
            splash.update_status(text, progress_val)
    else:
        splash = None
        def update_status(text, progress_val=None):
            pass

    def run_heavy_task_fluid(task_func, timeout_sec=60):
        """Ejecuta una función pesada en un hilo manteniendo la UI fluida."""
        import threading, time
        t = threading.Thread(target=task_func, daemon=True)
        t.start()
        start_t = time.time()
        while t.is_alive():
            app.processEvents()
            time.sleep(0.01)
            if time.time() - start_t > timeout_sec:
                break # Evitar cuelgue infinito si el hilo falla internamente
        return t

    # 1. Recargar configuración desde el disco (vital tras reinicio 888)
    from src.config import config
    config._load_config()
    config.current_user = None # Limpiar sesión anterior si reinicia en el mismo proceso
    
    # 2. BD en hilo: el import dispara _init_db; no bloquear el splash en el hilo UI
    try:
        from src.central_red_global.store_server import is_store_server_online
        _store_up = (not is_direct) and is_store_server_online()
    except Exception:
        _store_up = False

    if _store_up:
        update_status("Conectando al Servidor de Tienda...", 18)
    else:
        update_status("Inicializando base de datos...", 15)

    def _boot_db():
        from src.base_de_datos.database import db_manager
        db_manager._init_db()

    if is_direct:
        _boot_db()
    else:
        run_heavy_task_fluid(_boot_db, timeout_sec=45)

    # Sync cartelería: en terminales sí; en lanzador solo si no hay Servidor dedicado
    try:
        from src.utils.candados import is_store_server_running
        _sync_ok = is_direct or not is_store_server_running()
    except Exception:
        _sync_ok = True
    if _sync_ok:
        from src.cerebro_global.carteleria_cerebro.sincronizador_carteleria import sincronizador_carteleria
        sincronizador_carteleria.start()

    app.processEvents()

    # --- PASO 1: CARGAR RUTAS E ICONOS ---
    update_status("Cargando identidad visual...", 30)
    from src.utils.paths import get_resource_path
    icon_path = get_resource_path(os.path.join("src", "icon.png"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # --- PASO 2: CARGAR HARDWARE ---
    update_status("Conectando periféricos industriales...", 45)
    from src.hardware.printer import printer_manager
    ok = True
    msg = ""
    if not is_direct:
        ok_ref = [False]
        msg_ref = [""]
        def _check_printer():
            o, m = printer_manager.verificar_estado()
            ok_ref[0] = o
            msg_ref[0] = m
        run_heavy_task_fluid(_check_printer, timeout_sec=3)
        ok, msg = ok_ref[0], msg_ref[0]
    else:
        threading.Thread(target=printer_manager.verificar_estado, daemon=True).start()

    # --- PASO 3: LICENCIA Y SEGURIDAD ---
    update_status("Verificando licencia de seguridad...", 60)
    from src.inicio_y_perfiles.licencia_pantalla import LicenciaPantalla, check_license_active
    
    if not is_direct:
        lic_active = [False]
        run_heavy_task_fluid(lambda: lic_active.__setitem__(0, check_license_active()), timeout_sec=5)
        
        if not lic_active[0]:
            if splash: splash.finish(None)
            lic = LicenciaPantalla()
            if not qt_exec(lic): sys.exit()
            if splash: splash.show()

    # --- PASO 4: CARGAR MÓDULOS DE USUARIO ---
    update_status("Cargando perfiles de acceso...", 80)
    from src.inicio_y_perfiles.logica.auth_controller import AuthController
    AuthController().ensure_default_jefe()
    
    from src.inicio_y_perfiles.perfil_pantalla import PerfilPantalla
    from src.inicio_y_perfiles.login_pantalla import LoginPantalla
    from src.inicio_y_perfiles.apertura_pantalla import AperturaCajaPantalla
    from src.services.caja_service import verificar_y_realizar_autocierre
    
    update_status("Inicializando sistema (Lazy Loading)...", 100)
    from src.main_window import MainWindow
    
    # ¡Gracias al verdadero Lazy Loading, esto es instantáneo!
    main_window = MainWindow()
    
    # Precarga extrema de animaciones pesadas
    try:
        from src.ui_components.welcome_transition import WelcomeOverlay
        main_window._welcome_overlay = WelcomeOverlay(main_window)
        main_window._welcome_overlay.hide()
    except Exception as e:
        print("Error precargando WelcomeOverlay:", e)
    
    # Cerramos Splash si existe y empezamos el flujo
    if splash:
        splash.finish(None)

    if not is_direct and not ok:
        QMessageBox.warning(None, "⚠️ AVISO DE HARDWARE", 
            f"No se pudo conectar con la impresora.\n\n{msg}\n\n"
            "El sistema funcionará en modo simulación.")
        QMessageBox.warning(None, "⚠️ AVISO DE HARDWARE", 
            f"No se pudo conectar con la impresora.\n\n{msg}\n\n"
            "El sistema funcionará en modo simulación.")

    # --- HILO EN SEGUNDO PLANO PARA REPORTES SEMANALES ---
    def check_and_send_weekly_report():
        try:
            from src.services.email_service import enviar_reporte_semanal_si_es_necesario
            # Esperar unos segundos para no entorpecer el arranque
            time.sleep(15)
            enviar_reporte_semanal_si_es_necesario()
        except Exception as e:
            print(f"Error en hilo de reporte semanal: {e}")
            
    threading.Thread(target=check_and_send_weekly_report, daemon=True).start()

    # --- MODO EJECUCIÓN DIRECTA DE PERFIL ---
    if direct_role:
        from src.utils.candados import PerfilLocker
        if not PerfilLocker.lock_profile(direct_role):
            QMessageBox.warning(None, "Error", f"El perfil '{direct_role}' ya está en uso.")
            return 0
        from src.central_red_global.network_engine import init_network_engine
        init_network_engine(direct_role)
        role_selected = direct_role
        step = 2
    else:
        step = 1
        role_selected = None

    perfil_dlg = PerfilPantalla(is_master_launcher=True)
    def capture_role(role):
        nonlocal role_selected
        role_selected = role
    perfil_dlg.perfil_seleccionado.connect(capture_role)

    while True:
        if step == 1:
            if qt_exec(perfil_dlg):
                # En modo Lanzador Maestro, PerfilPantalla gestiona los subprocesos autónomos
                return 0
            else:
                perfil_dlg.hide()
                app.processEvents()
                return 0
        elif step == 2:
            if role_selected == "carteleria":
                # Lanzar la Cartelería en el mismo proceso (clave para el ejecutable).
                # Propagar el código de qt_exec: 888/99 deben reiniciar el loop externo.
                from src.carteleria.carteleria import lanzar_app
                perfil_dlg.hide()
                return lanzar_app(app)
                
            login_dlg = LoginPantalla(role_selected)
            if qt_exec(login_dlg):
                login_dlg.hide()
                app.processEvents()
                if role_selected == "cajero":
                    step = 3
                else:  # admin o jefe van directo sin apertura de caja
                    step = 4
            else:
                login_dlg.hide()
                app.processEvents()
                if direct_role:
                    return 0
                step = 1
        elif step == 3:
            hizo_cierre, monto_c = verificar_y_realizar_autocierre()
            if hizo_cierre:
                QMessageBox.information(None, "🛡️ SISTEMA DE SEGURIDAD", 
                    f"Se detectaron ventas abiertas de días anteriores.\n\n"
                    f"El sistema realizó un CIERRE AUTOMÁTICO de ${monto_c:.2f}.")

            apertura = AperturaCajaPantalla()
            if qt_exec(apertura):
                apertura.hide()
                app.processEvents()
                step = 4
            else:
                apertura.hide()
                app.processEvents()
                step = 2
        elif step == 4:
            main_window.apply_roles()
            from src.utils.qt_dpi import present_main_window
            present_main_window(main_window)
            
            # --- ANIMACIÓN PRECARGADA (Arranca al instante) ---
            if hasattr(main_window, '_welcome_overlay') and main_window._welcome_overlay is not None:
                main_window._welcome_overlay.show()
                main_window._welcome_overlay.raise_()
            
            result = qt_exec(app)
            try:
                from src.central_red_global.network_engine import shutdown_network_engine
                shutdown_network_engine()
            except Exception:
                pass
            main_window.close()
            main_window = None
            return result


if __name__ == "__main__":
    import sys
    if "--install-firewall" in sys.argv:
        from src.tools.setup_firewall import install_firewall
        ok = install_firewall()
        sys.exit(0 if ok else 1)

    parser = argparse.ArgumentParser(description="CobroFacil PRO 2026")
    parser.add_argument(
        "--role", "--profile", type=str, default=None,
        choices=["cajero", "admin", "jefe", "carteleria"],
        help="Ejecutar rol autónomo (terminal)",
    )
    parser.add_argument(
        "--server", action="store_true",
        help="Proceso Servidor de Tienda (MariaDB + LAN + presencia)",
    )
    parsed_args, _ = parser.parse_known_args()
    target_role = parsed_args.role
    is_store_server = bool(parsed_args.server)
    is_terminal_role = bool(target_role)

    from src.logger import setup_logger
    setup_logger()

    try:
        import ctypes
        if sys.platform == "win32":
            myappid = "punpro.cobrofacil.pos.31"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    # ── MODO SERVIDOR DE TIENDA (proceso dedicado) ──────────────────────────
    if is_store_server:
        try:
            from src.updater.silent_auto_updater import apply_pending_update_on_startup
            apply_pending_update_on_startup()
        except Exception:
            pass

        app = QApplication.instance() or QApplication(sys.argv)
        if not getattr(app, "_network_engine_shutdown_hook", False):
            from src.central_red_global.network_engine import shutdown_network_engine
            app.aboutToQuit.connect(shutdown_network_engine)
            app._network_engine_shutdown_hook = True

        try:
            from src.ui_components.tema_estilos import aplicar_tema
            from src.config import config
            tema = "estilo_dia.qss" if config.get("theme", "light") == "light" else "estilo_noche.qss"
            aplicar_tema(app, tema)
        except Exception:
            pass

        from src.central_red_global.store_server import run_store_server_app
        code = run_store_server_app(app)
        app_exit_event.set()
        sys.exit(code if code is not None else 0)

    # Actualizaciones en segundo plano (lanzador / terminales)
    try:
        from src.updater.silent_auto_updater import (
            apply_pending_update_on_startup,
            start_background_update_service,
        )
        apply_pending_update_on_startup()
        start_background_update_service()
    except Exception:
        pass

    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    if not getattr(app, "_network_engine_shutdown_hook", False):
        from src.central_red_global.network_engine import shutdown_network_engine
        app.aboutToQuit.connect(shutdown_network_engine)
        app._network_engine_shutdown_hook = True

    try:
        from src.ui_components.tema_estilos import aplicar_tema
        from src.config import config
        tema_actual = config.get("theme", "light")
        qss_filename = "estilo_dia.qss" if tema_actual == "light" else "estilo_noche.qss"
        aplicar_tema(app, qss_filename)
    except Exception as e:
        print(f"No se pudo cargar el módulo de temas: {e}")

    from src.ui_components.touch_feedback import TouchFeedbackManager
    touch_manager = TouchFeedbackManager(app)

    from src.hardware.cash_drawer import reset_drawer_manager
    reset_drawer_manager()

    from src.utils.candados import is_store_server_running

    # Terminales: no pelear por puertos LAN si el Servidor ya los tiene
    if is_terminal_role:
        if not is_store_server_running():
            try:
                from src.central_red_global.lan_server import init_lan_server
                init_lan_server()
            except Exception:
                pass
    else:
        # Lanzador: asegura proceso Servidor (MariaDB + red), no los posee
        try:
            if not acquire_master_launcher_lock():
                sys.exit(0)
        except Exception as e:
            print(f"Aviso al verificar candado maestro: {e}")

        from src.config import config
        from src.central_red_global.master_presence import es_pc_maestra_local

        if config.get("auto_start_store_server", True) and es_pc_maestra_local():
            try:
                from src.central_red_global.store_server import (
                    ensure_store_server_process,
                    set_windows_autostart,
                    is_windows_autostart_enabled,
                )
                print("[TIENDA] Asegurando Servidor de Tienda…")
                ok_srv = ensure_store_server_process(timeout_sec=45.0)
                if ok_srv and config.get("auto_start_store_server", True) and not is_windows_autostart_enabled():
                    set_windows_autostart(True)
                if not ok_srv:
                    raise RuntimeError("spawn servidor falló")
            except Exception as e:
                print(f"Aviso Servidor de Tienda: {e}")
                # Fallback: presencia en este proceso si el spawn falló
                try:
                    from src.services.mariadb_controller import mariadb_controller
                    mariadb_controller._ensure_firewall()
                    from src.central_red_global.lan_server import init_lan_server
                    init_lan_server()
                    from src.central_red_global.master_presence import ensure_master_lan_presence
                    ensure_master_lan_presence()
                except Exception as e2:
                    print(f"Fallback presencia local: {e2}")

    while True:
        exit_code = launch_app(direct_role=target_role)
        if exit_code not in (99, 888):
            break

    # Solo el proceso --server apaga MariaDB/LAN. Lanzador y terminales no tumban la tienda.
    if is_terminal_role and not is_store_server_running():
        try:
            from src.central_red_global.lan_server import stop_lan_server
            stop_lan_server()
        except Exception:
            pass
        try:
            from src.services.mariadb_controller import mariadb_controller
            if getattr(mariadb_controller, "_process", None) is not None:
                mariadb_controller.stop_server()
        except Exception:
            pass

    app_exit_event.set()
    sys.exit(exit_code)