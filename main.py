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

# ─────────────────────────────────────────────────────────────────
# 🛡️ PORTABILIDAD: Se ejecuta ANTES de cualquier import de módulos
#    Limpia rutas del desarrollador y crea carpetas necesarias.
#    Funciona igual en cualquier PC donde se instale el ejecutable.
# ─────────────────────────────────────────────────────────────────
from src.utils.paths import get_base_path, sanitize_config, ensure_app_folders

# 1. Crear carpetas necesarias si no existen (primera instalación)
ensure_app_folders()

# 2. Limpiar rutas hardcodeadas del desarrollador en config.json
_config_path = os.path.join(get_base_path(), "config.json")
sanitize_config(_config_path)
# ─────────────────────────────────────────────────────────────────

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

# Instalar reporte automatico de errores hacia GitHub Issues
try:
    from src.utils.error_reporter import instalar_hook_global
    instalar_hook_global()
except Exception:
    pass  # Si falla, el excepthook basico sigue funcionando

# Nota: Los módulos pesados se cargan dentro de launch_app para acelerar el inicio.

# Variable global para mantener viva la ventana principal
main_window = None


def launch_app():
    global main_window
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    # --- SPLASH SCREEN ---
    splash_pix = QPixmap(420, 280)
    splash_pix.fill(Qt.transparent)
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #1e3a8a,stop:1 #0f172a); border-radius: 18px; border: 2px solid #3B82F6;")

    # Icono trofeo grande
    lbl_icon = QLabel("\U0001f3c6", splash)
    lbl_icon.setAlignment(Qt.AlignCenter)
    lbl_icon.setGeometry(0, 30, 420, 60)
    lbl_icon.setStyleSheet("font-size: 48px; background: transparent; border: none;")

    # Título principal
    lbl_splash = QLabel("CajaFácil Pro", splash)
    lbl_splash.setAlignment(Qt.AlignCenter)
    lbl_splash.setGeometry(0, 95, 420, 50)
    lbl_splash.setStyleSheet("font-size: 28px; font-weight: 900; color: white; background: transparent; border: none; letter-spacing: 1px;")

    # Subtítulo
    lbl_sub = QLabel("Vendé rápido · Sin experiencia · Sin complicaciones", splash)
    lbl_sub.setAlignment(Qt.AlignCenter)
    lbl_sub.setGeometry(0, 148, 420, 28)
    lbl_sub.setStyleSheet("font-size: 11px; color: #93C5FD; background: transparent; border: none;")

    lbl_status = QLabel("Iniciando...", splash)
    lbl_status.setAlignment(Qt.AlignCenter)
    lbl_status.setGeometry(0, 230, 420, 28)
    lbl_status.setStyleSheet("font-size: 11px; color: #64748b; background: transparent; border: none;")
    
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
                    # Si va a reiniciar, aplicar update de GitHub en silencio
                    if result in (99, 888):
                        _aplicar_update_silencioso()
                    return result
            else:
                main_window.apply_roles()
                main_window.show()
                main_window.iniciar_reconstruccion_scifi()
                
                result = app.exec_()
                main_window.close()
                main_window = None
                # Si va a reiniciar, aplicar update de GitHub en silencio
                if result in (99, 888):
                    _aplicar_update_silencioso()
                return result
    
    return 0


def _aplicar_update_silencioso():
    """
    Descarga actualizaciones de GitHub en silencio durante el reinicio.
    No muestra ningun dialogo — solo actualiza los archivos si hay cambios.
    Se ejecuta ANTES de que la app se relance para que el reinicio ya use
    la version nueva.
    """
    try:
        from src.config import config
        if not config.get('github_update_enabled', True):
            return
        if not config.get('auto_update_check', True):
            return
        from src.updater.github_updater import verificar_actualizaciones_github
        logging.info("[AUTO-UPDATE] Verificando actualizaciones en GitHub...")
        res = verificar_actualizaciones_github(dry_run=False)
        if res.actualizados:
            logging.info(f"[AUTO-UPDATE] {len(res.actualizados)} archivos actualizados: {res.actualizados}")
        elif res.errores:
            logging.debug(f"[AUTO-UPDATE] Sin conexion o sin cambios: {res.errores[0]}")
    except Exception as e:
        logging.debug(f"[AUTO-UPDATE] Error silencioso: {e}")


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
                        shared_folder = config.get("shared_folder_name", "cajafacil pro")
                        shared_db_path = f"\\\\{hostname}\\{shared_folder}\\punpro.db"
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
    # Solución para pantallas de distintos tamaños (14", 15", 19", 24", 32")
    # NO usamos AA_EnableHighDpiScaling porque agranda todo demasiado en laptops.
    # En su lugar, forzamos escala 1:1 y la app ajusta sus propios tamaños
    # con _get_ui_scale() basado en la resolución real del monitor.
    import os
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    os.environ["QT_SCALE_FACTOR"] = "1"
    from PyQt5.QtCore import Qt
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

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