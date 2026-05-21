from src.database import db_manager
from src.logger import logger
from datetime import datetime

def verificar_y_realizar_autocierre():
    """
    Busca ventas de días anteriores que hayan quedado en estado 'COMPLETADA' 
    y las cierra automáticamente para garantizar la integridad de los reportes diarios.
    """
    try:
        # Buscamos si hay ventas de días pasados sin cerrar
        query_check = "SELECT COUNT(*) FROM ventas WHERE estado = 'COMPLETADA' AND date(fecha) < date('now', 'localtime')"
        pendientes = db_manager.execute_scalar(query_check)
        
        if pendientes and pendientes > 0:
            logger.info(f"Detectadas {pendientes} ventas de días anteriores sin cerrar. Ejecutando auto-cierre...")
            
            # 1. Obtener totales para el registro
            query_stats = """
                SELECT SUM(total) as t, SUM(pago_otro) as tarj 
                FROM ventas 
                WHERE estado = 'COMPLETADA' AND date(fecha) < date('now', 'localtime')
            """
            stats = db_manager.execute_query(query_stats)
            total_pend = stats[0]['t'] or 0
            tarj_pend = stats[0]['tarj'] or 0
            
            # 2. Registrar el movimiento de auditoría
            db_manager.execute_non_query(
                "INSERT INTO movimientos_caja (fecha, tipo, monto, usuario, observaciones) VALUES (?, 'CIERRE_AUTO', 0, 'SISTEMA', ?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                 f"Auto-cierre de {pendientes} ventas olvidadas. Total: ${total_pend:.2f}")
            )
            
            # 3. Cerrar las ventas
            db_manager.execute_non_query(
                "UPDATE ventas SET estado = 'CERRADA' WHERE estado = 'COMPLETADA' AND date(fecha) < date('now', 'localtime')"
            )
            
            return True, total_pend
    except Exception as e:
        logger.error(f"Error en auto-cierre: {e}")
        
    return False, 0
