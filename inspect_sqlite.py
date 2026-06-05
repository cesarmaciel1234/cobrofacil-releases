import sqlite3

conn = sqlite3.connect('AQVGI.db')
c = conn.cursor()

print("=== ESTRUCTURA DE CLIENTES ===")
c.execute("PRAGMA table_info(clientes)")
for row in c.fetchall():
    print(row)

print("\n=== ESTRUCTURA DE VENTAS ===")
c.execute("PRAGMA table_info(ventas)")
for row in c.fetchall():
    print(row)

print("\n=== ESTRUCTURA DE DETALLES_VENTAS ===")
c.execute("PRAGMA table_info(detalles_ventas)")
for row in c.fetchall():
    print(row)

# Ver algunos datos de ejemplo
print("\n=== MUESTRA DE CLIENTES ===")
c.execute("SELECT * FROM clientes LIMIT 1")
print(c.fetchone())

print("\n=== MUESTRA DE VENTAS ===")
c.execute("SELECT * FROM ventas LIMIT 1")
print(c.fetchone())

print("\n=== MUESTRA DE DETALLES_VENTAS ===")
c.execute("SELECT * FROM detalles_ventas LIMIT 1")
print(c.fetchone())

conn.close()
