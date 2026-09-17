import logging
from datetime import datetime
from src.base_de_datos.database import db_manager
from src import config

logger = logging.getLogger("PunPro.CajaController")

class CajaController:
    def __init__(self):
        pass

    def abrir_caja(self, monto: float) -> bool:
        \"\"\"Registra la apertura de caja en la base de datos a través del Motor de Turnos.\"\"\"
        usuario = config.current_user.get("username", "cajero") if config.current_user else "cajero"
        c_id = config.get("caja_id", 1)
        
        from src.motor_turnos.nucleo.gestor_turnos import GestorTurnos
        GestorTurnos.registrar_apertura_caja(usuario, c_id, monto)
        return True
