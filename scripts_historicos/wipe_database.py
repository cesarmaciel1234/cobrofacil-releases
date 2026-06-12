import sys
sys.path.append('src')
from utils.db import db_manager

tables_to_truncate = [
    'categorias', 
    'clientes', 
    'cuenta_corriente', 
    'departamentos', 
    'detalles_ventas', 
    'gastos', 
    'movimientos_caja', 
    'productos', 
    'romaneo_items', 
    'romaneos', 
    'ventas',
    'sistema_estado'
]

try:
    db_manager.execute_non_query("SET FOREIGN_KEY_CHECKS = 0;")
    
    # First pass: delete data
    for table in tables_to_truncate:
        try:
            db_manager.execute_non_query(f"DELETE FROM {table};")
            print(f"Deleted rows from {table}")
        except Exception as e:
            print(f"Could not delete from {table}: {e}")

    # Second pass: reset auto increment
    for table in tables_to_truncate:
        try:
            db_manager.execute_non_query(f"ALTER TABLE {table} AUTO_INCREMENT = 1;")
            print(f"Reset AI for {table}")
        except Exception as e:
            pass

finally:
    db_manager.execute_non_query("SET FOREIGN_KEY_CHECKS = 1;")
    print("Database wipe complete.")

