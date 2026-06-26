import sys
import time
import os
import threading
from PyQt6.QtWidgets import QApplication
from src.cajero.paso5_terminal import Paso5Terminal
from src.services.lan_server import init_lan_server

print('====================================================')
print('[TEST ESTRUCTURA] Iniciando Prueba Completa E2E')
print('====================================================')

# 1. Iniciar Servidor LAN en segundo plano
print('[TEST ESTRUCTURA] 1. Levantando Servidor LAN (El Router)...')
server_thread = threading.Thread(target=init_lan_server, daemon=True)
server_thread.start()
time.sleep(2) # Dar tiempo a que el servidor arranque

# 2. Iniciar Simulador de Cajero TPV
print('[TEST ESTRUCTURA] 2. Iniciando Motor de Cajero (El Emisor)...')
app = QApplication(sys.argv)
terminal = Paso5Terminal()

# 3. Bombardeo de productos
print('[TEST ESTRUCTURA] 3. Simulando Escaneo de Cajero...')
terminal.agregar_a_tabla({'id': '001', 'nombre': 'Fernet Branca', 'precio': 8500.0, 'precio_oferta': 0, 'cant_oferta': 0}, 1.0)
terminal.agregar_a_tabla({'id': '002', 'nombre': 'Coca Cola 2L', 'precio': 2500.0, 'precio_oferta': 0, 'cant_oferta': 0}, 1.0)

# Simular un descuento gigante modificando el JSON manualmente mediante la funcion del TPV para forzar a la IA
print('[TEST ESTRUCTURA] Forzando un Ahorro Extraordinario de  para despertar al Chef Lobo...')
# Hack temporal para la prueba: inyectar ahorro en la tabla oculta (simulando que se aplico el descuento)
# Para no complicarnos con la UI de Qt, lo inyectamos directamente en el metodo de volcado:
carrito_test = [
    {'producto': 'Fernet Branca', 'precio': 8500.0},
    {'producto': 'Coca Cola 2L', 'precio': 2500.0}
]

import json
from src.utils.paths import get_base_path
path = os.path.join(get_base_path(), 'live_scan.json')

with open(path, 'w', encoding='utf-8') as f:
    json.dump({'carrito': carrito_test, 'ahorro': 3000.0, 'timestamp': time.time()}, f, ensure_ascii=False)

print('[TEST ESTRUCTURA] JSON escrito. Si tenes la Carteleria abierta, DEBERIA SALTAR AHORA MISMO (espera 2 segundos).')

# Mantener vivo el programa 15 segundos para que la Carteleria lo lea del LAN Server
time.sleep(15)

print('[TEST ESTRUCTURA] 4. Limpiando Carrito (El Retorno)...')
with open(path, 'w', encoding='utf-8') as f:
    json.dump({'carrito': [], 'ahorro': 0.0, 'timestamp': time.time(), 'limpiar': True}, f, ensure_ascii=False)

print('[TEST ESTRUCTURA] Limpieza enviada. La Carteleria deberia volver a Index 0.')
time.sleep(5)
print('====================================================')
print('[TEST ESTRUCTURA] Finalizado con exito.')
print('====================================================')
