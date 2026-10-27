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
        is_master = getattr(db_manager, "is_master", True)
        is_forced_offline = getattr(db_manager, "_forced_local_offline", False)
        host = config.get("db_host", "")
        if not host and hasattr(db_manager, "_host_tienda"):
            try:
                host = db_manager._host_tienda()
            except Exception:
                host = ""

        maestra_online = False
        if not is_master and host:
            try:
                maestra_online = db_manager._puerto_maestra_vivo(host)
            except Exception:
                maestra_online = False

        from src.base_de_datos.offline_sync import offline_sync_manager
        resumen_pend = offline_sync_manager.obtener_resumen_completo_pendientes()
        pendientes = resumen_pend.get("ventas", 0)

        return {
            "is_master": is_master,
            "is_forced_offline": is_forced_offline,
            "maestra_online": maestra_online,
            "ventas_pendientes": pendientes,
            "resumen_pendientes": resumen_pend,
            "caja_id": config.get("caja_id", 1),
            "db_engine": getattr(db_manager, "db_engine_type", "sqlite"),
            "db_host": host or "localhost",
            "descubrimiento_udp_puerto": 37020,
        }

    def convertir_en_maestra(self):
        return convertir_en_maestra(self.logger)

    def convertir_en_esclava(self, ip_maestra):
        return convertir_en_esclava(self.logger, ip_maestra)
