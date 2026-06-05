from src.base_de_datos.database import DatabaseManager

db = DatabaseManager()

# Limpiar tablas
print("[*] Limpiando tablas...")
db.execute_non_query("TRUNCATE TABLE detalles_ventas")
db.execute_non_query("TRUNCATE TABLE ventas")
db.execute_non_query("TRUNCATE TABLE clientes")

print("✓ Tablas limpias")

# Ver conteos
print("Clientes:", db.execute_scalar('SELECT COUNT(*) FROM clientes'))
print("Ventas:", db.execute_scalar('SELECT COUNT(*) FROM ventas'))
print("Detalles:", db.execute_scalar('SELECT COUNT(*) FROM detalles_ventas'))
