from src.base_de_datos.database import db_manager
conn = db_manager.get_connection()
cur = conn.cursor()
cur.execute('DELETE FROM ventas')
conn.commit()
print('Ventas limpias')
