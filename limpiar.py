from src.base_de_datos.database import db_manager
from src.logger import logger

def limpiar_pruebas():
    # Forced to ensure we clean BOTH MariaDB and SQLite if needed
    tablas_transaccionales = [
        "ventas",
        "detalles_ventas",
        "detalle_ventas",
        "gastos",
        "romaneos",
        "romaneo_items",
        "movimientos_caja",
        "auditoria_cancelaciones",
        "mp_transferencias_usadas",
        "historial_promedios"
    ]
    
    conn = db_manager.get_connection()
    cur = conn.cursor()
    
    # We use DELETE FROM instead of TRUNCATE to be safe on both SQLite and MariaDB
    for t in tablas_transaccionales:
        try:
            cur.execute(f"DELETE FROM {t}")
            print(f"Limpiado: {t}")
        except Exception as e:
            print(f"Error limpiando {t}: {e}")
            
    conn.commit()
    print("Base de datos local limpia de transacciones de prueba.")

if __name__ == '__main__':
    limpiar_pruebas()
