import sys
import os

# Añadir el directorio raíz al path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


import traceback
import threading
import time
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen, QProgressBar, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont
# from PyQt5.QtWebEngineWidgets import QWebEngineView # TEMPORALMENTE DESACTIVADO PARA COMPILAR

def global_excepthook(exc_type, exc_value, exc_traceback):
    try:
        with open("crash.log", "w") as f:
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    except: pass
    sys.__excepthook__(exc_type, exc_value, exc_traceback)
sys.excepthook = global_excepthook

# Nota: Los módulos pesados se cargan dentro de launch_app para acelerar el inicio.

# Variable global para mantener viva la ventana principal
main_window = None

def launch_app():
    global main_window
    
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
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
    from src.services.lan_server import init_lan_server
    init_lan_server()
    app.processEvents()

    def update_status(text, progress_val=None):
        splash.update_status(text, progress_val)

    # --- PASO 1: CARGAR RUTAS E ICONOS ---
    update_status("Cargando identidad visual...", 20)
    from PyQt5.QtGui import QIcon
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
    
    # Cerramos Splash y empezamos el flujo
    splash.finish(None)

    # Auto-iniciar el bot burbuja asistente
    try:
        import subprocess
        bot_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests_e2e", "bot_burbuja.py")
        if os.path.exists(bot_script):
            subprocess.Popen([sys.executable, bot_script])
    except Exception as e:
        print(f"Error auto-iniciando bot asistente: {e}")

    if not ok:
        QMessageBox.warning(None, "⚠️ AVISO DE HARDWARE", 
            f"No se pudo conectar con la impresora.\n\n{msg}\n\n"
            "El sistema funcionará en modo simulación.")

    # --- FLUJO DE VENTANAS ---
    # Verificar si estamos en modo "Espectador LAN" basado en la configuración real de la base de datos.
    from src.config import config
    from PyQt5.QtWidgets import QInputDialog, QLineEdit
    
    db_path = getattr(db_manager, 'db_path', "") or ""
    is_remote = not getattr(db_manager, 'is_master', True)
    if is_remote:
        import hashlib
        local_pin_saved = config.get("local_pin", hashlib.sha256("1234".encode()).hexdigest())
        pin, ok_pin = QInputDialog.getText(
            None,
            "Modo Espectador LAN - PIN",
            f"Estás ingresando en modo LAN remoto.\n\nPC maestra: {db_path}\n\nIngrese PIN de acceso:",
            QLineEdit.Password
        )
        if ok_pin:
            pin_hash = hashlib.sha256(pin.encode()).hexdigest()
            if pin_hash == local_pin_saved or pin == local_pin_saved:
                config.current_user = {"username": "Espectador LAN", "role": "admin", "lan_mode": True}
                main_window.apply_roles()
                main_window.show()
                main_window.iniciar_reconstruccion_scifi()
                result = app.exec_()
                main_window.close()
                return result
            else:
                QMessageBox.critical(None, "Error", "PIN incorrecto.")
                return 0
        else:
            return 0

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
                perfil_dlg.hide()
                app.processEvents()
                step = 2
            else:
                perfil_dlg.hide()
                app.processEvents()
                return 0
        elif step == 2:
            login_dlg = LoginPantalla(role_selected)
            if login_dlg.exec_():
                login_dlg.hide()
                app.processEvents()
                if role_selected == "cajero":
                    step = 3
                else:
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
            main_window.iniciar_reconstruccion_scifi()
            
            # --- JOYA DE PRESENTACIÓN (Transición de Partículas) ---
            from src.ui_components.welcome_transition import WelcomeOverlay
            main_window._welcome_overlay = WelcomeOverlay(main_window)
            main_window._welcome_overlay.show()
            # -------------------------------------------------------
            
            result = app.exec_()
            main_window.close()
            main_window = None
            return result

def start_hardware_watchdog():
    """ Hilo de vigilancia que asegura que el hardware responda. """
    def watchdog_loop():
        logging.info("[WATCHDOG] Iniciando vigilancia de hardware...")
        print("\n[WATCHDOG] Iniciando vigilancia de hardware...")
        while True:
            try:
                from src.hardware.cash_drawer import drawer_manager
                if drawer_manager is not None:
                    status = drawer_manager.check_status()
            except Exception as e:
                logging.error(f"[WATCHDOG ERROR] {e}")
                print(f"[WATCHDOG ERROR] {e}")

            
            time.sleep(5) # Vigilancia cada 5 segundos
            
    thread = threading.Thread(target=watchdog_loop, daemon=True)
    thread.start()
    return thread

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

        while True:
            try:
                is_master = getattr(db_manager, 'is_master', False)
                db_path = getattr(db_manager, 'db_path', "") or ""
                if is_master and db_path and os.path.exists(db_path):
                    if not _update_service_running:
                        if iniciar_servidor():
                            _update_service_running = True
                else:
                    if _update_service_running:
                        detener_servidor()
                        _update_service_running = False
            except Exception as e:
                logging.debug(f"[UPDATER] Service manager error: {e}")
            time.sleep(5)

    thread = threading.Thread(target=manager_loop, daemon=True)
    thread.start()
    return thread

def start_udp_discovery_server():
    """ Inicia el servicio de descubrimiento UDP en segundo plano para enlazar terminales automáticamente. """
    def server_loop():
        import socket
        import json
        import logging
        try:
            from src.base_de_datos.database import db_manager
            from src.utils.paths import get_base_path
        except ImportError:
            return
            
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('', 37020))
        except Exception as e:
            logging.error(f"UDP Discovery Bind Error: {e}")
            return
            
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                if data == b"PUNPRO_DISCOVER":
                    if not getattr(db_manager, 'is_master', False):
                        continue

                    if not os.path.exists(db_manager.db_path):
                        continue

                    base_path = get_base_path().lower()
                    db_path = db_manager.db_path.lower()
                    is_local = base_path in db_path or not db_path or db_path == "punpro.db"
                    
                    if is_local:
                        from src.config import config
                        import hashlib
                        hostname = socket.gethostname()
                        shared_folder = config.get("shared_folder_name", "tpv pro 2026")
                        current_db_name = config.get("db_name", "punpro.db")
                        shared_db_path = f"\\\\{hostname}\\{shared_folder}\\{current_db_name}"
                        server_ip = socket.gethostbyname(hostname)
                        
                        srv_pass = config.get("server_password", "admin")
                        srv_pass_hash = hashlib.sha256(srv_pass.encode()).hexdigest()
                        
                        response = {
                            "hostname": hostname,
                            "server_ip": server_ip,
                            "db_path": shared_db_path,
                            "pass_hash": srv_pass_hash,
                            "mode": "master"
                        }
                        sock.sendto(json.dumps(response).encode('utf-8'), addr)
            except Exception:
                pass
                
    thread = threading.Thread(target=server_loop, daemon=True)
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
        except Exception as e:
            logging.error(f"UDP Update Discovery Bind Error: {e}")
            return

        while True:
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
            except Exception:
                pass

    thread = threading.Thread(target=server_loop, daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    # psutil auto-kill disabled for debugging

    from src.logger import setup_logger
    setup_logger()
    
    # 1. Inicializar
    app = QApplication(sys.argv)
    
    # --- FEEDBACK TACTIL (MODULO INDEPENDIENTE) ---
    from src.ui_components.touch_feedback import TouchFeedbackManager
    touch_manager = TouchFeedbackManager(app)
    
    # 2. Inicializar el Hardware de forma segura
    from src.hardware.cash_drawer import reset_drawer_manager
    reset_drawer_manager()
    
    start_hardware_watchdog()
    start_update_server()           # Servidor LAN de actualizaciones (solo en la PC maestra)
    start_udp_discovery_server()    # Servidor de descubrimiento automático en red
    start_update_discovery_server() # Servidor de descubrimiento para actualizaciones LAN

    while True:
        exit_code = launch_app()
        if exit_code not in (99, 888):
            break
    sys.exit(exit_code)