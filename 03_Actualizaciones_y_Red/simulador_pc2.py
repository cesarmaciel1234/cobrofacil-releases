import socket
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Simula la PC2 (remota) que estará escuchando
FAKE_IP = "127.0.0.1"
API_PORT = 8000
UDP_PORT = 37020

class FakeLANRequestHandler(BaseHTTPRequestHandler):
    def _send_response(self, status, data):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_POST(self):
        if self.path == '/api/set_master':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            print(f"\n[Falsa PC2] Recibí petición POST en /api/set_master")
            print(f"[Falsa PC2] Datos recibidos: {post_data.decode('utf-8')}")
            
            # Simular que aceptamos convertirnos en esclava
            self._send_response(200, {"status": "success", "message": "Simulacion: Rol cambiado a ESCLAVA exitosamente."})
        else:
            self._send_response(404, {"status": "not_found"})

    def do_GET(self):
        if self.path == '/api/ping':
            print(f"\n[Falsa PC2] Recibí petición GET en /api/ping")
            self._send_response(200, {"status": "ok", "mode": "MAESTRA", "hostname": "TEST-PC2"})
        else:
            self._send_response(404, {"status": "not_found"})

    def log_message(self, format, *args):
        pass

def start_http_server():
    server = HTTPServer(('0.0.0.0', API_PORT), FakeLANRequestHandler)
    print(f"[Falsa PC2] API HTTP escuchando en puerto {API_PORT}")
    server.serve_forever()

def start_udp_discovery_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(('0.0.0.0', UDP_PORT))
    print(f"[Falsa PC2] UDP Discovery escuchando en puerto {UDP_PORT}")
    
    while True:
        data, addr = sock.recvfrom(1024)
        if data == b"PUNPRO_DISCOVER":
            print(f"\n[Falsa PC2] Recibí Broadcast UDP de {addr}")
            # Responder con datos falsos
            response = {
                "hostname": "TEST-PC2",
                "server_ip": "127.0.0.2", # Usamos .2 para evitar el bloqueo de "no se puede conectar a sí mismo"
                "db_path": "simulated_path",
                "pass_hash": "simulated_hash",
                "mode": "MAESTRA",
                "api_url": f"http://127.0.0.2:{API_PORT}"
            }
            sock.sendto(json.dumps(response).encode('utf-8'), addr)

if __name__ == "__main__":
    print("==================================================")
    print(" Iniciando simulador de PC2 (PC Remota Falsa)")
    print("==================================================")
    
    t_http = threading.Thread(target=start_http_server, daemon=True)
    t_http.start()
    
    start_udp_discovery_server()
