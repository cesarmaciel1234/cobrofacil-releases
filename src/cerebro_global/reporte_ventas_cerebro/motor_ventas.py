import sqlite3
import datetime
from src.base_de_datos.database import db_manager

class MotorVentas:
    """
    Cerebro Central de Reportes y Ventas.
    Sirve tanto para la UI del Jefe (Reportes) como para la Cartelería Inteligente.
    Extrae datos REALES de la base de datos sin sobrecargar la interfaz gráfica.
    """
    
    @staticmethod
    def get_personas_viendo(periodo="hoy"):
        """
        Devuelve la cantidad de tickets (ventas) generadas.
        Se usa en la Cartelería para decir 'X personas compraron/viendo esto'.
        """
        try:
            today = datetime.date.today()
            if periodo == "hoy":
                start_date = today.strftime('%Y-%m-%d 00:00:00')
            else:
                # "mes"
                start_date = today.replace(day=1).strftime('%Y-%m-%d 00:00:00')
                
            conn = db_manager.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM ventas WHERE fecha >= ? AND estado = 'COMPLETADA'",
                    (start_date,)
                )
                res = cursor.fetchone()
                return res[0] if res else 0
            finally:
                if hasattr(conn, 'close'):
                    conn.close()
        except Exception as e:
            print(f"Error en get_personas_viendo: {e}")
            return 0

    @staticmethod
    def get_unidades_vendidas(nombre_producto, periodo="mes"):
        """
        Devuelve cuántas unidades (o kilos) se vendieron de un producto específico.
        """
        try:
            today = datetime.date.today()
            if periodo == "hoy":
                start_date = today.strftime('%Y-%m-%d 00:00:00')
            else:
                start_date = today.replace(day=1).strftime('%Y-%m-%d 00:00:00')
                
            conn = db_manager.get_connection()
            try:
                cursor = conn.cursor()
                # Join with ventas to filter by date and state
                cursor.execute("""
                    SELECT SUM(dv.cantidad) 
                    FROM detalles_ventas dv
                    JOIN ventas v ON dv.id_venta = v.id
                    WHERE v.fecha >= ? AND v.estado = 'COMPLETADA'
                    AND dv.nombre_producto = ?
                """, (start_date, nombre_producto))
                res = cursor.fetchone()
                return float(res[0]) if res and res[0] else 0.0
            finally:
                if hasattr(conn, 'close'):
                    conn.close()
        except Exception as e:
            print(f"Error en get_unidades_vendidas: {e}")
            return 0.0

    @staticmethod
    def get_top_ventas(limit=5, periodo="mes"):
        """
        Calcula el Top de productos más vendidos en cantidad.
        Retorna lista de diccionarios: [{'nombre': 'Lomo', 'cantidad': 120.5, 'recaudacion': 50000}]
        """
        try:
            today = datetime.date.today()
            if periodo == "hoy":
                start_date = today.strftime('%Y-%m-%d 00:00:00')
            else:
                start_date = today.replace(day=1).strftime('%Y-%m-%d 00:00:00')
                
            conn = db_manager.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT dv.nombre_producto, SUM(dv.cantidad) as total_cant, SUM(dv.subtotal) as total_recaudacion
                    FROM detalles_ventas dv
                    JOIN ventas v ON dv.id_venta = v.id
                    WHERE v.fecha >= ? AND v.estado = 'COMPLETADA'
                    GROUP BY dv.nombre_producto
                    ORDER BY total_cant DESC
                    LIMIT ?
                """, (start_date, limit))
                
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    results.append({
                        "nombre": row[0],
                        "cantidad": float(row[1] or 0),
                        "recaudacion": float(row[2] or 0)
                    })
                return results
            finally:
                if hasattr(conn, 'close'):
                    conn.close()
        except Exception as e:
            print(f"Error en get_top_ventas: {e}")
            return []

motor_ventas = MotorVentas()
