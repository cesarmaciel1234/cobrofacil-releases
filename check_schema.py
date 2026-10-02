from src.base_de_datos.core.connection import db_connection

conn = db_connection.get_connection()
cursor = conn.cursor()

try:
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name IN ('ventas', 'caja_movimientos', 'caja', 'pagos');")
    for row in cursor.fetchall():
        print(row)
except Exception as e:
    pass

try:
    cursor.execute("SHOW CREATE TABLE ventas;")
    print("ventas:", cursor.fetchall())
except:
    pass

try:
    cursor.execute("SHOW CREATE TABLE caja_movimientos;")
    print("caja_movimientos:", cursor.fetchall())
except:
    pass
