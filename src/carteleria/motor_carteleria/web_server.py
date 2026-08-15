import http.server
import json
import os
import socketserver
import threading
import time
from functools import lru_cache

from src.utils.paths import get_resource_path


class CarteleriaWebHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, web_root=None, main_window=None, **kwargs):
        self.web_root = web_root
        self.main_window = main_window
        super().__init__(*args, directory=web_root, **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self.handle_api()
            return
        return super().do_GET()

    def handle_api(self):
        if self.path == "/api/state":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            state = self.main_window.get_web_state() if self.main_window else {}
            print(f"[WebServer] /api/state: {len(state.get('precios', []))} productos en estado")
            self.wfile.write(json.dumps(state, ensure_ascii=False).encode("utf-8"))
            return

        if self.path == "/api/precios":
            start_time = time.time()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            try:
                # Usar cache del main_window si está disponible
                if self.main_window and hasattr(self.main_window, 'rows_precios') and self.main_window.rows_precios:
                    precios = self.main_window.rows_precios
                    print(f"[WebServer] /api/precios: {len(precios)} productos desde cache ({(time.time() - start_time)*1000:.0f}ms)")
                    self.wfile.write(json.dumps({'precios': precios}, ensure_ascii=False).encode('utf-8'))
                    return
                
                # Cargar desde inventario real (tabla productos)
                from src.base_de_datos.database import db_manager
                q = """
                    SELECT 
                        id, 
                        nombre, 
                        precio, 
                        precio_oferta, 
                        cant_oferta, 
                        tipo_unidad_oferta,
                        departamento,
                        categoria,
                        stock,
                        unidad,
                        es_pesable
                    FROM productos 
                    WHERE COALESCE(stock, 0) > 0
                    ORDER BY nombre
                    LIMIT 50
                """
                filas = db_manager.execute_query(q)
                precios = []
                if filas:
                    for r in filas:
                        if isinstance(r, dict):
                            precios.append({
                                'id': r.get('id'),
                                'nombre': r.get('nombre'),
                                'precio': r.get('precio') or 0,
                                'precio_oferta': r.get('precio_oferta') or 0,
                                'cant_oferta': r.get('cant_oferta') or 0,
                                'tipo_unidad_oferta': r.get('tipo_unidad_oferta') or '',
                                'departamento': r.get('departamento') or '',
                                'categoria': r.get('categoria') or '',
                                'stock': r.get('stock') or 0,
                                'unidad': r.get('unidad') or '',
                                'es_pesable': r.get('es_pesable') or 0,
                            })
                        else:
                            # Fallback para tuple
                            precios.append({
                                'id': r[0] if len(r) > 0 else 0,
                                'nombre': r[1] if len(r) > 1 else '',
                                'precio': r[2] if len(r) > 2 else 0,
                                'precio_oferta': r[3] if len(r) > 3 else 0,
                                'cant_oferta': r[4] if len(r) > 4 else 0,
                                'tipo_unidad_oferta': r[5] if len(r) > 5 else '',
                                'departamento': r[6] if len(r) > 6 else '',
                                'categoria': r[7] if len(r) > 7 else '',
                                'stock': r[8] if len(r) > 8 else 0,
                                'unidad': r[9] if len(r) > 9 else '',
                                'es_pesable': r[10] if len(r) > 10 else 0,
                            })
                elapsed = (time.time() - start_time) * 1000
                print(f"[WebServer] /api/precios: {len(precios)} productos cargados ({elapsed:.0f}ms)")
                if precios:
                    print(f"[WebServer] Primer producto: {precios[0].get('nombre')} - ${precios[0].get('precio')}")
                self.wfile.write(json.dumps({'precios': precios}, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                print(f"[WebServer] Error cargando inventario: {e}")
                self.wfile.write(json.dumps({'precios': []}).encode('utf-8'))
            return

        self.send_response(404)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))

    def log_message(self, format, *args):
        # Evitar spam en stdout
        pass


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class CarteleriaWebServer:
    def __init__(self, main_window, host="127.0.0.1", port=0):
        self.main_window = main_window
        self.host = host
        self.port = port
        self.httpd = None
        self.thread = None
        # Ruta actualizada para estructura lanzador_tv/la_cara_web/
        self.web_root = get_resource_path(os.path.join("src", "carteleria", "lanzador_tv", "la_cara_web"))

    def start(self):
        try:
            if not os.path.isdir(self.web_root):
                return
            handler = lambda *args, **kwargs: CarteleriaWebHandler(*args, web_root=self.web_root, main_window=self.main_window, **kwargs)
            self.httpd = ThreadedHTTPServer((self.host, self.port), handler)
            self.port = self.httpd.server_address[1]
            self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.thread.start()
        except Exception:
            self.httpd = None
            self.thread = None

    def stop(self):
        try:
            if self.httpd:
                self.httpd.shutdown()
                self.httpd.server_close()
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=1)
        except Exception:
            pass
