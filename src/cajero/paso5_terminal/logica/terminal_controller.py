from src.base_de_datos.database import db_manager
from .carrito_service import CarritoService
from .stock_ofertas_service import StockOfertasService
from .movimientos_caja_service import MovimientosCajaService
from .cierre_remoto_service import CierreRemotoService

class TerminalController:
    """
    Controlador (Presenter) para la Terminal Paso 5.
    Maneja la lógica de negocio pura delegándola a servicios especializados.
    """
    def __init__(self, view):
        self.view = view
        self.carrito = CarritoService()
        self.stock_ofertas = StockOfertasService()
        self.movimientos_caja = MovimientosCajaService()
        self.cierre_remoto = CierreRemotoService()

    def get_db_path(self):
        return db_manager.db_path.lower()

    def registrar_heartbeat(self, caja_id, hostname):
        db_manager.registrar_heartbeat(caja_id, hostname)

    def get_terminales_activos_count(self):
        return db_manager.get_terminales_activos_count()

    def get_db_engine_info(self):
        engine = getattr(db_manager, "db_engine_type", "mariadb") or "mariadb"
        host = getattr(getattr(db_manager, "mariadb_engine", None), "host", None) or "localhost"
        return engine, host
