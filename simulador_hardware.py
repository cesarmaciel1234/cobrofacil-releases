import socket
import json
import time
import sys

NEXUS_UDP_PORT = 37021

def enviar_evento_udp(tipo, role, datos=None):
    origen = f"LAPTOP-SIMULATOR|{role}|caja1"
    payload = {
        "origen": origen,
        "tipo": tipo,
        "datos": datos or {},
        "ts": time.time(),
    }
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        msg = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        sock.sendto(msg, ("255.255.255.255", NEXUS_UDP_PORT))
        sock.close()
        print(f"? Enviado: {tipo} como {role}")
    except Exception as e:
        print(f"? Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        opc = sys.argv[1]
        if opc == "1":
            enviar_evento_udp("VENTA_NUEVA", "CAJERO", {"total": 500, "metodo_pago": "EFECTIVO"})
        elif opc == "2":
            enviar_evento_udp("HARDWARE_SENSOR", "CAJERO", {"evento": "DRAWER_OPEN"})
        elif opc == "3":
            enviar_evento_udp("HARDWARE_SENSOR", "ADMIN", {"evento": "DRAWER_OPEN"})
    else:
        print("Uso: python simulador_hardware.py [1|2|3]")
