import logging
from src.config import config
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

class MotorRed:
    """Motor central para la gestión de la red LAN y modos (Maestra/Esclava)."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def obtener_estado_red(self):
        """Devuelve el estado actual de la red."""
        return {
            "is_master": getattr(db_manager, "is_master", True),
            "caja_id": config.get("caja_id", 1),
            "db_engine": getattr(db_manager, "db_engine_type", "sqlite"),
            "db_host": config.get("db_host", "") or "localhost",
            "descubrimiento_udp_puerto": 37020
        }

    def convertir_en_maestra(self):
        """Convierte la PC en maestra (base de datos local MariaDB)."""
        try:
            config.set("is_master", True)
            config.set("db_engine", "mariadb")
            config.set("db_host", "localhost")
            db_manager.reconectar_mariadb("localhost")
            return True, "Configurado exitosamente como MAESTRA (Servidor MariaDB Local)."
        except Exception as e:
            self.logger.error(f"Error convirtiendo a maestra: {e}")
            return False, f"Error: {e}"

    def convertir_en_esclava(self, ip_maestra):
        """Convierte la PC en esclava conectándose a la IP maestra."""
        import re
        if ip_maestra:
            match = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', ip_maestra)
            if match:
                ip_maestra = match.group(0)
                
        if not ip_maestra or ip_maestra.lower() in ("localhost", "127.0.0.1"):
            return False, "Debes ingresar una IP válida de red (ej: 192.168.0.100)."
            
        try:
            config.set("is_master", False)
            config.set("db_engine", "mariadb")
            config.set("db_host", ip_maestra)
            
            db_manager.reconectar_mariadb(ip_maestra)
            
            if db_manager.is_connected():
                return True, f"Conexión exitosa a la Maestra en {ip_maestra}."
            else:
                # Revertir a local si falla
                config.set("is_master", True)
                config.set("db_engine", "sqlite")
                config.set("db_host", "localhost")
                db_manager.reconectar_local()
                return False, "Falló la conexión. Verificá que la IP sea correcta y que la PC Maestra esté encendida."
        except Exception as e:
            self.logger.error(f"Error convirtiendo a esclava: {e}")
            return False, f"Error inesperado: {e}"
