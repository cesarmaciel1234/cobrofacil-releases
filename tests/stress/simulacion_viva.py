import time
import json
import random
import os
from src.base_de_datos.database import Database

def run_simulation():
    db = Database()
    
    productos = [
        "Pechuga de Pollo Premium",
        "Asado de Novillo",
        "Coca-Cola 2L",
        "Empanadas de Carne",
        "Helado de Chocolate",
        "Pan Frances",
        "Tomates Perita",
        "Queso Cremoso",
        "Vino Tinto Malbec",
        "Chorizo Mezcla"
    ]
    
    print("Iniciando simulacion continua...")
    
    loop_count = 0
    while True:
        # Simular escaneo cada 5 segundos
        if loop_count % 5 == 0:
            producto = random.choice(productos)
            scan_data = {
                "timestamp": time.time(),
                "ultimo_escaneado": producto
            }
            with open("live_scan.json", "w", encoding="utf-8") as f:
                json.dump(scan_data, f)
            print(f"Cajero escaneó: {producto}")
            
        # Rotar la Oferta Relámpago cada 25 segundos
        if loop_count % 25 == 0:
            try:
                # MariaDB usa RAND(), SQLite usa RANDOM()
                db.execute_non_query("UPDATE productos SET es_sos = 0")
                if getattr(db, 'db_engine_type', 'sqlite') == 'mariadb':
                    db.execute_non_query("UPDATE productos SET es_sos = 1 WHERE precio > 0 ORDER BY RAND() LIMIT 1")
                else:
                    db.execute_non_query("UPDATE productos SET es_sos = 1 WHERE precio > 0 ORDER BY RANDOM() LIMIT 1")
                print("¡Nueva oferta relámpago activada!")
            except Exception as e:
                print(f"Error actualizando DB: {e}")
            
        time.sleep(1)
        loop_count += 1

if __name__ == "__main__":
    run_simulation()
