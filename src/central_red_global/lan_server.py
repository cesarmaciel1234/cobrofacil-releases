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

lan_exit_event = threading.Event()
_http_server_instance = None

def stop_lan_server():
    lan_exit_event.set()
    if _http_server_instance:
        threading.Thread(target=_http_server_instance.shutdown, daemon=True).start()

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
                    try:
                        from src.base_de_datos.diario_ventas_externo import encolar_venta

                        encolar_venta(id_venta, venta_data or {}, items or [])
                    except Exception:
                        pass
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
                
                auth_token = data.get('token', '')
                if auth_token != config.get("update_auth_token", "1234"):
                    self._send_response(401, {"status": "error", "message": "Acceso denegado: Token inválido."})
                    return
                
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
                        
                # Reconexión en caliente (sin matar el proceso). Cartelería y
                # terminales deben seguir abiertos al pasar a ESCLAVA.
                from src.central_red_global.motor_red import MotorRed
                motor = MotorRed()
                ok, msg = motor.convertir_en_esclava(master_ip)
                if not ok:
                    self._send_response(500, {"status": "error", "message": msg})
                    return
                self._send_response(200, {
                    "status": "success",
                    "message": f"Rol cambiado a ESCLAVA. {msg}",
                })
                # Solo reiniciar si no hay QApplication (proceso headless / --server)
                from PyQt6.QtWidgets import QApplication
                from PyQt6.QtCore import QTimer
                app = QApplication.instance()
                if app is None:
                    return
                # Reinicio suave solo si el caller lo pide (compat). Por defecto no.
                if data.get("restart", False):
                    QTimer.singleShot(1000, lambda: app.exit(888))
            except Exception as e:
                logger.error(f"Error procesando /api/set_master: {e}")
                self._send_response(500, {"status": "error", "message": str(e)})
        else:
            self._send_response(404, {"status": "not_found"})

    def do_GET(self):
        if self.path == '/api/ping':
            mode = "MAESTRA" if getattr(db_manager, "is_master", True) else "ESCLAVA"
            self._send_response(200, {"status": "ok", "mode": mode, "hostname": socket.gethostname()})
        elif self.path == '/api/live_scan':
            from src.utils.paths import get_base_path
            import os
            import json
            
            path_ls = os.path.join(get_base_path(), "live_scan.json")
            if os.path.exists(path_ls):
                try:
                    with open(path_ls, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self._send_response(200, data)
                except Exception as e:
                    self._send_response(500, {"error": str(e)})
    
        elif self.path == '/api/carteleria/grilla':
            try:
                import json
                query = 'SELECT departamento, nombre_producto, precio_normal, precio_oferta, regla_texto FROM carteleria_global ORDER BY departamento, nombre_producto'
                rows = db_manager.execute_query(query)
                
                # Format to dictionary: {'ALMACEN': [('nombre', 100, 50, 'regla')], ...}
                agrupados = {}
                for r in rows:
                    if isinstance(r, dict):
                        cat = str(r.get('departamento') or '')
                        nombre = str(r.get('nombre_producto') or '')
                        pn = float(r.get('precio_normal') or 0)
                        po = float(r.get('precio_oferta') or 0)
                        rt = str(r.get('regla_texto') or '')
                    else:
                        cat = str(r[0] or '')
                        nombre = str(r[1] or '')
                        pn = float(r[2] or 0)
                        po = float(r[3] or 0)
                        rt = str(r[4] or '')
                    
                    if cat not in agrupados: agrupados[cat] = []
                    agrupados[cat].append((nombre, pn, po, rt))
                
                self._send_response(200, agrupados)
            except Exception as e:
                self._send_response(500, {'error': str(e)})

        elif self.path == '/api/carteleria/data':
            try:
                import json
                import os
                from src.utils.paths import get_base_path
                config_path = os.path.join(get_base_path(), "config.json")
                cfg_data = {}
                if os.path.exists(config_path):
                    with open(config_path, "r", encoding="utf-8") as f:
                        cfg_data = json.load(f)
                        
                is_mariadb = getattr(db_manager, "db_engine_type", "sqlite") == "mariadb"
                rand_func = "RAND()" if is_mariadb else "RANDOM()"
                
                # SOS
                sos_query = f"SELECT nombre, precio, precio_oferta, precio_oferta_relampago, precio_oferta_promedio, cant_oferta, tipo_unidad_oferta, stock FROM productos WHERE precio_oferta_relampago > 0 AND (precio > 0 OR precio_oferta > 0 OR precio_oferta_relampago > 0) ORDER BY {rand_func} LIMIT 1"
                oferta_sos = db_manager.execute_query(sos_query)
                
                # Precios
                precios_query = "SELECT categoria, nombre, precio, precio_oferta, precio_oferta_relampago, precio_oferta_promedio, cant_oferta, tipo_unidad_oferta, stock FROM productos WHERE precio > 0 ORDER BY categoria"
                rows_precios = db_manager.execute_query(precios_query)
                
                # Top Ventas Reales (Hoy, Semana, Mes)
                if is_mariadb:
                    cond_hoy = "DATE(v.fecha) = CURDATE()"
                    cond_semana = "v.fecha >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
                    cond_mes = "v.fecha >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
                    join_cond = "dv.id_producto COLLATE utf8mb4_unicode_ci = p.codigo COLLATE utf8mb4_unicode_ci OR dv.id_producto COLLATE utf8mb4_unicode_ci = CAST(p.id AS CHAR) COLLATE utf8mb4_unicode_ci"
                else:
                    cond_hoy = "date(v.fecha) = date('now', 'localtime')"
                    cond_semana = "date(v.fecha) >= date('now', '-7 days', 'localtime')"
                    cond_mes = "date(v.fecha) >= date('now', '-30 days', 'localtime')"
                    join_cond = "dv.id_producto = p.codigo OR dv.id_producto = CAST(p.id AS TEXT)"
                
                def get_top_query(cond_date):
                    return f"""
                        SELECT p.nombre, p.precio, p.precio_oferta, p.precio_oferta_relampago, 
                               p.precio_oferta_promedio, p.cant_oferta, p.tipo_unidad_oferta, p.stock, p.es_pesable
                        FROM detalles_ventas dv
                        JOIN ventas v ON dv.id_venta = v.id
                        JOIN productos p ON {join_cond}
                        WHERE {cond_date} AND p.precio > 0
                        GROUP BY p.id, p.codigo, p.nombre, p.precio, p.precio_oferta, p.precio_oferta_relampago, p.precio_oferta_promedio, p.cant_oferta, p.tipo_unidad_oferta, p.stock, p.es_pesable
                        ORDER BY SUM(dv.cantidad) DESC
                        LIMIT 10
                    """
                
                top_dict = {"hoy": [], "semana": [], "mes": []}
                
                try:
                    # SQLite usa CAST(p.id AS TEXT), MariaDB usa CAST(p.id AS CHAR)
                    q_hoy = get_top_query(cond_hoy)
                    q_sem = get_top_query(cond_semana)
                    q_mes = get_top_query(cond_mes)
                    
                    if not is_mariadb:
                        q_hoy = q_hoy.replace("CAST(p.id AS CHAR)", "CAST(p.id AS TEXT)").replace("VARCHAR(50)", "TEXT")
                        q_sem = q_sem.replace("CAST(p.id AS CHAR)", "CAST(p.id AS TEXT)").replace("VARCHAR(50)", "TEXT")
                        q_mes = q_mes.replace("CAST(p.id AS CHAR)", "CAST(p.id AS TEXT)").replace("VARCHAR(50)", "TEXT")
                    
                    top_dict["hoy"] = db_manager.execute_query(q_hoy)
                    top_dict["semana"] = db_manager.execute_query(q_sem)
                    top_dict["mes"] = db_manager.execute_query(q_mes)
                except Exception as e_sql:
                    # Fallback si las tablas no están listas o hay un error de JOIN
                    pass
                
                # Si el real falló o está vacío por falta de ventas, rellenar con aleatorios
                fallback_q = f"SELECT nombre, precio, precio_oferta, precio_oferta_relampago, precio_oferta_promedio, cant_oferta, tipo_unidad_oferta, stock, es_pesable FROM productos WHERE precio > 0 ORDER BY {rand_func} LIMIT 10"
                if not top_dict["hoy"]: top_dict["hoy"] = db_manager.execute_query(fallback_q)
                if not top_dict["semana"]: top_dict["semana"] = top_dict["hoy"]
                if not top_dict["mes"]: top_dict["mes"] = top_dict["hoy"]

                
                # Resumen para el dashboard
                response_data = {
                    "config": {
                        "business_name": cfg_data.get("business_name", "Carnicería"),
                        "phone": cfg_data.get("phone", "No disponible"),
                        "carteleria_rotacion": cfg_data.get("carteleria_rotacion", 15),
                        "carteleria_tiempo_sos": cfg_data.get("carteleria_tiempo_sos", 10),
                        "carteleria_frec_sos": cfg_data.get("carteleria_frec_sos", 2),
                        "mensaje_zocalo": cfg_data.get("mensaje_zocalo", "")
                    },
                    "sos": oferta_sos,
                    "precios": rows_precios,
                    "top10": top_dict
                }
                
                self._send_response(200, response_data)
            except Exception as e:
                self._send_response(500, {"error": str(e)})
        elif self.path in ("/carteleria_cache.json", "/api/carteleria/cache"):
            # Alias: cartelería esclava pedía el JSON plano (código viejo)
            self.path = "/api/carteleria/data"
            return self.do_GET()
        else:
            self._send_response(404, {"status": "not_found"})

    def do_POST(self):
        if self.path == '/api/carteleria/config_update':
            try:
                import json
                from src.config import config
                
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(post_data)
                
                for key, val in data.items():
                    config.set(key, val)
                
                config.save()
                self._send_response(200, {"status": "success"})
            except Exception as e:
                self._send_response(500, {"error": str(e)})
        else:
            self._send_response(404, {"status": "not_found"})

    def log_message(self, format, *args):
        pass

def start_http_server():
    global _http_server_instance
    try:
        server = HTTPServer(('0.0.0.0', API_PORT), LANRequestHandler)
        _http_server_instance = server
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
        sock.settimeout(2.0)
        logger.info(f"Servidor UDP Discovery LAN iniciado en puerto {UDP_PORT}")
        
        while not lan_exit_event.is_set():
            try:
                data, addr = sock.recvfrom(1024)
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Error procesando peticion UDP Discovery: {e}")
                continue
                
            try:
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
                logger.error(f"Error parseando peticion UDP: {e}")
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
