import codecs

with codecs.open('src/admin/admin3_reportes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix Cajero query
bad_cajero_query = '''            res_cajeros = db_manager.execute_query(
                "SELECT COALESCE(u.username, v.cajero) as cajero, COUNT(v.id) as cant, SUM(v.total) as tot "
                "FROM ventas v LEFT JOIN usuarios u ON v.id_usuario = u.id "
                "WHERE (v.fecha BETWEEN ? AND ?) AND v.estado IN ('COMPLETADA', 'CERRADA') "
                "GROUP BY cajero ORDER BY tot DESC LIMIT 5", (start_str, end_str)
            )'''
good_cajero_query = '''            res_cajeros = db_manager.execute_query(
                "SELECT COALESCE(v.usuario, 'Desconocido') as cajero, COUNT(v.id) as cant, SUM(v.total) as tot "
                "FROM ventas v "
                "WHERE (v.fecha BETWEEN ? AND ?) AND v.estado IN ('COMPLETADA', 'CERRADA') "
                "GROUP BY cajero ORDER BY tot DESC LIMIT 5", (start_str, end_str)
            )'''

content = content.replace(bad_cajero_query, good_cajero_query)

# Fix Producto query
bad_producto_query = '''            res_productos = db_manager.execute_query(
                "SELECT p.nombre, SUM(dv.cantidad) as cant, SUM(dv.subtotal) as tot "
                "FROM detalles_ventas dv JOIN ventas v ON dv.id_venta = v.id "
                "JOIN productos p ON dv.id_producto = p.id "
                "WHERE (v.fecha BETWEEN ? AND ?) AND v.estado IN ('COMPLETADA', 'CERRADA') "
                "GROUP BY p.id ORDER BY tot DESC LIMIT 5", (start_str, end_str)
            )'''
good_producto_query = '''            res_productos = db_manager.execute_query(
                "SELECT dv.nombre_producto as nombre, SUM(dv.cantidad) as cant, SUM(dv.subtotal) as tot "
                "FROM detalles_ventas dv JOIN ventas v ON dv.id_venta = v.id "
                "WHERE (v.fecha BETWEEN ? AND ?) AND v.estado IN ('COMPLETADA', 'CERRADA') "
                "GROUP BY dv.nombre_producto ORDER BY tot DESC LIMIT 5", (start_str, end_str)
            )'''

content = content.replace(bad_producto_query, good_producto_query)

with codecs.open('src/admin/admin3_reportes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Queries fixed successfully!")
