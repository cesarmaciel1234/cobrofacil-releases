import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.base_de_datos.database import DatabaseManager

db = DatabaseManager()

# Limpiar tablas
print("[*] Limpiando tablas...")
# First delete child tables
db.execute_non_query("DELETE FROM cuenta_corriente")
db.execute_non_query("DELETE FROM detalles_ventas")
# Then delete parent tables
db.execute_non_query("DELETE FROM ventas")
db.execute_non_query("DELETE FROM clientes")
db.execute_non_query("DELETE FROM productos")
db.execute_non_query("DELETE FROM departamentos")

print("OK Tablas limpias")

# Ver conteos
print("Clientes:", db.execute_scalar('SELECT COUNT(*) FROM clientes'))
print("Ventas:", db.execute_scalar('SELECT COUNT(*) FROM ventas'))
print("Detalles:", db.execute_scalar('SELECT COUNT(*) FROM detalles_ventas'))
print("Productos:", db.execute_scalar('SELECT COUNT(*) FROM productos'))
print("Departamentos:", db.execute_scalar('SELECT COUNT(*) FROM departamentos'))
