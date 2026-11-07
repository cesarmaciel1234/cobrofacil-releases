import json
import threading
import socket
import os
import hashlib
import uuid
from decimal import Decimal
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from src.logger import logger
from src.base_de_datos.database import db_manager
from src.config import config
from src.central_red_global.sync_tienda.maestra.http import manejar_get, manejar_post, payload_ranking


def es_anuncio_tienda(info: dict) -> bool:
    """PC maestra con MariaDB (caja o cartelería en la misma máquina). No TV esclava."""
    if not isinstance(info, dict):
        return False
    if str(info.get("mode") or "").upper() != "MAESTRA":
        return False
    if str(info.get("esclava") or "").lower() in ("1", "true", "si"):
        return False
    eng = str(info.get("db_engine") or "").lower()
    if eng and eng != "mariadb":
        return False
    serv = str(info.get("servicio") or "").lower()
    if serv in ("esclava", "tv_esclava"):
        return False
    return True


def _esta_pc_anuncia_tienda() -> bool:
    """Misma regla que el jefe: maestra + MariaDB. Esclava (TV sola) no se anuncia."""
    try:
        if config.get("carteleria_is_slave") or config.get("is_master") is False:
            return False
    except Exception:
        pass
    if not getattr(db_manager, "is_master", False):
        return False
    return getattr(db_manager, "db_engine_type", "") == "mariadb"


def _payload_publicidad():
    try:
        from src.carteleria.motor_carteleria.motor_publicidad import motor_publicidad

        motor_publicidad.cargar_configuracion(forzar=True)
        return motor_publicidad.as_dict()
    except Exception:
        return {"promocionados": [], "ids": []}


def _payload_reporte():
    try:
        from src.jefe.reportes.financiero.consulta import payload_reporte_global

        return payload_reporte_global()
    except Exception:
        return {}


API_PORT = 8000
UDP_PORT = 37020

lan_exit_event = threading.Event()
_http_server_instance = None
_http_thread = None
_udp_thread = None
_lifecycle_lock = threading.Lock()
_HTTP_WORKERS = 32
_RETRY_SECONDS = 5


class _BoundedThreadingHTTPServer(ThreadingHTTPServer):
    """Atiende solicitudes en paralelo sin permitir hilos ilimitados."""

    daemon_threads = True
    block_on_close = False

    def __init__(self, server_address, request_handler):
        self._request_slots = threading.BoundedSemaphore(_HTTP_WORKERS)
        super().__init__(server_address, request_handler)

    def process_request(self, request, client_address):
        if not self._request_slots.acquire(blocking=False):
            logger.warning("Servidor API LAN ocupado; se rechazó una conexión por límite de concurrencia.")
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self._request_slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._request_slots.release()


def _store_id_local() -> str:
    """Identidad estable de esta tienda; la IP solo indica dónde encontrarla."""
    store_id = str(config.get("store_id", "") or "").strip()
    if store_id:
        return store_id
    store_id = uuid.uuid4().hex
    config.set("store_id", store_id)
    return store_id


def stop_lan_server():
    lan_exit_event.set()
    if _http_server_instance:
        threading.Thread(target=_http_server_instance.shutdown, daemon=True).start()

def _json_safe(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", "replace")
    if hasattr(value, "keys") and not isinstance(value, dict):
        try:
            return {k: value[k] for k in value.keys()}
        except Exception:
            pass
    return str(value)


class LANRequestHandler(BaseHTTPRequestHandler):
    def _send_response(self, status, data):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=_json_safe).encode('utf-8'))

    def _check_auth(self):
        expected_token = config.token_api_lan()
        auth_header = self.headers.get("Authorization", "")
        presented = ""
        if auth_header.startswith("Bearer "):
            presented = auth_header[7:].strip()
        if not presented:
            presented = (self.headers.get("X-LAN-Token") or "").strip()
        if presented and expected_token and presented == expected_token:
            return True
        self._send_response(401, {"status": "error", "message": "Acceso denegado. Token LAN inválido."})
        return False

    def do_POST(self):
        if not self._check_auth():
            return
        if manejar_post(self, self.path):
            return
        if self.path == '/api/guardar_venta':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))
                venta_data = data.get('venta_data') or {}
                items = data.get('items')
                fiado = data.get('fiado')
                if not fiado and str(venta_data.get('metodo_pago') or '') in ('Fiado', 'Clientes'):
                    cid = venta_data.get('cliente_id') or venta_data.get('fiado_cliente_id')
                    if cid:
                        fiado = {
                            'cliente_id': cid,
                            'total': float(venta_data.get('total') or 0),
                        }
                id_venta = db_manager.guardar_venta_completa(venta_data, items, fiado=fiado)

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
                expected_upd = config.token_api_lan()
                if not expected_upd or auth_token != expected_upd:
                    self._send_response(401, {"status": "error", "message": "Acceso denegado: Token inválido."})
                    return

                master_ip = data.get('master_ip')
                if not master_ip:
                    self._send_response(400, {"status": "error", "message": "Falta el parámetro master_ip."})
                    return
                logger.info(f"Petición remota para cambiar a rol ESCLAVA con Maestra en {master_ip}")

                import pymysql
                try:
                    from src.db_engines.mariadb_engine import MariaDBEngine
                    pwd = getattr(MariaDBEngine, "password", None) or "1234"
                    engine = MariaDBEngine(host=master_ip)
                    pwd = engine.password
                    conn = pymysql.connect(host=master_ip, port=3306, user="root", password=pwd, connect_timeout=3)
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

        elif self.path == '/api/carteleria/config_update':
            try:
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

    def do_GET(self):
        if manejar_get(self, self.path):
            return
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
                sos_query = f"SELECT nombre, precio, precio_oferta, precio_oferta_relampago, precio_oferta_promedio, cant_oferta, tipo_unidad_oferta, stock FROM productos WHERE precio_oferta_relampago > 0 AND (precio > 0 OR precio_oferta > 0 OR precio_oferta_relampago > 0) AND LOWER(nombre) NOT LIKE '%articulo comun%' AND LOWER(nombre) NOT LIKE '%venta libre%' ORDER BY {rand_func} LIMIT 10"
                oferta_sos = db_manager.execute_query(sos_query)

                # Precios (mismas columnas que DbSyncWorker: PNG + departamento)
                precios_query = (
                    "SELECT categoria, nombre, precio, precio_oferta, precio_oferta_relampago, "
                    "precio_oferta_promedio, cant_oferta, tipo_unidad_oferta, stock, unidad, "
                    "es_pesable, departamento, icono, id FROM productos WHERE precio > 0 "
                    "AND LOWER(nombre) NOT LIKE '%articulo comun%' "
                    "AND LOWER(nombre) NOT LIKE '%venta libre%' "
                    "ORDER BY categoria"
                )
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

                # Sin ventas el top queda vacío. No se rellena con productos al azar.


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
                    "top10": top_dict,
                    "ranking": payload_ranking(),
                    "publicidad": _payload_publicidad(),
                    "reporte": _payload_reporte(),
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

    def log_message(self, format, *args):
        pass

def start_http_server():
    global _http_server_instance
    while not lan_exit_event.is_set():
        server = None
        try:
            server = _BoundedThreadingHTTPServer(('0.0.0.0', API_PORT), LANRequestHandler)
            _http_server_instance = server
            logger.info(
                "Servidor API LAN escuchando en puerto %s (máximo %s solicitudes simultáneas).",
                API_PORT,
                _HTTP_WORKERS,
            )
            server.serve_forever(poll_interval=0.5)
        except OSError as e:
            if not lan_exit_event.is_set():
                logger.error("No se pudo iniciar el servidor API LAN: %s", e)
        except Exception as e:
            if not lan_exit_event.is_set():
                logger.exception("El servidor API LAN se interrumpió: %s", e)
        finally:
            if _http_server_instance is server:
                _http_server_instance = None
            if server is not None:
                server.server_close()
        if not lan_exit_event.is_set():
            lan_exit_event.wait(_RETRY_SECONDS)

def start_udp_discovery_server():
    while not lan_exit_event.is_set():
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(('0.0.0.0', UDP_PORT))
            sock.settimeout(2.0)
            logger.info("Servidor UDP Discovery LAN escuchando en puerto %s", UDP_PORT)

            while not lan_exit_event.is_set():
                try:
                    data, addr = sock.recvfrom(1024)
                except socket.timeout:
                    continue
                except OSError as e:
                    if not lan_exit_event.is_set():
                        logger.error("Error recibiendo descubrimiento UDP: %s", e)
                    break

                try:
                    if data == b"PUNPRO_DISCOVER":
                        if not _esta_pc_anuncia_tienda():
                            continue
                        db_engine = getattr(db_manager, "db_engine_type", "sqlite")
                        try:
                            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            s.connect(("8.8.8.8", 80))
                            local_ip = s.getsockname()[0]
                            s.close()
                        except OSError:
                            local_ip = socket.gethostbyname(socket.gethostname())

                        pass_hash = hashlib.sha256(config.get("server_password", "1234").encode()).hexdigest()
                        response = {
                            "hostname": socket.gethostname(),
                            "server_ip": local_ip,
                            "store_id": _store_id_local(),
                            "db_path": getattr(db_manager, "db_path", ""),
                            "pass_hash": pass_hash,
                            "mode": "MAESTRA",
                            "servicio": "tienda",
                            "db_engine": db_engine,
                            "api_url": f"http://{local_ip}:{API_PORT}",
                        }
                        sock.sendto(json.dumps(response).encode("utf-8"), addr)
                except Exception as e:
                    logger.exception("Error procesando petición UDP de descubrimiento: %s", e)
        except OSError as e:
            if not lan_exit_event.is_set():
                logger.error("No se pudo iniciar el descubrimiento UDP: %s", e)
        finally:
            if sock is not None:
                sock.close()
        if not lan_exit_event.is_set():
            lan_exit_event.wait(_RETRY_SECONDS)

def init_lan_server():
    """Inicia los servidores LAN (API HTTP y UDP Discovery) en segundo plano si no están iniciados."""
    global _http_thread, _udp_thread
    with _lifecycle_lock:
        if lan_exit_event.is_set():
            lan_exit_event.clear()
        if _http_thread is None or not _http_thread.is_alive():
            _http_thread = threading.Thread(
                target=start_http_server,
                name="servidor-api-lan",
                daemon=True,
            )
            _http_thread.start()
        if _udp_thread is None or not _udp_thread.is_alive():
            _udp_thread = threading.Thread(
                target=start_udp_discovery_server,
                name="servidor-discovery-udp",
                daemon=True,
            )
            _udp_thread.start()
