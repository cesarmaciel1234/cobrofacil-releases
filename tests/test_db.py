import sys, os
sys.path.insert(0, r'C:\Users\cesar\OneDrive\Desktop\tpv pro 2026')
from src.base_de_datos.database import DatabaseManager

db = DatabaseManager()
print('is_mariadb:', getattr(db, 'db_engine_type', 'sqlite') == 'mariadb')

query_g = """
    SELECT nombre, precio, precio_oferta 
    FROM productos 
    WHERE precio >= ? AND precio <= ? AND precio > 0
    AND (nombre LIKE '%carbón%' OR nombre LIKE '%carbon%' OR nombre LIKE '%salsa%' OR nombre LIKE '%chorizo%')
    LIMIT 3
"""
try:
    res = db.execute_query(query_g, (0, 99999))
    print('Result of execution (params=(0,99999)):', res is not None)
except Exception as e:
    print('Failed with params:', e)

try:
    query_a = "SELECT nombre, precio FROM productos WHERE nombre LIKE '%carbón%' LIMIT 1"
    res2 = db.execute_query(query_a, ())
    print('Result of execution (params=()):', res2 is not None)
except Exception as e:
    print('Failed without params:', e)
