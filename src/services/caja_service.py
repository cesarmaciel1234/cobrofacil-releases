from src.database import db_manager
from src.logger import logger
from datetime import datetime

def verificar_y_realizar_autocierre():
    """
    Busca ventas de días anteriores que hayan quedado en estado 'COMPLETADA' 
    y las cierra automáticamente para garantizar la integridad de los reportes diarios.
    """
    try:
        from datetime import datetime
        # Obtenemos la fecha de hoy a las 00:00:00 para comparar
        hoy_inicio = datetime.now().strftime("%Y-%m-%d 00:00:00")
        
        # Buscamos si hay ventas de días pasados sin cerrar
        query_check = "SELECT COUNT(*) FROM ventas WHERE estado = 'COMPLETADA' AND fecha < ?"
        pendientes = db_manager.execute_scalar(query_check, (hoy_inicio,))
        
        if pendientes and pendientes > 0:
            logger.info(f"Detectadas {pendientes} ventas de días anteriores sin cerrar. Ejecutando auto-cierre...")
            
            # 1. Obtener totales para el registro
            query_stats = """
                SELECT SUM(total) as t, SUM(pago_otro) as tarj 
                FROM ventas 
                WHERE estado = 'COMPLETADA' AND fecha < ?
            """
            stats = db_manager.execute_query(query_stats, (hoy_inicio,))
            total_pend = stats[0]['t'] or 0
            tarj_pend = stats[0]['tarj'] or 0
            
            # 2. Registrar el movimiento de auditoría
            db_manager.execute_non_query(
                "INSERT INTO movimientos_caja (fecha, tipo, monto, usuario, observaciones) VALUES (?, 'CIERRE_AUTO', 0, 'SISTEMA', ?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                 f"Auto-cierre de {pendientes} ventas olvidadas. Total: ${float(total_pend):.2f}")
            )
            
            # 3. Cerrar las ventas
            db_manager.execute_non_query(
                "UPDATE ventas SET estado = 'CERRADA' WHERE estado = 'COMPLETADA' AND fecha < ?",
                (hoy_inicio,)
            )
            
            return True, total_pend
    except Exception as e:
        logger.error(f"Error en auto-cierre: {e}")
        
    return False, 0
