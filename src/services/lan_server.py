import json
import threading
import socket
import sqlite3
import os
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from src.logger import logger
from src.base_de_datos.database import db_manager
from src.config import config

API_PORT = 8000
UDP_PORT = 37020

class LANRequestHandler(BaseHTTPRequestHandler):
    def _send_response(self, status, data):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_POST(self):
        if self.path == '/api/guardar_venta':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                venta_data = data.get('venta_data')
                items = data.get('items')
                
                # We use the db_manager to save it locally on the master
                id_venta = db_manager.guardar_venta_completa(venta_data, items)
                
                if id_venta and id_venta != 9999999:
                    self._send_response(200, {"status": "success", "id_venta": id_venta})
                else:
                    self._send_response(500, {"status": "error", "message": "Failed to save to database."})
            except Exception as e:
                logger.error(f"API LAN Error: {e}")
                self._send_response(500, {"status": "error", "message": str(e)})
        else:
            self._send_response(404, {"status": "not_found"})
            
    def do_GET(self):
        if self.path == '/api/ping':
            self._send_response(200, {"status": "ok", "mode": "MAESTRA"})
        else:
            self._send_response(404, {"status": "not_found"})

    def log_message(self, format, *args):
        # Suppress default HTTP logging to keep console clean
        pass

def start_http_server():
    try:
        server = HTTPServer(('0.0.0.0', API_PORT), LANRequestHandler)
        logger.info(f"Servidor API LAN iniciado en puerto {API_PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Error al iniciar servidor API HTTP: {e}")

def start_udp_discovery_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    try:
        sock.bind(('0.0.0.0', UDP_PORT))
        logger.info(f"Servidor UDP Discovery LAN iniciado en puerto {UDP_PORT}")
        
        while True:
            data, addr = sock.recvfrom(1024)
            if data == b"PUNPRO_DISCOVER":
                # Prepare response
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                
                pass_hash = hashlib.sha256(config.get("server_password", "1234").encode()).hexdigest()
                
                response = {
                    "hostname": socket.gethostname(),
                    "server_ip": local_ip,
                    "db_path": db_manager.db_path,
                    "pass_hash": pass_hash,
                    "mode": "MAESTRA",
                    "api_url": f"http://{local_ip}:{API_PORT}"
                }
                sock.sendto(json.dumps(response).encode('utf-8'), addr)
    except Exception as e:
        logger.error(f"Error en servidor UDP Discovery: {e}")
    finally:
        sock.close()

def init_lan_server():
    """Inicia los servidores LAN solo si la PC actual es la maestra."""
    if db_manager.is_master:
        # Hilo API HTTP para recibir ventas concurrentes
        t_http = threading.Thread(target=start_http_server, daemon=True)
        t_http.start()
        
        # Hilo UDP Discovery para que otras PCs la encuentren
        t_udp = threading.Thread(target=start_udp_discovery_server, daemon=True)
        t_udp.start()
