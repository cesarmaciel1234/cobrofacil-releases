import logging

from src.config import config
from src.central_red_global.servidor.rol.esclava import convertir_en_esclava
from src.central_red_global.servidor.rol.maestra import convertir_en_maestra


def _db_manager():
    """Import perezoso: este módulo se carga mientras la base todavía arranca."""
    from src.base_de_datos.database import db_manager

    return db_manager


class MotorRed:
    """Fachada: estado + convertir MAESTRA / ESCLAVA."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def obtener_estado_red(self):
        db_manager = _db_manager()
        return {
            "is_master": getattr(db_manager, "is_master", True),
            "caja_id": config.get("caja_id", 1),
            "db_engine": getattr(db_manager, "db_engine_type", "sqlite"),
            "db_host": config.get("db_host", "") or "localhost",
            "descubrimiento_udp_puerto": 37020,
        }

    def convertir_en_maestra(self):
        return convertir_en_maestra(self.logger)

    def convertir_en_esclava(self, ip_maestra):
        return convertir_en_esclava(self.logger, ip_maestra)
