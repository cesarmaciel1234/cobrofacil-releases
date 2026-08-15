"""
Cerebro Lanzador TV — Servidor HTTP + navegador kiosk

Responsabilidades:
- ServidorCuello: servidor HTTP de archivos estáticos
- CarteleriaWebHandler: handler de peticiones HTTP + API
- _lanzar_navegador(): abre Chrome/Edge en modo kiosk en el monitor TV
"""

import http.server
import json
import os
import socketserver
import threading
import subprocess
import platform
import logging
import tempfile

from src.utils.paths import get_resource_path

logger = logging.getLogger("CerebroLanzadorTV")


def _json_default(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


class CarteleriaWebHandler(http.server.SimpleHTTPRequestHandler):
    """Handler HTTP para servir archivos estáticos y API de cartelería"""

    def __init__(self, *args, web_root=None, main_window=None, **kwargs):
        self.web_root = web_root
        self.main_window = main_window
        super().__init__(*args, directory=web_root, **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self.handle_api()
            return
        return super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

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

        self._write_json({"error": "Not found"}, status=404)

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
        if self.main_window and hasattr(self.main_window, "rows_precios"):
            return self.main_window.rows_precios or []
        return []

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
        self.web_root = get_resource_path(
            os.path.join("src", "carteleria", "lanzador_tv", "la_cara_web")
        )
        self._kiosk_profile = os.path.join(tempfile.gettempdir(), "tpv-carteleria-kiosk")

    def iniciar(self, screen_index=None):
        try:
            if screen_index is not None:
                self.screen_index = screen_index
            if not os.path.isdir(self.web_root):
                logger.warning("Directorio web_root no encontrado: %s", self.web_root)
                return False

            if not self.httpd:
                handler = lambda *args, **kwargs: CarteleriaWebHandler(
                    *args,
                    web_root=self.web_root,
                    main_window=self.main_window,
                    **kwargs
                )
                self.httpd = ThreadedHTTPServer((self.host, self.port), handler)
                self.port = self.httpd.server_address[1]
                self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
                self.thread.start()
                logger.info("Servidor HTTP iniciado en http://%s:%s", self.host, self.port)

            self._lanzar_navegador()
            return True
        except Exception as exc:
            logger.error("Error iniciando servidor: %s", exc)
            return False

    def reubicar(self, screen_index):
        self.screen_index = screen_index
        if self.httpd:
            self._lanzar_navegador()

    def detener(self):
        try:
            self._cerrar_navegador()
            if self.httpd:
                self.httpd.shutdown()
                self.httpd.server_close()
                self.httpd = None
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=1)
            self.thread = None
            logger.info("Servidor HTTP y navegador detenidos")
        except Exception as exc:
            logger.error("Error deteniendo servidor: %s", exc)

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
            from src.utils.qt_dpi import secondary_screen

            app = QApplication.instance()
            if not app:
                return 0, 0, 1920, 1080
            screens = app.screens()
            if not screens:
                return 0, 0, 1920, 1080
            if self.screen_index is not None and 0 <= self.screen_index < len(screens):
                screen = screens[self.screen_index]
            else:
                screen = secondary_screen(app) or (screens[-1] if len(screens) > 1 else screens[0])
            geo = screen.geometry()
            return geo.x(), geo.y(), geo.width(), geo.height()
        except Exception:
            return 0, 0, 1920, 1080

    def _flags_kiosk(self, url):
        x, y, w, h = self._geometria_tv()
        os.makedirs(self._kiosk_profile, exist_ok=True)
        return [
            f"--user-data-dir={self._kiosk_profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-features=Translate,InfiniteSessionRestore",
            "--disable-session-crashed-bubble",
            "--disable-infobars",
            "--disable-restore-session-state",
            "--noerrdialogs",
            "--kiosk",
            "--start-fullscreen",
            f"--window-position={x},{y}",
            f"--window-size={w},{h}",
            url,
        ]

    def _buscar_chrome_windows(self):
        candidatos = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        ]
        for path in candidatos:
            if path and os.path.exists(path):
                return path
        return None

    def _lanzar_navegador(self):
        try:
            self._cerrar_navegador()
            url = f"http://{self.host}:{self.port}/"
            sistema = platform.system()

            if sistema == "Windows":
                navegador = self._buscar_chrome_windows()
                if navegador:
                    self.browser_process = subprocess.Popen(
                        [navegador] + self._flags_kiosk(url)
                    )
                else:
                    os.startfile(url)
            elif sistema == "Darwin":
                self.browser_process = subprocess.Popen(
                    ["open", "-a", "Google Chrome", "--args"] + self._flags_kiosk(url)
                )
            else:
                for binario in ("google-chrome", "chromium-browser", "chromium", "microsoft-edge"):
                    try:
                        self.browser_process = subprocess.Popen(
                            [binario] + self._flags_kiosk(url)
                        )
                        break
                    except FileNotFoundError:
                        continue
                if self.browser_process is None:
                    subprocess.Popen(["xdg-open", url])

            logger.info("Navegador kiosk en %s", url)
        except Exception as exc:
            logger.error("Error lanzando navegador: %s", exc)
