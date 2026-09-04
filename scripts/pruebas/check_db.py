import json
import sys

def check_db():
    sys.path.append(r"C:\Users\cesar\OneDrive\Desktop\tpv pro 2026")
    from src.base_de_datos.database import DatabaseManager
    from src.cerebro_global.auditoria.motor_auditoria import MotorAuditoria
    db = DatabaseManager()
    res = MotorAuditoria.obtener_inventario(db)
    print(f"Total: {len(res)}")
    if res:
        print(f"First row type: {type(res[0])}")
        print(f"First row: {dict(res[0]) if not isinstance(res[0], dict) else res[0]}")

if __name__ == '__main__':
    check_db()
