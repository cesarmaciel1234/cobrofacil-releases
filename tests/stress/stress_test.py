import json
import time
import os
import random

path = 'live_scan.json'

print('[STRESS TEST] Iniciando rafaga de escaneos...')

carrito = []
ahorro = 0.0

for i in range(1, 51):
    producto = f'Producto de prueba {i}'
    precio = round(random.uniform(100.0, 5000.0), 2)
    carrito.append({'producto': producto, 'precio': precio})
    
    # 20% de probabilidad de generar ahorro
    if random.random() < 0.2:
        ahorro += round(random.uniform(50.0, 1000.0), 2)
        
    data = {
        'carrito': carrito,
        'ahorro': ahorro,
        'timestamp': time.time(),
        'ultimo_escaneado': producto
    }
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f)
        
    print(f'Escaneado: {producto} | Carrito: {len(carrito)} items | Ahorro: ')
    
    # Simula escaneos super rapidos (entre 100ms y 300ms)
    time.sleep(random.uniform(0.1, 0.3))

print('[STRESS TEST] Pausa para dejar que la Carteleria analice y salte (2 segundos)...')
time.sleep(2)

print('[STRESS TEST] Rafaga de limpieza (cancelar y volver a empezar)...')
for _ in range(5):
    data = {
        'carrito': [],
        'ahorro': 0.0,
        'timestamp': time.time(),
        'limpiar': True
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    time.sleep(0.2)

print('[STRESS TEST] Fin de la prueba de estres.')
