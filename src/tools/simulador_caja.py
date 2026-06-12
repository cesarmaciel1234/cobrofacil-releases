import time
import json
import os

ruta = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'scan_live.json')
productos = ["Asado Especial", "Kilo de Milanesa", "Chorizo Puro Cerdo", "Matambre de Novillo"]

print("INICIANDO SIMULADOR DE CAJERO...")
print("Por favor, mira la pantalla de Cartelería.")

for p in productos:
    print(f"El cajero acaba de escanear: {p}")
    try:
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump({"ultimo_escaneo": p}, f)
    except Exception as e:
        print("Error escribiendo archivo:", e)
    
    # Esperamos 10 segundos para dejar que la alerta se muestre y termine
    time.sleep(12)

print("✅ Pruebas finalizadas.")
