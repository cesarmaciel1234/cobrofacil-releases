# -*- coding: utf-8 -*-
from src.base_de_datos.database import DatabaseManager

def calcular_ganancia_parcial(desde_str: str, hasta_str: str) -> float:
    """
    Calcula la ganancia SOLO de los productos que tienen costo cargado en inventario.
    Ignora las ventas que no tienen id_producto asociado o cuyo costo es 0 o NULL.
    Esto evita inflar la ganancia con productos a los que no se les asignó costo.
    """
    db = DatabaseManager()
    
    query = '''
    SELECT dv.cantidad, dv.precio_unitario, p.costo 
    FROM detalles_ventas dv
    JOIN ventas v ON dv.id_venta = v.id
    JOIN productos p ON dv.id_producto = p.id
    WHERE (v.estado IS NULL OR UPPER(TRIM(v.estado)) NOT IN ('CANCELADA','ANULADA','CANCELADO','ANULADO'))
      AND v.fecha >= ? AND v.fecha <= ?
      AND p.costo IS NOT NULL AND p.costo > 0
    '''
    res = db.execute_query(query, (desde_str, hasta_str))
    
    if not res:
        return 0.0
        
    ganancia_total = 0.0
    for row in res:
        try:
            cantidad = float(row["cantidad"] or 0)
            precio_venta = float(row["precio_unitario"] or 0)
            costo = float(row["costo"] or 0)
            
            venta_total = cantidad * precio_venta
            costo_total = cantidad * costo
            ganancia_total += (venta_total - costo_total)
        except:
            pass
            
    return ganancia_total
