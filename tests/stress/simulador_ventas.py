import json, os, time
from src.utils.paths import get_base_path

path = os.path.join(get_base_path(), "live_scan.json")

def simulate_sale(items, wait_time=0.5):
    carrito = []
    total_ahorro = 0.0
    for idx, item in enumerate(items):
        carrito.append(item)
        if "ahorro" in item:
            total_ahorro += item["ahorro"]
        
        print(f"[SIMULADOR] Escaneando: {item['nombre']}... (Item {idx+1}/{len(items)})", flush=True)
        # Volcar al archivo
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"carrito": carrito, "ahorro": total_ahorro, "timestamp": time.time()}, f, ensure_ascii=False)
        except Exception as e:
            print(f"[SIMULADOR] Error: {e}")
        
        time.sleep(wait_time)

    print(f"[SIMULADOR] Venta terminada. Total ahorro: ${total_ahorro}", flush=True)
    time.sleep(15)

print("[SIMULADOR] Iniciando...", flush=True)

# Simulamos una venta con 3 items, escaneados rapido (cada 0.3s)
venta_1 = [
    {"id": "001", "nombre": "Coca Cola 2L", "precio_unitario": "$2500", "cantidad": "1", "descuento": "$0", "subtotal": "$2500", "ahorro": 0},
    {"id": "002", "nombre": "Papas Lays", "precio_unitario": "$1500", "cantidad": "1", "descuento": "$0", "subtotal": "$1500", "ahorro": 0},
    {"id": "003", "nombre": "[OFERTA] Fernet", "precio_unitario": "$6000", "cantidad": "1", "descuento": "$1000", "subtotal": "$6000", "ahorro": 1000}
]

simulate_sale(venta_1, 0.3)

print("[SIMULADOR] Limpiando carrito (nueva venta)...", flush=True)
try:
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"carrito": [], "ahorro": 0.0, "timestamp": time.time(), "limpiar": True}, f, ensure_ascii=False)
except: pass

time.sleep(2)

print("[SIMULADOR] Fin de la simulacion.", flush=True)
