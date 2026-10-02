import logging
from datetime import date
from src.base_de_datos.database import db_manager as db_maestra
from src.contabilidad.database import Database

logger = logging.getLogger(__name__)

class SincronizadorMaestra:
    """
    Se encarga de leer de MariaDB (la TPV) e insertar en la base de Contabilidad.
    """
    def __init__(self, db_contabilidad: Database):
        self.db_contabilidad = db_contabilidad

    def traer_ventas_del_dia(self, fecha: date = None):
        """
        Agrupa las ventas de la TPV de una fecha (o de hoy) por medio de pago, 
        y las inyecta como Ingresos en Contabilidad.
        """
        if not fecha:
            fecha = date.today()
        
        fecha_str = fecha.strftime("%Y-%m-%d")
        fecha_str_like = f"{fecha_str}%"
        
        logger.info(f"Sincronizando ventas del {fecha_str} desde la base Maestra...")

        try:
            # Query para agrupar ventas por método de pago del día
            query = """
                SELECT 
                    COALESCE(metodo_pago, 'Efectivo') as m_pago, 
                    SUM(total) as total
                FROM ventas 
                WHERE fecha LIKE ? AND estado IN ('COMPLETADA', 'CERRADA')
                GROUP BY m_pago
            """
            resultados = db_maestra.execute_query(query, (fecha_str_like,))
            
            if not resultados:
                logger.info("No hay ventas para sincronizar en esa fecha.")
                return True
                
            for fila in resultados:
                m_pago = fila.get('m_pago', 'Desconocido')
                total = float(fila.get('total', 0.0))
                
                # Insertamos en la base de datos de contabilidad
                self.db_contabilidad.add_income(
                    date=fecha_str,
                    amount=total,
                    description=f"Ventas del día - {m_pago}",
                    source="Ventas TPV"
                )
            
            logger.info(f"Sincronización de ventas de {fecha_str} exitosa.")
            return True
        except Exception as e:
            logger.error(f"Error al sincronizar ventas: {e}")
            return False

    def traer_retiros_y_cierres(self, fecha: date = None):
        """
        Lee los movimientos de caja (retiros, faltantes) de MariaDB
        y los inyecta como Gastos o Ingresos Extra en Contabilidad.
        """
        pass
