"""
Cerebro Lanzador TV — Servidor HTTP + navegador kiosk

Responsabilidades:
- ServidorCuello: servidor HTTP de archivos estáticos
- CarteleriaWebHandler: handler de peticiones HTTP + API
- _lanzar_navegador(): abre Chrome/Edge en modo kiosk en el monitor TV
"""

import http.server
import json
import mimetypes
import os
import socketserver
import threading
import subprocess
import platform
import logging
import tempfile
import sys
from urllib.parse import parse_qs, unquote, urlparse

from src.utils.paths import get_base_path, get_resource_path
from src.carteleria.lanzador_tv.navegador_kiosk import (
    TeclasTv,
    buscar_navegador,
    flags_pantalla_completa,
)

logger = logging.getLogger("CerebroLanzadorTV")


def cargar_web_tv():
    """En el EXE: tv_cara.bin en memoria. Si falta, la carpeta la_cara_web (dev o instalado viejo)."""
    if getattr(sys, "frozen", False):
        try:
            from src.carteleria.lanzador_tv.tv_cara_pack import cargar_cara_en_memoria

            mem = cargar_cara_en_memoria()
            if mem:
                return None, mem
        except Exception:
            logger.exception("No se pudo abrir el paquete oculto de la TV")

    rel = os.path.join("src", "carteleria", "lanzador_tv", "la_cara_web")
    candidatos = [
        get_resource_path(rel),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "la_cara_web"),
        os.path.join(get_base_path(), rel),
        os.path.join(get_base_path(), "_internal", rel),
    ]
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        meipass = getattr(sys, "_MEIPASS", "")
        candidatos.extend([
            os.path.join(exe_dir, "_internal", rel),
            os.path.join(meipass, rel) if meipass else "",
        ])
    for path in candidatos:
        if path and os.path.isfile(os.path.join(path, "index.html")):
            return path, None
    return "", None


def _json_default(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


class CarteleriaWebHandler(http.server.SimpleHTTPRequestHandler):
    """Handler HTTP para servir archivos estáticos y API de cartelería"""

    def __init__(self, *args, web_root=None, main_window=None, zip_store=None, **kwargs):
        self.web_root = web_root
        self.main_window = main_window
        self.zip_store = zip_store
        dummy = web_root if web_root and os.path.isdir(web_root) else os.getcwd()
        super().__init__(*args, directory=dummy, **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self.handle_api()
            return
        if self.path.startswith("/iconos/"):
            self._serve_icono()
            return
        if self.zip_store is not None:
            self._serve_memoria()
            return
        return super().do_GET()

    def _serve_memoria(self):
        parsed = urlparse(self.path)
        rel = unquote(parsed.path or "/").lstrip("/")
        if not rel or rel.endswith("/"):
            rel = (rel + "index.html") if rel else "index.html"
        if ".." in rel.split("/"):
            self.send_error(404)
            return
        data = self.zip_store.get(rel)
        if data is None:
            self.send_error(404)
            return
        ctype = mimetypes.guess_type(rel)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path.startswith("/api/control"):
            self.handle_api()
            return
        self.send_error(404)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _serve_icono(self):
        from src.carteleria.assets_paths import ruta_archivo_icono

        name = os.path.basename(unquote(urlparse(self.path).path))
        if not name or name in (".", "..") or ".." in name:
            self.send_error(404)
            return
        ext = os.path.splitext(name)[1].lower()
        tipos = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".svg": "image/svg+xml",
        }
        if ext not in tipos:
            self.send_error(404)
            return
        full = ruta_archivo_icono(name)
        if not full:
            try:
                from src.carteleria.motor_carteleria.iconos_tv import _png_por_nombre
                alt = _png_por_nombre(os.path.splitext(name)[0])
                if alt and alt != name:
                    full = ruta_archivo_icono(alt)
            except Exception:
                full = ""
        if not full:
            self.send_error(404)
            return
        try:
            with open(full, "rb") as handle:
                data = handle.read()
        except OSError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", tipos[ext])
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def handle_api(self):
        if self.path == "/api/state":
            try:
                state = self._get_state()
            except Exception as exc:
                logger.warning("Error armando /api/state: %s", exc)
                state = {"config": {}, "precios": []}
            self._write_json(state)
            return

        if self.path == "/api/precios":
            try:
                precios = self._get_precios()
            except Exception as exc:
                logger.warning("Error obteniendo precios: %s", exc)
                precios = []
            self._write_json({"precios": precios})
            return

        if self.path.startswith("/api/control"):
            self._handle_control()
            return

        self._write_json({"error": "Not found"}, status=404)

    def _handle_control(self):
        action = ""
        parsed = urlparse(self.path)
        action = (parse_qs(parsed.query).get("action") or [""])[0].strip().lower()
        if not action and self.command == "POST":
            try:
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b""
                action = str(json.loads(raw.decode("utf-8") or "{}").get("action") or "").strip().lower()
            except Exception:
                action = ""
        mw = self.main_window
        if mw and hasattr(mw, "on_tv_control"):
            mw.on_tv_control(action)
        elif mw and hasattr(mw, "_cerebro") and mw._cerebro:
            if action in ("stop", "f11", "esc"):
                mw._cerebro.detener()
            elif action in ("monitor", "f10"):
                mw._cerebro.reubicar((getattr(mw._cerebro, "screen_index", 0) or 0) + 1)
        self._write_json({"ok": True, "action": action})

    def _write_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, default=_json_default).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _get_state(self):
        if self.main_window and hasattr(self.main_window, "get_web_state"):
            return self.main_window.get_web_state()
        try:
            from src.config import config
            return {
                "config": {
                    "business_name": config.get("business_name", "Cartelería"),
                    "phone": config.get("phone", ""),
                    "mensaje_zocalo": config.get("mensaje_zocalo", ""),
                    "carteleria_theme": config.get("carteleria_theme", "temu"),
                },
                "precios": self._get_precios(),
            }
        except Exception as exc:
            logger.warning("No se pudo construir el estado de cartelería: %s", exc)
            return {"config": {}, "precios": []}

    def _get_precios(self):
        precios = []
        if self.main_window and hasattr(self.main_window, "rows_precios"):
            precios = self.main_window.rows_precios or []
        return precios

    def log_message(self, format, *args):
        pass


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class ServidorCuello:
    """Servidor HTTP + navegador kiosk para cartelería TV."""

    def __init__(self, main_window=None, host="127.0.0.1", port=0):
        self.main_window = main_window
        self.host = host
        self.port = port
        self.httpd = None
        self.thread = None
        self.browser_process = None
        self.screen_index = None
        self.web_root, self.zip_store = cargar_web_tv()
        self._kiosk_profile = os.path.join(tempfile.gettempdir(), "tpv-carteleria-kiosk")
        self._teclas = None
        self.last_error = ""

    def iniciar(self, screen_index=None):
        try:
            self.last_error = ""
            if screen_index is not None:
                self.screen_index = screen_index
            self.web_root, self.zip_store = cargar_web_tv()
            tiene_mem = bool(self.zip_store and "index.html" in self.zip_store)
            tiene_disco = bool(self.web_root and os.path.isfile(os.path.join(self.web_root, "index.html")))
            if not tiene_mem and not tiene_disco:
                self.last_error = (
                    "Falta la cara web de la TV (index.html).\n"
                    f"Buscada en:\n{self.web_root or '(paquete en memoria)'}"
                )
                logger.warning("Cara web TV no encontrada")
                return False

            if not self.httpd:
                handler = lambda *args, **kwargs: CarteleriaWebHandler(
                    *args,
                    web_root=self.web_root,
                    main_window=self.main_window,
                    zip_store=self.zip_store,
                    **kwargs
                )
                self.httpd = ThreadedHTTPServer((self.host, self.port), handler)
                self.port = self.httpd.server_address[1]
                self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
                self.thread.start()
                logger.info("Servidor HTTP iniciado en http://%s:%s", self.host, self.port)

            self._lanzar_navegador()
            self._iniciar_teclas()
            return True
        except Exception as exc:
            self.last_error = str(exc)
            logger.error("Error iniciando servidor: %s", exc)
            return False

    def reubicar(self, screen_index):
        self.screen_index = screen_index
        if self.httpd:
            self._lanzar_navegador()

    def detener(self):
        try:
            self._detener_teclas()
            self._cerrar_navegador()
            if self.httpd:
                try:
                    self.httpd.shutdown()
                except Exception:
                    pass
                try:
                    self.httpd.server_close()
                except Exception:
                    pass
                self.httpd = None
            self.thread = None
            logger.info("Servidor HTTP y navegador detenidos")
        except Exception as exc:
            logger.error("Error deteniendo servidor: %s", exc)

    def _iniciar_teclas(self):
        if self._teclas:
            return
        parent = self.main_window if isinstance(self.main_window, object) else None
        try:
            from PyQt6.QtCore import QObject
            if not isinstance(parent, QObject):
                parent = None
        except Exception:
            parent = None
        self._teclas = TeclasTv(
            on_f10=self._tecla_f10,
            on_f11=self._tecla_salir,
            on_esc=self._tecla_salir,
            parent=parent,
        )
        self._teclas.start()

    def _detener_teclas(self):
        if not self._teclas:
            return
        self._teclas.stop()
        self._teclas = None

    def _tecla_f10(self):
        mw = self.main_window
        if mw and hasattr(mw, "on_tv_control"):
            mw.on_tv_control("monitor")
            return
        try:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            n = len(app.screens()) if app else 1
        except Exception:
            n = 1
        self.screen_index = ((self.screen_index or 0) + 1) % max(n, 1)
        self.reubicar(self.screen_index)

    def _tecla_salir(self):
        mw = self.main_window
        if mw and hasattr(mw, "on_tv_control"):
            mw.on_tv_control("stop")
            return
        self.detener()

    def _cerrar_navegador(self):
        if not self.browser_process:
            return
        try:
            if platform.system() == "Windows":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(self.browser_process.pid)],
                    capture_output=True,
                    check=False,
                )
            else:
                self.browser_process.terminate()
                try:
                    self.browser_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.browser_process.kill()
        except Exception as exc:
            logger.warning("Error cerrando navegador: %s", exc)
        self.browser_process = None

    def _geometria_tv(self):
        try:
            from PyQt6.QtWidgets import QApplication

            app = QApplication.instance()
            if not app:
                return 0, 0, 1920, 1080
            screens = app.screens()
            if not screens:
                return 0, 0, 1920, 1080
            if self.screen_index is not None and 0 <= self.screen_index < len(screens):
                screen = screens[self.screen_index]
            else:
                screen = app.primaryScreen() or screens[0]
            geo = screen.geometry()
            return geo.x(), geo.y(), geo.width(), geo.height()
        except Exception:
            return 0, 0, 1920, 1080

    def _flags_kiosk(self, url):
        x, y, w, h = self._geometria_tv()
        return flags_pantalla_completa(url, self._kiosk_profile, x, y, w, h)

    def _lanzar_navegador(self):
        try:
            self._cerrar_navegador()
            url = f"http://{self.host}:{self.port}/"
            sistema = platform.system()
            flags = self._flags_kiosk(url)
            navegador = buscar_navegador()

            if sistema == "Windows":
                if navegador:
                    self.browser_process = subprocess.Popen([navegador] + flags)
                else:
                    logger.warning("No hay Chrome ni Edge; abro el navegador por defecto")
                    os.startfile(url)
            elif sistema == "Darwin":
                self.browser_process = subprocess.Popen(
                    ["open", "-a", navegador or "Google Chrome", "--args"] + flags
                )
            else:
                if navegador:
                    self.browser_process = subprocess.Popen([navegador] + flags)
                else:
                    subprocess.Popen(["xdg-open", url])

            logger.info("TV en %s con %s", url, navegador or "navegador por defecto")
        except Exception as exc:
            logger.error("Error lanzando navegador: %s", exc)
