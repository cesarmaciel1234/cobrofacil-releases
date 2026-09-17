import logging
from datetime import datetime
from src.base_de_datos.database import db_manager

logger = logging.getLogger('PunPro.MotorTurnos')

class GestorTurnos:
    @staticmethod
    def iniciar_o_reanudar_turno(usuario: str, rol: str, caja_id: int, monto_inicial: float = 0.0) -> bool:
        \"\"\"
        Maneja el inicio de sesión operativo.
        Retorna True si es una APERTURA fresca (requiere pedir monto),
        o False si se reanuda un turno existente o es Admin (no pide monto).
        \"\"\"
        if rol in ('admin', 'jefe', 'super'):
            # El Jefe no abre caja, audita.
            fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            try:
                db_manager.execute_non_query(
                    \"INSERT INTO movimientos_caja (fecha, tipo, monto, usuario, observaciones, caja_id) \"
                    \"VALUES (?, 'INTERVENCION', 0, ?, 'Inicio de sesión de Supervisor', ?)\",
                    (fecha, usuario, caja_id)
                )
                logger.info(f"Intervención de Supervisor registrada: {usuario} en Caja {caja_id}")
            except Exception as e:
                logger.error(f"Error registrando intervención de jefe: {e}")
            return False # No requiere pedir saldo inicial
            
        # Lógica para Cajeros (Buscar si tienen turno abierto HOY)
        hoy_inicio = datetime.now().strftime('%Y-%m-%d 00:00:00')
        
        mov = db_manager.execute_query(
            \"SELECT id, tipo, usuario FROM movimientos_caja \"
            \"WHERE caja_id = ? AND tipo IN ('APERTURA', 'CIERRE_Z', 'CIERRE_AUTO', 'CIERRE_TURNO') \"
            \"AND fecha >= ? ORDER BY id DESC LIMIT 1\",
            (caja_id, hoy_inicio)
        )
        
        if mov and mov[0]['tipo'] == 'APERTURA':
            if mov[0]['usuario'].lower() == usuario.lower():
                logger.info(f"Reanudando turno abierto para el cajero {usuario} en caja {caja_id}")
                return False
            else:
                logger.warning(f"La caja {caja_id} está abierta por {mov[0]['usuario']}. {usuario} está entrando.")
                return True 
                
        return True

    @staticmethod
    def registrar_apertura_caja(usuario: str, caja_id: int, monto: float):
        \"\"\"
        Registra físicamente la apertura tras confirmar el monto.
        \"\"\"
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            mov = db_manager.execute_query(
                \"SELECT id, tipo FROM movimientos_caja WHERE caja_id = ? AND tipo IN \"
                \"('APERTURA', 'CIERRE_Z', 'CIERRE_AUTO', 'CIERRE_TURNO') ORDER BY id DESC LIMIT 1\",
                (caja_id,)
            )
            if mov and mov[0]["tipo"] == "APERTURA":
                last_id = mov[0]["id"]
                db_manager.execute_non_query(
                    \"UPDATE movimientos_caja SET monto = ?, usuario = ?, observaciones = 'Reapertura por reinicio/crash' WHERE id = ?\",
                    (monto, usuario, last_id)
                )
                logger.info(f"Reapertura/Sobrescritura de turno por {usuario} en Caja {caja_id} con ")
            else:
                db_manager.execute_non_query(
                    \"INSERT INTO movimientos_caja (fecha, tipo, monto, usuario, observaciones, caja_id) \"
                    \"VALUES (?, 'APERTURA', ?, ?, 'Inicio', ?)\",
                    (fecha, monto, usuario, caja_id)
                )
                logger.info(f"Turno abierto por {usuario} en Caja {caja_id} con ")
        except Exception as e:
            logger.error(f"Error al registrar apertura: {e}")
