from src.services.lan_server import init_lan_server
import time

print("Iniciando servidor LAN...")
init_lan_server()
print("Servidor LAN iniciado en puerto 8000. Esperando peticiones...")

while True:
    time.sleep(1)
