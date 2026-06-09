import os
import sys
import time
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.base_de_datos.database import db_manager
from src.base_de_datos.offline_sync import offline_sync_manager

def run_offline_test():
    print("="*50)
    print("INICIANDO TEST DE RECUPERACIÓN OFFLINE")
    print("="*50)
    
    # 1. Limpiar base y cola offline
    try:
        db_manager.execute_non_query("SET FOREIGN_KEY_CHECKS = 0")
    except Exception:
        pass
    try:
        db_manager.execute_non_query("PRAGMA foreign_keys = OFF")
    except Exception:
        pass
        
    db_manager.execute_non_query("DELETE FROM detalles_ventas WHERE id_venta IN (SELECT id FROM ventas WHERE usuario = 'cajero_offline')")
    db_manager.execute_non_query("DELETE FROM ventas WHERE usuario = 'cajero_offline'")
    
    try:
        db_manager.execute_non_query("SET FOREIGN_KEY_CHECKS = 1")
    except Exception:
        pass
    try:
        db_manager.execute_non_query("PRAGMA foreign_keys = ON")
    except Exception:
        pass

    if os.path.exists(offline_sync_manager.queue_file):
        with open(offline_sync_manager.queue_file, "w", encoding="utf-8") as f:
            json.dump([], f)
            
    print("\n[1] Simulando caída de red y ventas en modo Offline...")
    ventas_caidas = 5
    
    for i in range(ventas_caidas):
        venta_data = {
            'total': 100.0,
            'pago_con': 100.0,
            'cambio': 0.0,
            'pago_efectivo': 100.0,
            'pago_otro': 0.0,
            'usuario': 'cajero_offline',
            'metodo_pago': 'Efectivo',
            'estado': 'COMPLETADA',
            'caja_id': 1
        }
        items = [{
            'id': 1,
            'nombre': 'Producto Offline',
            'cant': 1,
            'precio': 100.0,
            'subtotal': 100.0,
            'es_pesable': 0
        }]
        
        # Simulamos que base_de_datos falla y delega a offline
        offline_sync_manager.guardar_venta_offline(venta_data, items)
        
    with open(offline_sync_manager.queue_file, "r", encoding="utf-8") as f:
        queue = json.load(f)
        
    print(f"[OK] {len(queue)} ventas retenidas en la cola offline local.")
    
    # Iniciar el hilo de sincronización offline manualmente para este test
    offline_sync_manager.sync_worker.start()
    
    print("\n[2] Red restablecida. Esperando que el hilo en segundo plano sincronice...")
    print("El hilo chequea cada 15 segundos. Esperando 16s...")
    
    time.sleep(16)
    
    # Comprobar
    ventas_db = db_manager.execute_scalar("SELECT COUNT(*) FROM ventas WHERE usuario = 'cajero_offline'")
    
    with open(offline_sync_manager.queue_file, "r", encoding="utf-8") as f:
        queue_final = json.load(f)
        
    print("\n" + "="*50)
    print("RESULTADOS OFFLINE:")
    print(f"Ventas en DB: {ventas_db} / Esperadas: {ventas_caidas}")
    print(f"Ventas restantes en buffer: {len(queue_final)}")
    
    if ventas_db == ventas_caidas and len(queue_final) == 0:
        print("[OK] SINCRONIZACIÓN PERFECTA. Tolerancia a fallos certificada.")
    else:
        print("[FALLO] FALLO EN LA RECUPERACIÓN OFFLINE.")
    print("="*50)

if __name__ == "__main__":
    run_offline_test()
