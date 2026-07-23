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
                if not res: return 0
                if isinstance(res, dict): return int(list(res.values())[0])
                return int(res[0])
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
                if not res: return 0.0
                val = list(res.values())[0] if isinstance(res, dict) else res[0]
                return float(val) if val else 0.0
            finally:
                if hasattr(conn, 'close'):
                    conn.close()
        except Exception as e:
            print(f"Error en get_unidades_vendidas: {e}")
            return 0.0

    @staticmethod
    def get_top_ventas(limit=5, periodo="mes", modo="volumen"):
        """
        Calcula el Top de productos más vendidos.
        modo='volumen': Suma de cantidad (kilos/unidades)
        modo='frecuencia': Cuenta en cuántos tickets apareció
        Retorna lista de diccionarios: [{'nombre': 'Lomo', 'cantidad': 120.5, 'recaudacion': 50000}]
        """
        try:
            today = datetime.date.today()
            if periodo == "hoy":
                start_date = today.strftime('%Y-%m-%d 00:00:00')
            else:
                start_date = today.replace(day=1).strftime('%Y-%m-%d 00:00:00')
                
            if modo == "frecuencia":
                query = """
                    SELECT dv.nombre_producto, COUNT(DISTINCT dv.id_venta) as total_cant, SUM(dv.subtotal) as total_recaudacion
                    FROM detalles_ventas dv
                    JOIN ventas v ON dv.id_venta = v.id
                    WHERE v.fecha >= ? AND v.estado = 'COMPLETADA'
                    GROUP BY dv.nombre_producto
                    ORDER BY total_cant DESC
                    LIMIT ?
                """
            elif modo == "clavos":
                # Productos menos vendidos (o con stock que no salen)
                query = """
                    SELECT dv.nombre_producto, SUM(dv.cantidad) as total_cant, SUM(dv.subtotal) as total_recaudacion
                    FROM detalles_ventas dv
                    JOIN ventas v ON dv.id_venta = v.id
                    WHERE v.fecha >= ? AND v.estado = 'COMPLETADA'
                    GROUP BY dv.nombre_producto
                    ORDER BY total_cant ASC
                    LIMIT ?
                """
            else:
                query = """
                    SELECT dv.nombre_producto, SUM(dv.cantidad) as total_cant, SUM(dv.subtotal) as total_recaudacion
                    FROM detalles_ventas dv
                    JOIN ventas v ON dv.id_venta = v.id
                    WHERE v.fecha >= ? AND v.estado = 'COMPLETADA'
                    GROUP BY dv.nombre_producto
                    ORDER BY total_cant DESC
                    LIMIT ?
                """
            
            rows = db_manager.execute_query(query, (start_date, limit))
            
            results = []
            if not rows: return results
            
            for row in rows:
                if isinstance(row, dict):
                    nombre = row.get("nombre_producto") or row.get("nombre") or list(row.values())[0]
                    cantidad = row.get("total_cant") or row.get("cantidad") or list(row.values())[1]
                    recaudacion = row.get("total_recaudacion") or row.get("recaudacion") or list(row.values())[2]
                    results.append({
                        "nombre": str(nombre),
                        "cantidad": float(cantidad or 0),
                        "recaudacion": float(recaudacion or 0)
                    })
                else:
                    results.append({
                        "nombre": row[0],
                        "cantidad": float(row[1] or 0),
                        "recaudacion": float(row[2] or 0)
                    })
            return results
        except Exception as e:
            print(f"Error en get_top_ventas: {e}")
            return []

motor_ventas = MotorVentas()
