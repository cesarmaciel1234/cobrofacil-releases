import sys
sys.path.append('src')
from utils.db import db_manager

query = """
SELECT v.id, v.fecha, v.usuario, p.departamento, dv.nombre_producto,
       dv.cantidad, p.unidad AS unidad_medida, dv.precio_unitario, dv.subtotal,
       v.metodo_pago, v.estado
FROM ventas v
JOIN detalles_ventas dv ON dv.id_venta = v.id
LEFT JOIN productos p ON dv.id_producto = p.id
ORDER BY v.id DESC LIMIT 50 OFFSET 0
"""
rows = db_manager.execute_query(query)
print('Length:', len(rows) if rows else 0)
if rows: 
    print(rows[0])
