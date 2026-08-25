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
            elif periodo == "semana":
                start_date = (today - datetime.timedelta(days=7)).strftime('%Y-%m-%d 00:00:00')
            else:
                # Ventana móvil de 30 días reales
                start_date = (today - datetime.timedelta(days=30)).strftime('%Y-%m-%d 00:00:00')
                
            query = "SELECT COUNT(*) FROM ventas WHERE fecha >= ? AND COALESCE(estado, '') != 'CANCELADA'"
            rows = db_manager.execute_query(query, (start_date,))
            if not rows: return 0
            res = rows[0]
            if isinstance(res, dict): return int(list(res.values())[0])
            return int(res[0])
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
            elif periodo == "semana":
                start_date = (today - datetime.timedelta(days=7)).strftime('%Y-%m-%d 00:00:00')
            else:
                start_date = (today - datetime.timedelta(days=30)).strftime('%Y-%m-%d 00:00:00')
                
            query = """
                SELECT SUM(dv.cantidad) 
                FROM detalles_ventas dv
                JOIN ventas v ON dv.id_venta = v.id
                WHERE v.fecha >= ? AND COALESCE(v.estado, '') != 'CANCELADA'
                AND dv.nombre_producto = ?
            """
            rows = db_manager.execute_query(query, (start_date, nombre_producto))
            if not rows: return 0.0
            res = rows[0]
            val = list(res.values())[0] if isinstance(res, dict) else res[0]
            return float(val) if val else 0.0
        except Exception as e:
            print(f"Error en get_unidades_vendidas: {e}")
            return 0.0

    @staticmethod
    def _rango_periodo(periodo="mes"):
        today = datetime.date.today()
        maniana = today + datetime.timedelta(days=1)
        if periodo == "hoy":
            inicio = today
            fin = maniana
        elif periodo == "ayer":
            inicio = today - datetime.timedelta(days=1)
            fin = today
        elif periodo == "semana":
            inicio = today - datetime.timedelta(days=7)
            fin = maniana
        else:
            inicio = today - datetime.timedelta(days=30)
            fin = maniana
        return (
            inicio.strftime("%Y-%m-%d 00:00:00"),
            fin.strftime("%Y-%m-%d 00:00:00"),
        )

    @staticmethod
    def get_top_ventas(limit=5, periodo="mes", modo="volumen"):
        """
        Calcula el Top de productos más vendidos.
        modo='volumen': Suma de cantidad (kilos/unidades)
        modo='frecuencia': Cuenta en cuántos tickets apareció
        Retorna lista de diccionarios: [{'nombre': 'Lomo', 'cantidad': 120.5, 'recaudacion': 50000}]
        """
        try:
            start_date, end_date = MotorVentas._rango_periodo(periodo)
            filtro_fecha = "v.fecha >= ? AND v.fecha < ? AND COALESCE(v.estado, '') != 'CANCELADA'"

            if modo == "frecuencia":
                query = f"""
                    SELECT dv.nombre_producto, COUNT(DISTINCT dv.id_venta) as total_cant, SUM(dv.subtotal) as total_recaudacion
                    FROM detalles_ventas dv
                    JOIN ventas v ON dv.id_venta = v.id
                    WHERE {filtro_fecha}
                    GROUP BY dv.nombre_producto
                    ORDER BY total_cant DESC
                    LIMIT ?
                """
            elif modo == "clavos":
                query = f"""
                    SELECT dv.nombre_producto, SUM(dv.cantidad) as total_cant, SUM(dv.subtotal) as total_recaudacion
                    FROM detalles_ventas dv
                    JOIN ventas v ON dv.id_venta = v.id
                    WHERE {filtro_fecha}
                    GROUP BY dv.nombre_producto
                    ORDER BY total_cant ASC
                    LIMIT ?
                """
            else:
                query = f"""
                    SELECT dv.nombre_producto, SUM(dv.cantidad) as total_cant, SUM(dv.subtotal) as total_recaudacion
                    FROM detalles_ventas dv
                    JOIN ventas v ON dv.id_venta = v.id
                    WHERE {filtro_fecha}
                    GROUP BY dv.nombre_producto
                    ORDER BY total_cant DESC
                    LIMIT ?
                """

            rows = db_manager.execute_query(query, (start_date, end_date, limit))
            
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
