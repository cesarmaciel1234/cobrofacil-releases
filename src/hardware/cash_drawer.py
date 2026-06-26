from src.utils.qt_compat import qt_exec
import logging
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QMutex, QMutexLocker
import sys
import os

# Asegurar que el directorio raíz esté en el path para importaciones absolutas
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_path not in sys.path:
    sys.path.append(root_path)

try:
    from src.config import config
    from src.hardware.printer import printer_manager, _impresora_cajero_activo
except (ImportError, ModuleNotFoundError):
    from config import config
    from hardware.printer import printer_manager, _impresora_cajero_activo

logger = logging.getLogger(__name__)

class CashDrawerManager(QObject):
    """
    Módulo Centralizado de Gestión del Cajón de Dinero (Elite 2026).
    Maneja la apertura, el sensado de estado y la lógica de seguridad operativa.
    """
    
    drawer_opened = pyqtSignal()
    drawer_closed = pyqtSignal()
    intrusion_detected = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._last_status = False 
        self._apertura_autorizada = False
        self._is_checking = False
        self._opos_active = False
        self._lock = QMutex()
        self._init_opos()

    def _init_opos(self):
        """ Intenta inicializar el driver OPOS como fallback para hardware 3nstar/Epson. """
        try:
            import win32com.client
            from src.hardware.printer import OPOS_LDNS
            # Nombres lógicos: Prioridad al configurado, luego búsqueda genérica industrial
            custom_ldn = config.get("opos_drawer_name", "")
            ldns = [custom_ldn] if custom_ldn else OPOS_LDNS
            
            for ldn in ldns:
                if not ldn: continue
                try:
                    logger.info(f"Intentando conectar a OPOS LDN: {ldn}...")
                    self._opos = win32com.client.Dispatch("OPOS.CashDrawer")
                    self._opos.Open(ldn)
                    self._opos.ClaimDevice(2000)
                    self._opos.DeviceEnabled = True
                    self._opos_active = True
                    logger.info(f"✅ ¡ÉXITO! Motor OPOS activado para: {ldn}")
                    break
                except Exception as e:
                    logger.warning(f"❌ Fallo en LDN {ldn}: {e}")
                    continue
        except Exception as e:
            logger.error(f"❌ Error crítico al inicializar win32com/OPOS: {e}")

    def set_authorized(self, status=True):
        """ Marca la próxima apertura como autorizada para el monitor de seguridad. """
        self._apertura_autorizada = status
        if status:
            logger.info("Apertura autorizada programada.")

    def abrir(self, autorizada=True):
        """ Envía la señal física de apertura (OPOS o ESC/POS). """
        self._apertura_autorizada = autorizada
        logger.info(f"Abriendo cajón de dinero ({'Autorizada' if autorizada else 'FORZADA'}).")
        
        # 1. Intento vía OPOS si está activo
        if self._opos_active:
            try:
                self._opos.OpenDrawer()
                return True
            except Exception as e:
                logger.error(f"Fallo al abrir vía OPOS: {e}")
                self._opos_active = False # Fallback al motor genérico
        
        # 2. Fallback a motor genérico (Printer Manager)
        return printer_manager.abrir_cajon()

    def check_status(self):
        """ Consulta el estado físico de TODOS los cajones de forma segura. """
        locker = QMutexLocker(self._lock)
        if self._is_checking: return self._last_status
        
        self._is_checking = True
        try:
            # 1. Intento vía OPOS
            if self._opos_active:
                try:
                    status = self._opos.DrawerOpened
                    self._process_status_change(status)
                    return status
                except: 
                    self._opos_active = False

            # 2. Intento Genérico/Serial
            p1 = _impresora_cajero_activo()
            status = printer_manager.check_drawer_status(p1) if p1 else False
            
            self._process_status_change(status)
            return status
        finally:
            self._is_checking = False

    def _process_status_change(self, status):
        # Lógica de cambio de estado
        if status != self._last_status:
            if status is True:
                self.drawer_opened.emit()
                if not self._apertura_autorizada:
                    self.intrusion_detected.emit()
            else:
                self.drawer_closed.emit()
                self._apertura_autorizada = False
                
            self._last_status = status

    def reset_all(self):
        """ Desconecta todas las señales para evitar fugas de memoria al reiniciar la app. """
        try:
            self.drawer_opened.disconnect()
            self.drawer_closed.disconnect()
            self.intrusion_detected.disconnect()
        except: pass
        self._apertura_autorizada = False
        self._last_status = False

    @property
    def is_open(self):
        return self._last_status

    @property
    def is_authorized(self):
        return self._apertura_autorizada

# Instancia única (Singleton) para todo el sistema
drawer_manager = None

def reset_drawer_manager():
    global drawer_manager
    try:
        if drawer_manager is not None:
            drawer_manager.reset_all()
    except: pass
    drawer_manager = CashDrawerManager()

reset_drawer_manager()

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # Configuración de log para el test
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("DrawerTest")
    
    app = QApplication(sys.argv)
    
    def on_opened(): logger.info("📢 SEÑAL RECIBIDA: Cajón ABIERTO")
    def on_closed(): logger.info("📢 SEÑAL RECIBIDA: Cajón CERRADO")
    def on_intrusion(): logger.warning("⚠️ ALERTA: Apertura NO AUTORIZADA (Intrusión)")
    
    # Conectar señales para el test
    drawer_manager.drawer_opened.connect(on_opened)
    drawer_manager.drawer_closed.connect(on_closed)
    drawer_manager.intrusion_detected.connect(on_intrusion)
    
    logger.info("🔧 Iniciando Test de Hardware...")
    
    # Intentar apertura autorizada
    drawer_manager.abrir(autorizada=True)
    
    # Polling de estado cada 2 segundos para monitorear el sensor
    timer = QTimer()
    timer.timeout.connect(lambda: logger.info(f"📊 Estado actual: {'ABIERTO' if drawer_manager.check_status() else 'CERRADO'}"))
    timer.start(2000)
    
    logger.info("📡 Monitoreando señales. Cierre la ventana o Ctrl+C para terminar.")
sys.exit(qt_exec(app))