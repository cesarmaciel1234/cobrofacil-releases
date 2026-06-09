import json
import threading
import socket
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
                
                # Guardar en base de datos local
                id_venta = db_manager.guardar_venta_completa(venta_data, items)
                
                if id_venta and id_venta != 9999999:
                    self._send_response(200, {"status": "success", "id_venta": id_venta})
                else:
                    self._send_response(500, {"status": "error", "message": "Failed to save to database."})
            except Exception as e:
                logger.error(f"API LAN Error: {e}")
                self._send_response(500, {"status": "error", "message": str(e)})
                
        elif self.path == '/api/set_master':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                master_ip = data.get('master_ip')
                if not master_ip:
                    self._send_response(400, {"status": "error", "message": "Falta el parámetro master_ip."})
                    return
                logger.info(f"Petición remota para cambiar a rol ESCLAVA con Maestra en {master_ip}")
                
                # Test connection to master on 3306 using '1234' then fallback to ''
                import pymysql
                try:
                    conn = pymysql.connect(host=master_ip, port=3306, user="root", password="1234", connect_timeout=3)
                    conn.close()
                except Exception:
                    try:
                        conn = pymysql.connect(host=master_ip, port=3306, user="root", password="", connect_timeout=3)
                        conn.close()
                    except Exception as e:
                        self._send_response(500, {
                            "status": "error", 
                            "message": f"No se pudo establecer conexión TCP/MariaDB con {master_ip}:3306. Detalle: {str(e)}"
                        })
                        return
                        
                config.set("db_engine", "mariadb")
                config.set("db_host", master_ip)
                config.save()
                self._send_response(200, {"status": "success", "message": f"Rol cambiado a ESCLAVA exitosamente. Conectando a {master_ip}."})
                from PyQt5.QtWidgets import QApplication
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(1000, lambda: QApplication.instance().exit(888))
            except Exception as e:
                logger.error(f"Error procesando /api/set_master: {e}")
                self._send_response(500, {"status": "error", "message": str(e)})
        else:
            self._send_response(404, {"status": "not_found"})

    def do_GET(self):
        if self.path == '/api/ping':
            mode = "MAESTRA" if getattr(db_manager, "is_master", True) else "ESCLAVA"
            self._send_response(200, {"status": "ok", "mode": mode, "hostname": socket.gethostname()})
        else:
            self._send_response(404, {"status": "not_found"})

    def log_message(self, format, *args):
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
            try:
                data, addr = sock.recvfrom(1024)
                if data == b"PUNPRO_DISCOVER":
                    db_engine = getattr(db_manager, 'db_engine_type', 'sqlite')
                    if db_engine == 'sqlite' and not os.path.exists(db_manager.db_path):
                        continue
                        
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        s.connect(("8.8.8.8", 80))
                        local_ip = s.getsockname()[0]
                        s.close()
                    except Exception:
                        local_ip = socket.gethostbyname(socket.gethostname())
                    
                    pass_hash = hashlib.sha256(config.get("server_password", "1234").encode()).hexdigest()
                    is_master = getattr(db_manager, "is_master", True)
                    
                    response = {
                        "hostname": socket.gethostname(),
                        "server_ip": local_ip,
                        "db_path": db_manager.db_path,
                        "pass_hash": pass_hash,
                        "mode": "MAESTRA" if is_master else "ESCLAVA",
                        "api_url": f"http://{local_ip}:{API_PORT}"
                    }
                    sock.sendto(json.dumps(response).encode('utf-8'), addr)
            except Exception as e:
                logger.error(f"Error procesando peticion UDP Discovery: {e}")
    except Exception as e:
        logger.error(f"Error en servidor UDP Discovery: {e}")
    finally:
        sock.close()

_http_server_started = False
_udp_server_started = False

def init_lan_server():
    """Inicia los servidores LAN (API HTTP y UDP Discovery) en segundo plano si no están iniciados."""
    global _http_server_started, _udp_server_started
    
    if not _http_server_started:
        t_http = threading.Thread(target=start_http_server, daemon=True)
        t_http.start()
        _http_server_started = True
        
    if not _udp_server_started:
        t_udp = threading.Thread(target=start_udp_discovery_server, daemon=True)
        t_udp.start()
        _udp_server_started = True
