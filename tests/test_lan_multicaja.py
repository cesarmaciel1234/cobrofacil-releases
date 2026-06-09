import os
import sys
import threading
import time
import requests
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.base_de_datos.database import db_manager

API_URL = "http://127.0.0.1:8000/api/guardar_venta"

def cajero_worker(caja_id, cajero_name, num_ventas):
    print(f"[Caja {caja_id}] Iniciando turno. Procesando {num_ventas} ventas...")
    exitos = 0
    fallos = 0
    start_time = time.time()
    
    for i in range(num_ventas):
        venta_data = {
            'total': 150.0,
            'pago_con': 200.0,
            'cambio': 50.0,
            'pago_efectivo': 150.0,
            'pago_otro': 0.0,
            'usuario': cajero_name,
            'metodo_pago': 'Efectivo',
            'estado': 'COMPLETADA',
            'descuento': 0.0,
            'recargo': 0.0,
            'caja_id': caja_id
        }
        items = [{
            'id': 1, # Asumimos que hay un producto con ID 1
            'nombre': 'Producto Multicaja',
            'cant': 1,
            'precio': 150.0,
            'subtotal': 150.0,
            'es_pesable': 0
        }]
        
        payload = {
            "venta_data": venta_data,
            "items": items
        }
        
        try:
            response = requests.post(API_URL, json=payload, timeout=5.0)
            if response.status_code == 200 and response.json().get("status") == "success":
                exitos += 1
            else:
                fallos += 1
        except Exception as e:
            fallos += 1
            
        time.sleep(0.01) # Simular pequeño tiempo de escaneo/cobro
 
    end_time = time.time()
    print(f"[Caja {caja_id}] Turno finalizado en {end_time - start_time:.2f}s. Exitosas: {exitos}, Fallos: {fallos}")

def run_multicaja_test():
    print("="*50)
    print("INICIANDO TEST DE CONCURRENCIA MULTICAJA LAN")
    print("="*50)
    
    # Pre-crear el producto
    db_manager.execute_non_query("INSERT OR IGNORE INTO productos (id, codigo, nombre, precio, stock) VALUES (1, 'MC001', 'Producto Multicaja', 150.0, 10000.0)")
    
    # Empezar servidor LAN en un hilo (Si no está corriendo)
    from src.services.lan_server import init_lan_server
    init_lan_server()
    print("Servidor LAN Maestro iniciado. Esperando 2 segundos...")
    time.sleep(2)
    
    num_cajas = 3
    ventas_por_caja = 30
    
    threads = []
    for caja_id in range(1, num_cajas + 1):
        t = threading.Thread(target=cajero_worker, args=(caja_id, f"cajero_{caja_id}", ventas_por_caja))
        threads.append(t)
        
    start_total = time.time()
    for t in threads:
        t.start()
        
    for t in threads:
        t.join()
        
    end_total = time.time()
    
    # Comprobación de integridad
    total_esperado = num_cajas * ventas_por_caja
    ventas_db = db_manager.execute_scalar("SELECT COUNT(*) FROM ventas WHERE usuario LIKE 'cajero_%'")
    
    print("\n" + "="*50)
    print(f"TEST FINALIZADO EN {end_total - start_total:.2f}s")
    print(f"Ventas procesadas (DB): {ventas_db} / Esperadas: {total_esperado}")
    if ventas_db == total_esperado:
        print("[OK] CONCURRENCIA PERFECTA. Sin bloqueos ni datos perdidos.")
    else:
        print("[FALLO] PÉRDIDA DE DATOS O BLOQUEO DE DB DETECTADO.")
    print("="*50)
    
if __name__ == "__main__":
    # Limpieza previa
    try:
        db_manager.execute_non_query("SET FOREIGN_KEY_CHECKS = 0")
    except Exception:
        pass
    try:
        db_manager.execute_non_query("PRAGMA foreign_keys = OFF")
    except Exception:
        pass
        
    db_manager.execute_non_query("DELETE FROM detalles_ventas WHERE id_venta IN (SELECT id FROM ventas WHERE usuario LIKE 'cajero_%')")
    db_manager.execute_non_query("DELETE FROM ventas WHERE usuario LIKE 'cajero_%'")
    
    try:
        db_manager.execute_non_query("SET FOREIGN_KEY_CHECKS = 1")
    except Exception:
        pass
    try:
        db_manager.execute_non_query("PRAGMA foreign_keys = ON")
    except Exception:
        pass
        
    run_multicaja_test()
