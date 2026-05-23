import sys
import os

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Añadir el directorio raíz al path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


import traceback
import threading
import time
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen, QProgressBar, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont

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
    from src.config import config
    config.current_user = None # Limpiar sesión anterior si reinicia en el mismo proceso
    
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    # --- SPLASH SCREEN MODERNA (DISEÑO 2026) ---
    splash_pix = QPixmap(400, 300)
    splash_pix.fill(Qt.transparent)
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setStyleSheet("background-color: #1E3A8A; color: white; border-radius: 20px; border: 2px solid #3B82F6;")
    
    # Label de Título en el Splash
    lbl_splash = QLabel("PUNPRO ELITE 2026", splash)
    lbl_splash.setAlignment(Qt.AlignCenter)
    lbl_splash.setGeometry(0, 80, 400, 50)
    lbl_splash.setStyleSheet("font-size: 24px; font-weight: bold; color: white; background: transparent; border: none;")
    
    lbl_status = QLabel("Iniciando motor industrial...", splash)
    lbl_status.setAlignment(Qt.AlignCenter)
    lbl_status.setGeometry(0, 220, 400, 30)
    lbl_status.setStyleSheet("font-size: 12px; color: #93C5FD; background: transparent; border: none;")
    
    splash.show()
    app.processEvents()

    def update_status(text):
        lbl_status.setText(text)
        app.processEvents()

    # --- PASO 1: CARGAR RUTAS E ICONOS ---
    update_status("Cargando identidad visual...")
    from PyQt5.QtGui import QIcon
    from src.utils.paths import get_resource_path
    icon_path = get_resource_path(os.path.join("src", "icon.png"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # --- PASO 2: CARGAR HARDWARE ---
    update_status("Conectando periféricos industriales...")
    from src.hardware.printer import printer_manager
    ok, msg = printer_manager.verificar_estado()

    # --- PASO 3: LICENCIA Y SEGURIDAD ---
    update_status("Verificando licencia de seguridad...")
    from src.paso1_licencia import Paso1Licencia, check_license_active
    if not check_license_active():
        splash.finish(None)
        lic = Paso1Licencia()
        if not lic.exec_(): sys.exit()
        splash.show()

    # --- PASO 4: CARGAR MÓDULOS DE USUARIO ---
    update_status("Cargando perfiles de acceso...")
    from src.paso2_perfil import Paso2Perfil
    from src.paso3_login import Paso3Login
    from src.paso4_apertura import Paso4AperturaCaja
    from src.services.caja_service import verificar_y_realizar_autocierre
    
    update_status("Finalizando inicialización...")
    from src.main_window import MainWindow
    
    # Pre-creación de la ventana principal para ocultar la pausa en la pantalla de carga (Splash)
    main_window = MainWindow()
    
    # Cerramos Splash y empezamos el flujo
    splash.finish(None)

    if not ok:
        QMessageBox.warning(None, "⚠️ AVISO DE HARDWARE", 
            f"No se pudo conectar con la impresora.\n\n{msg}\n\n"
            "El sistema funcionará en modo simulación.")

    # --- FLUJO DE VENTANAS ---
    # Verificar si estamos en modo "Espectador LAN"
    from src.config import config
    from PyQt5.QtWidgets import QInputDialog, QLineEdit
    
    db_path = config.get("db_path", "")
    is_remote = bool(db_path and (db_path.startswith("\\\\") or db_path.startswith("//") or ":" in db_path and ".db" in db_path and not "Desktop" in db_path))
    # Una forma más sencilla: Si hay un db_path configurado, asumimos que es remoto/custom
    if db_path and db_path != "":
        local_pin = config.get("local_pin", "1234")
        pin, ok_pin = QInputDialog.getText(None, "Modo Espectador LAN", f"Ingrese PIN de Acceso ({local_pin}):", QLineEdit.Password)
        if ok_pin and pin == local_pin:
            config.current_user = {"username": "Espectador LAN", "role": "admin"}
            main_window.apply_roles()
            main_window.show()
            main_window.iniciar_reconstruccion_scifi()
            result = app.exec_()
            main_window.close()
            return result
        else:
            QMessageBox.critical(None, "Error", "PIN incorrecto o cancelado.")
            return 0

    perfil_dlg = Paso2Perfil()
    role_selected = None
    
    def capture_role(role):
        nonlocal role_selected
        role_selected = role
    
    perfil_dlg.perfil_seleccionado.connect(capture_role)
    
    if perfil_dlg.exec_():
        perfil_dlg.hide()
        app.processEvents()
        
        login_dlg = Paso3Login(role_selected)
        if login_dlg.exec_():
            login_dlg.hide()
            app.processEvents()
            
            if role_selected == "cajero":
                hizo_cierre, monto_c = verificar_y_realizar_autocierre()
                if hizo_cierre:
                    QMessageBox.information(None, "🛡️ SISTEMA DE SEGURIDAD", 
                        f"Se detectaron ventas abiertas de días anteriores.\n\n"
                        f"El sistema realizó un CIERRE AUTOMÁTICO de ${monto_c:.2f}.")

                apertura = Paso4AperturaCaja()
                if apertura.exec_():
                    apertura.hide()
                    app.processEvents()
                    
                    main_window.apply_roles()
                    main_window.show()
                    main_window.iniciar_reconstruccion_scifi()
                    
                    result = app.exec_()
                    main_window.close()
                    main_window = None
                    return result
            else:
                main_window.apply_roles()
                main_window.show()
                main_window.iniciar_reconstruccion_scifi()
                
                result = app.exec_()
                main_window.close()
                main_window = None
                return result
    
    return 0

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

def start_update_server():
    """
    Intenta iniciar el servidor de actualizaciones LAN en segundo plano.
    Solo se activa si el puerto 38001 está libre (= esta es la PC maestra).
    Las PCs cliente fallan silenciosamente y no inician servidor.
    """
    def _iniciar():
        try:
            from src.updater.update_server import iniciar_servidor
            iniciar_servidor()
        except Exception as e:
            logging.debug(f"[UPDATER] No iniciado como servidor: {e}")
    thread = threading.Thread(target=_iniciar, daemon=True)
    thread.start()
    return thread

def start_udp_discovery_server():
    """ Inicia el servicio de descubrimiento UDP en segundo plano para enlazar terminales automáticamente. """
    def server_loop():
        import socket
        import json
        import logging
        try:
            from src.database import db_manager
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
                            "pass_hash": srv_pass_hash
                        }
                        sock.sendto(json.dumps(response).encode('utf-8'), addr)
            except Exception:
                pass
                
    thread = threading.Thread(target=server_loop, daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    # 1. Inicializar QApplication de primero para tener un contexto Qt válido para QObjects
    app = QApplication(sys.argv)
    
    # 2. Inicializar el Hardware de forma segura
    from src.hardware.cash_drawer import reset_drawer_manager
    reset_drawer_manager()
    
    start_hardware_watchdog()
    start_update_server()           # Servidor LAN de actualizaciones (solo en la PC maestra)
    start_udp_discovery_server()    # Servidor de descubrimiento automático en red

    while True:
        exit_code = launch_app()
        if exit_code not in (99, 888):
            break
    sys.exit(exit_code)