from datetime import datetime
from src.base_de_datos.database import db_manager
from src.config import config

class CajaController:
    """Controlador para la lógica de apertura y configuración inicial de caja."""

    def __init__(self):
        pass

    def abrir_caja(self, monto: float) -> bool:
        """Registra la apertura de caja en la base de datos."""
        usuario = config.current_user.get("username", "cajero") if config.current_user else "cajero"
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c_id = config.get("caja_id", 1)
        
        # Último movimiento relevante: tras CIERRE_TURNO / Z / AUTO → nueva APERTURA
        mov = db_manager.execute_query(
            "SELECT id, tipo FROM movimientos_caja WHERE caja_id = ? AND tipo IN "
            "('APERTURA', 'CIERRE_Z', 'CIERRE_AUTO', 'CIERRE_TURNO') ORDER BY id DESC LIMIT 1",
            (c_id,),
        )
        if mov and mov[0]["tipo"] == "APERTURA":
            # Caja ya abierta (reinicio/crash): NO TOCAR LA FECHA ORIGINAL
            # Si actualizamos la fecha, todas las ventas anteriores al reinicio quedan excluidas del corte.
            last_id = mov[0]["id"]
            db_manager.execute_non_query(
                "UPDATE movimientos_caja SET monto = ?, usuario = ?, observaciones = 'Reapertura por reinicio/crash' WHERE id = ?",
                (monto, usuario, last_id),
            )
        else:
            db_manager.execute_non_query(
                "INSERT INTO movimientos_caja (fecha, tipo, monto, usuario, observaciones, caja_id) VALUES (?, 'APERTURA', ?, ?, 'Inicio', ?)",
                (fecha, monto, usuario, c_id),
            )
        return True
