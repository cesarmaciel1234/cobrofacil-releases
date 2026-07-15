import time
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

class WorkerAnaliticaJefe(QThread):
    """
    Cerebro analítico del Jefe que se ejecuta en segundo plano.
    Calcula Ganancia Real y Valuación del Inventario usando los costos reales.
    No congela la UI (interfaz gráfica) gracias a QThread.
    """
    
    # Señal que emite un diccionario con los resultados cuando termina el proceso.
    datos_listos = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, fecha_inicio=None, fecha_fin=None):
        super().__init__()
        # Si no se pasan fechas, usamos el día de hoy por defecto
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.fecha_inicio = fecha_inicio if fecha_inicio else today_str
        self.fecha_fin = fecha_fin if fecha_fin else today_str

    def run(self):
        try:
            # 1. VALORIZACIÓN DEL INVENTARIO ACTUAL
            # Total de costo = Suma(stock * costo)
            # Total proyectado en venta = Suma(stock * precio)
            query_inventario = """
                SELECT 
                    SUM(stock * costo) as total_costo,
                    SUM(stock * precio) as total_venta
                FROM productos 
                WHERE stock > 0
            """
            res_inv = db_manager.execute_query(query_inventario)
            valor_costo = 0.0
            valor_venta = 0.0
            if res_inv and len(res_inv) > 0:
                row = res_inv[0]
                valor_costo = float(row.get("total_costo") or 0.0)
                valor_venta = float(row.get("total_venta") or 0.0)
                
            ganancia_proyectada_inventario = valor_venta - valor_costo

            # 2. GANANCIA REAL DE LAS VENTAS
            # Cruzamos detalles_ventas con productos (para obtener el costo real actual) y ventas (para filtrar completadas)
            query_ventas = """
                SELECT 
                    dv.cantidad,
                    dv.precio_unitario,
                    COALESCE(p.costo, 0) as costo
                FROM detalles_ventas dv
                JOIN ventas v ON dv.id_venta = v.id
                LEFT JOIN productos p ON dv.id_producto = p.codigo
                WHERE v.estado = 'COMPLETADA' 
                  AND date(v.fecha) >= ? 
                  AND date(v.fecha) <= ?
            """
            res_ventas = db_manager.execute_query(query_ventas, (self.fecha_inicio, self.fecha_fin))
            
            ganancia_real = 0.0
            total_ventas = 0.0
            total_costos_ventas = 0.0
            
            if res_ventas:
                for row in res_ventas:
                    cant = float(row.get("cantidad") or 0)
                    precio_v = float(row.get("precio_unitario") or 0)
                    costo_p = float(row.get("costo") or 0)
                    
                    ingreso = cant * precio_v
                    costo_total = cant * costo_p
                    ganancia = ingreso - costo_total
                    
                    total_ventas += ingreso
                    total_costos_ventas += costo_total
                    ganancia_real += ganancia

            # Empaquetamos resultados
            resultados = {
                "inventario_valor_costo": valor_costo,
                "inventario_valor_venta": valor_venta,
                "inventario_ganancia_proy": ganancia_proyectada_inventario,
                "ventas_total_ingresos": total_ventas,
                "ventas_total_costos": total_costos_ventas,
                "ventas_ganancia_real": ganancia_real,
                "periodo_inicio": self.fecha_inicio,
                "periodo_fin": self.fecha_fin
            }
            
            self.datos_listos.emit(resultados)

        except Exception as e:
            self.error.emit(str(e))
