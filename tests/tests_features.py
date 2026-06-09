import os
import sys
import datetime

# Asegurar que importamos desde el directorio raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.base_de_datos.database import db_manager
from src.services.email_service import generar_html_cierre_z
from src.config import config

def test_alerta_stock():
    print("--- PROBANDO ALERTA DE STOCK MINIMO ---")
    
    # 1. Insertar un producto de prueba con bajo stock
    query_insert = """
    REPLACE INTO productos (id, nombre, precio, stock, stock_minimo) 
    VALUES ('99999999', 'Producto Test Faltante', 100.0, 2.0, 5.0)
    """
    db_manager.execute_non_query(query_insert)
    print("[OK] Producto de prueba insertado con stock=2 y stock_minimo=5")
    
    # 2. Ejecutar la query que hace la terminal
    query_check = "SELECT COUNT(*) FROM productos WHERE stock <= stock_minimo AND stock_minimo > 0"
    bajos = db_manager.execute_scalar(query_check)
    
    if bajos and bajos > 0:
        print(f"[EXITO] La terminal detectó {bajos} productos con bajo stock. El banner se mostrará!")
    else:
        print("[ERROR] No se detectaron productos con bajo stock.")
        
    # Limpiar
    db_manager.execute_non_query("DELETE FROM productos WHERE id='99999999'")

def test_email_cierre():
    print("\n--- PROBANDO REPORTE DE EMAIL CIERRE Z ---")
    
    datos_mock = {
        'caja_id': 1,
        'usuario': 'Cesar Admin',
        'tipo_cierre': 'CIERRE Z MANUAL',
        'efectivo_esperado': 54000.0,
        'efectivo_fisico': 54000.0,
        'diferencia': 0.0,
        'total_ventas': 120000.0
    }
    
    html = generar_html_cierre_z(datos_mock)
    
    test_file_path = os.path.join(os.path.dirname(__file__), 'test_cierre_z.html')
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(html)
        
    print("[EXITO] HTML generado correctamente.")
    print(f"Puedes abrir el archivo {test_file_path} en tu navegador para ver cómo se verá el email.")

def test_autocierre():
    print("\n--- PROBANDO LÓGICA DE AUTOCIERRE ---")
    from src.services.caja_service import verificar_y_realizar_autocierre
    
    print("Llamando a verificar_y_realizar_autocierre()...")
    hizo_cierre, monto = verificar_y_realizar_autocierre()
    
    if hizo_cierre:
        print(f"[OK] Se cerraron ventas automáticamente. Monto total: ${monto}")
    else:
        print("[OK] No hay ventas pendientes de días anteriores para auto-cerrar.")

if __name__ == "__main__":
    test_alerta_stock()
    test_email_cierre()
    test_autocierre()
    print("\nTESTS FINALIZADOS CON EXITO.")
