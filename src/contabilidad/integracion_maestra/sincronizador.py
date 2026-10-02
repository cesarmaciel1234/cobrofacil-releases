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
        Tambien importa el Costo de Mercaderia vendida en el dia.
        """
        if not fecha:
            fecha = date.today()
        
        fecha_str = fecha.strftime("%Y-%m-%d")
        fecha_str_like = f"{fecha_str}%"
        
        logger.info(f"Sincronizando ventas del {fecha_str} desde la base Maestra...")

        try:
            # 1. Limpiar ingresos y costos previos de la misma fecha importados automaticamente
            self.db_contabilidad.execute_query(
                "DELETE FROM income WHERE date = ? AND source = 'Ventas TPV'",
                (fecha_str,)
            )
            self.db_contabilidad.execute_query(
                "DELETE FROM expenses WHERE date = ? AND description = 'Costo de Ventas TPV'",
                (fecha_str,)
            )

            # 2. Traer Ventas (Ingresos)
            query_ventas = """
                SELECT 
                    COALESCE(metodo_pago, 'Efectivo') as m_pago, 
                    SUM(total) as total
                FROM ventas 
                WHERE fecha LIKE ? AND estado IN ('COMPLETADA', 'CERRADA')
                GROUP BY m_pago
            """
            resultados = db_maestra.execute_query(query_ventas, (fecha_str_like,))
            
            ventas_existen = False
            if resultados:
                ventas_existen = True
                for fila in resultados:
                    m_pago = fila.get('m_pago', 'Desconocido')
                    total = float(fila.get('total', 0.0))
                    
                    self.db_contabilidad.add_income(
                        date=fecha_str,
                        amount=total,
                        description=f"Ventas del día - {m_pago}",
                        source="Ventas TPV"
                    )

            # 3. Traer Costos de Mercaderia (Egresos/Costo)
            query_costos = """
                SELECT SUM(dv.cantidad * p.costo) as costo_total
                FROM detalles_ventas dv
                JOIN ventas v ON dv.id_venta = v.id
                JOIN productos p ON dv.id_producto = p.id
                WHERE v.fecha LIKE ? AND v.estado IN ('COMPLETADA', 'CERRADA')
                  AND p.costo IS NOT NULL AND p.costo > 0
            """
            res_costos = db_maestra.execute_query(query_costos, (fecha_str_like,))
            if res_costos and res_costos[0] and res_costos[0].get('costo_total'):
                costo_total = float(res_costos[0]['costo_total'])
                if costo_total > 0:
                    self.db_contabilidad.add_expense(
                        date=fecha_str,
                        amount=costo_total,
                        category="Mercadería",
                        description="Costo de Ventas TPV"
                    )
            
            if ventas_existen:
                logger.info(f"Sincronización de ventas y costos de {fecha_str} exitosa.")
                return True
            else:
                logger.info("No hay ventas para sincronizar en esa fecha.")
                return False
                
        except Exception as e:
            logger.error(f"Error al sincronizar ventas: {e}")
            return False

    def traer_retiros_y_cierres(self, fecha: date = None):
        """
        Lee los movimientos de caja (retiros, faltantes) de MariaDB
        y los inyecta como Gastos o Ingresos Extra en Contabilidad.
        """
        pass
