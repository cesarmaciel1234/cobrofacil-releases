import json
import time
import threading
import os

path = 'live_scan.json'
running = True

def pos_writer():
    for i in range(100):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({'carrito': [{'producto': f'Prod {i}', 'precio': i}], 'timestamp': time.time()}, f)
        except Exception as e:
            print(f'[POS] Error de escritura: {e}')
        time.sleep(0.01)

def lan_reader():
    for i in range(100):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f'[LAN] Error de lectura: {e}')
        time.sleep(0.01)

print('[BRIDGE TEST] Iniciando prueba de colision de lectura/escritura (POS vs LAN)...')

t1 = threading.Thread(target=pos_writer)
t2 = threading.Thread(target=lan_reader)

t1.start()
t2.start()

t1.join()
t2.join()

print('[BRIDGE TEST] Prueba de colision finalizada.')
