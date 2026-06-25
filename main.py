import sys
import os

# Añadir el directorio raíz al path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import traceback
import threading
import time
import logging

# Desactivar aceleración por hardware para evitar deadlocks del chatbot Chromium
sys.argv.append('--disable-gpu')
sys.argv.append('--disable-software-rasterizer')

from PyQt5.QtCore import Qt, QTimer, QCoreApplication
# Vital: configurar antes de importar QApplication y QtWebEngineWidgets
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon

def global_excepthook(exc_type, exc_value, exc_traceback):
    try:
        from src.logger import logger
        logger.error("Excepción global no capturada:", exc_info=(exc_type, exc_value, exc_traceback))
        with open("crash.log", "w", encoding="utf-8") as f:
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    except: pass
    sys.__excepthook__(exc_type, exc_value, exc_traceback)
sys.excepthook = global_excepthook

# Nota: Los módulos pesados se cargan dentro de launch_app para acelerar el inicio.

# Variables globales para mantener viva la ventana principal y estado
main_window = None
app_exit_event = threading.Event()

def launch_app():
    global main_window
    
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
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
    
    # --- SPLASH SCREEN MODERNA (DISEÑO 2026) ---
    from src.inicio_y_perfiles.pantallaentrada import CobroFacilSplash
    splash = CobroFacilSplash()
    splash.show()
    app.processEvents()
    
    # 1. Recargar configuración desde el disco (vital tras reinicio 888)
    from src.config import config
    config._load_config()
    config.current_user = None # Limpiar sesión anterior si reinicia en el mismo proceso
    
    # 2. Recargar motor de base de datos para tomar la nueva ruta LAN
    from src.base_de_datos.database import db_manager
    db_manager._init_db()
    
    # Iniciar Servidor LAN si esta PC es la Maestra
    # NOTA: init_lan_server() ya se llama una vez en el bloque __main__.
    # No se llama de nuevo aquí para evitar el error OSError: [WinError 10048]
    # (doble bind del mismo puerto UDP 38001).
    app.processEvents()

    def update_status(text, progress_val=None):
        splash.update_status(text, progress_val)

    # --- PASO 1: CARGAR RUTAS E ICONOS ---
    update_status("Cargando identidad visual...", 20)
    from src.utils.paths import get_resource_path
    icon_path = get_resource_path(os.path.join("src", "icon.png"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # --- PASO 2: CARGAR HARDWARE ---
    update_status("Conectando periféricos industriales...", 40)
    from src.hardware.printer import printer_manager
    ok, msg = printer_manager.verificar_estado()

    # --- PASO 3: LICENCIA Y SEGURIDAD ---
    update_status("Verificando licencia de seguridad...", 60)
    from src.inicio_y_perfiles.licencia_pantalla import LicenciaPantalla, check_license_active
    if not check_license_active():
        splash.finish(None)
        lic = LicenciaPantalla()
        if not lic.exec_(): sys.exit()
        splash.show()

    # --- PASO 4: CARGAR MÓDULOS DE USUARIO ---
    update_status("Cargando perfiles de acceso...", 80)
    from src.inicio_y_perfiles.perfil_pantalla import PerfilPantalla
    from src.inicio_y_perfiles.login_pantalla import LoginPantalla
    from src.inicio_y_perfiles.apertura_pantalla import AperturaCajaPantalla
    from src.services.caja_service import verificar_y_realizar_autocierre
    
    update_status("Inicializando sistema...", 100)
    from src.main_window import MainWindow
    
    # Pre-creación de la ventana principal para ocultar la pausa en la pantalla de carga (Splash)
    main_window = MainWindow()
    
    # Precarga extrema de animaciones pesadas
    try:
        from src.ui_components.welcome_transition import WelcomeOverlay
        main_window._welcome_overlay = WelcomeOverlay(main_window)
        main_window._welcome_overlay.hide()
    except Exception as e:
        print("Error precargando WelcomeOverlay:", e)
    
    # Cerramos Splash y empezamos el flujo
    splash.finish(None)

    # Auto-iniciar el bot burbuja asistente (retrasado 5s para que Qt esté estable)
    def _launch_bot():
        try:
            import subprocess
            bot_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "cajero", "chat_bot_animado.py")
            if os.path.exists(bot_script):
                # Usar pythonw.exe para evitar el crash silencioso de QWebEngineView (Chromium) en Windows
                pythonw_exe = sys.executable.replace("python.exe", "pythonw.exe")
                if not os.path.exists(pythonw_exe):
                    pythonw_exe = sys.executable  # Fallback
                subprocess.Popen([pythonw_exe, bot_script])
        except Exception as e:
            print(f"Error auto-iniciando bot asistente: {e}")

    QTimer.singleShot(5000, _launch_bot)  # 5s de margen para que Qt/Chromium esté listo

    if not ok:
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

    # --- FLUJO DE VENTANAS NORMAL ---


    step = 1
    role_selected = None

    perfil_dlg = PerfilPantalla()
    def capture_role(role):
        nonlocal role_selected
        role_selected = role
    perfil_dlg.perfil_seleccionado.connect(capture_role)

    while True:
        if step == 1:
            if perfil_dlg.exec_():
                from src.utils.candados import PerfilLocker
                if not PerfilLocker.lock_profile(role_selected):
                    QMessageBox.warning(None, "Error", f"El perfil '{role_selected}' ya está en uso.")
                    continue
                
                # Inicializar el Cerebro Conector UDP (NetworkEngine)
                from src.network.network_engine import init_network_engine
                init_network_engine(role_selected)
                
                perfil_dlg.hide()
                app.processEvents()
                step = 2
            else:
                perfil_dlg.hide()
                app.processEvents()
                return 0
        elif step == 2:
            if role_selected == "carteleria":
                from src.config import config
                config.current_user = {"role": "carteleria"}
                step = 4
                continue
                
            login_dlg = LoginPantalla(role_selected)
            if login_dlg.exec_():
                login_dlg.hide()
                app.processEvents()
                if role_selected == "cajero":
                    step = 3
                else:  # admin o jefe van directo sin apertura de caja
                    step = 4
            else:
                login_dlg.hide()
                app.processEvents()
                step = 1
        elif step == 3:
            hizo_cierre, monto_c = verificar_y_realizar_autocierre()
            if hizo_cierre:
                QMessageBox.information(None, "🛡️ SISTEMA DE SEGURIDAD", 
                    f"Se detectaron ventas abiertas de días anteriores.\n\n"
                    f"El sistema realizó un CIERRE AUTOMÁTICO de ${monto_c:.2f}.")

            apertura = AperturaCajaPantalla()
            if apertura.exec_():
                apertura.hide()
                app.processEvents()
                step = 4
            else:
                apertura.hide()
                app.processEvents()
                step = 2
        elif step == 4:
            main_window.apply_roles()
            main_window.show()
            
            # --- ANIMACIÓN PRECARGADA (Arranca al instante) ---
            if hasattr(main_window, '_welcome_overlay') and main_window._welcome_overlay is not None:
                main_window._welcome_overlay.show()
                main_window._welcome_overlay.raise_()
            
            result = app.exec_()
            main_window.close()
            main_window = None
            return result


_update_service_running = False

def start_update_server():
    """
    Monitorea la configuración y mantiene el servidor de actualizaciones activo
    solamente si esta PC es la maestra local.
    """
    def manager_loop():
        global _update_service_running
        try:
            from src.updater.update_server import iniciar_servidor, detener_servidor
            from src.base_de_datos.database import db_manager
        except Exception as e:
            logging.debug(f"[UPDATER] No se pudo importar el servicio de actualizaciones: {e}")
            return

        while not app_exit_event.is_set():
            try:
                is_master = getattr(db_manager, 'is_master', False)
                db_path = getattr(db_manager, 'db_path', "") or ""
                db_valido = db_path.startswith("mariadb://") or db_path.startswith("mysql://") or os.path.exists(db_path)
                if is_master and db_path and db_valido:
                    if not _update_service_running:
                        if iniciar_servidor():
                            _update_service_running = True
                else:
                    if _update_service_running:
                        detener_servidor()
                        _update_service_running = False
            except Exception as e:
                logging.debug(f"[UPDATER] Service manager error: {e}")
            app_exit_event.wait(5)

    thread = threading.Thread(target=manager_loop, daemon=True)
    thread.start()
    return thread


def start_update_discovery_server():
    """Responde a las consultas de actualización LAN para clientes."""
    def server_loop():
        import socket
        import json
        import logging
        try:
            from src.base_de_datos.database import db_manager
        except ImportError:
            return

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('', 38002))
            sock.settimeout(2.0)
        except Exception as e:
            logging.error(f"UDP Update Discovery Bind Error: {e}")
            return

        while not app_exit_event.is_set():
            try:
                data, addr = sock.recvfrom(1024)
                if data == b"PUNPRO_UPDATE_DISCOVER":
                    if not getattr(db_manager, 'is_master', False):
                        continue
                    if not _update_service_running:
                        continue

                    server_ip = None
                    try:
                        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        probe.connect(addr)
                        server_ip = probe.getsockname()[0]
                        probe.close()
                    except:
                        pass

                    if not server_ip:
                        try:
                            server_ip = socket.gethostbyname(socket.gethostname())
                        except:
                            server_ip = addr[0]

                    if server_ip == "127.0.0.1":
                        server_ip = addr[0]

                    response = {"update_server": True, "server_ip": server_ip}
                    sock.sendto(json.dumps(response).encode('utf-8'), addr)
                    print(f"[UPDATER] Responded discovery to {addr[0]} with server_ip={server_ip}")
            except socket.timeout:
                continue
            except Exception:
                pass

    thread = threading.Thread(target=server_loop, daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    import sys
    if "--install-firewall" in sys.argv:
        from src.tools.setup_firewall import install_firewall
        install_firewall()
        sys.exit(0)

    from src.logger import setup_logger
    setup_logger()
    
    # Asegurar reglas de firewall de forma automática en el arranque
    try:
        from src.services.mariadb_controller import mariadb_controller
        mariadb_controller._ensure_firewall()
    except Exception as e:
        pass
    
    # 1. Inicializar
    app = QApplication(sys.argv)
    
    # --- FEEDBACK TACTIL (MODULO INDEPENDIENTE) ---
    from src.ui_components.touch_feedback import TouchFeedbackManager
    touch_manager = TouchFeedbackManager(app)
    
    # 2. Inicializar el Hardware de forma segura
    from src.hardware.cash_drawer import reset_drawer_manager
    reset_drawer_manager()

    start_update_server()           # Servidor LAN de actualizaciones (solo en la PC maestra)
    from src.services.lan_server import init_lan_server
    init_lan_server()               # Servidor LAN unificado (API HTTP y UDP Discovery)
    start_update_discovery_server() # Servidor de descubrimiento para actualizaciones LAN

    while True:
        exit_code = launch_app()
        if exit_code not in (99, 888):
            break
            
    try:
        from src.services.mariadb_controller import mariadb_controller
        mariadb_controller.stop_server()
    except Exception as e:
        print(f"Error al detener MariaDB: {e}")
        
    try:
        from src.services.lan_server import stop_lan_server
        stop_lan_server()
    except Exception as e:
        print(f"Error al detener LAN Server: {e}")
        
    app_exit_event.set()
    sys.exit(exit_code)