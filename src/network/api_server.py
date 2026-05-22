"""
api_server.py - Servidor HTTP Local y Transmisor UDP para Monitor Remoto Wi-Fi
Expone la base de datos a otras PCs en la misma red local.
"""
import os
import json
import socket
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import sqlite3

class APIRequestHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "x-api-key, Content-Type")

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self._send_cors_headers()
        self.end_headers()

    def _auth_check(self):
        # Validar la llave API con el PIN del admin
        from src.config import config
        api_key = self.headers.get("x-api-key", "")
        # Obtener el hash del admin real de la base de datos (u omitirlo si es igual al api_key)
        # Para mantenerlo simple, comparamos con el PIN almacenado
        from src.database import db_manager
        res = db_manager.execute_query("SELECT pin FROM usuarios WHERE rol='admin' LIMIT 1")
        if res and res[0]['pin'] == api_key:
            return True
        return False

    def do_POST(self):
        if not self._auth_check():
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Unauthorized")
            return

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            req_data = json.loads(post_data.decode('utf-8'))
            query = req_data.get("query", "")
            params = req_data.get("params", ())
            q_type = req_data.get("type", "query") # 'query', 'non_query', 'scalar'

            from src.database import db_manager
            
            # Ejecutar con el manager nativo
            if q_type == "query":
                result = db_manager.execute_query(query, params)
                resp = {"status": "success", "data": result}
            elif q_type == "non_query":
                db_manager.execute_non_query(query, params)
                resp = {"status": "success"}
            elif q_type == "scalar":
                result = db_manager.execute_scalar(query, params)
                resp = {"status": "success", "data": result}
            else:
                resp = {"status": "error", "message": "Unknown query type"}

            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self._send_cors_headers()
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))

    # Evitar logs masivos en consola
    def log_message(self, format, *args):
        pass


def start_http_server():
    from src.config import config
    port = config.get("api_port", 8080)
    server = ThreadingHTTPServer(('0.0.0.0', port), APIRequestHandler)
    print(f"📡 API Server activo en puerto {port}")
    server.serve_forever()

def start_udp_broadcaster():
    """ Grita a la red WiFi cada 3 segundos 'Soy la Caja Principal' """
    import time
    from src.config import config
    port = config.get("api_port", 8080)
    hostname = socket.gethostname()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    while True:
        try:
            msg = json.dumps({"type": "CAJAFACIL_DISCOVERY", "hostname": hostname, "port": port})
            sock.sendto(msg.encode('utf-8'), ('255.255.255.255', 8081))
        except Exception:
            pass
        time.sleep(3)

class NetworkServer:
    _instance = None
    _started = False
    
    @classmethod
    def start(cls):
        if cls._started: return
        cls._started = True
        
        # Iniciar HTTP API
        t_http = threading.Thread(target=start_http_server, daemon=True)
        t_http.start()
        
        # Iniciar UDP Broadcaster
        t_udp = threading.Thread(target=start_udp_broadcaster, daemon=True)
        t_udp.start()

