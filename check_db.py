import json
import sys

def check_db():
    sys.path.append(r"C:\Users\cesar\OneDrive\Desktop\tpv pro 2026")
    from src.base_de_datos.database import DatabaseManager
    db = DatabaseManager()
    productos = db.execute_query("SELECT nombre FROM productos LIMIT 500")
    print(json.dumps([p['nombre'] for p in productos], indent=2))

if __name__ == '__main__':
    check_db()
