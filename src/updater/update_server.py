"""
update_server.py  — Servidor de Actualizaciones LAN / WiFi
===========================================================
Corre en SEGUNDO PLANO en la PC MAESTRA (la tuya).
Las demás PCs de la red se conectan automáticamente y descargan solo
los archivos que cambiaron.

Puerto: 38001 (HTTP simple, sin instalar nada extra)

Endpoints:
  GET /version.json          → manifest con versiones y checksums
  GET /file/<ruta relativa>  → contenido del archivo solicitado
  GET /status                → estado del servidor (ping)
"""

import os
import json
import hashlib
import threading
import socket
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from datetime import datetime
from urllib.parse import unquote

UPDATE_PORT = 38001
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VERSION_FILE = os.path.join(BASE_DIR, "version.json")

# ── Generar / actualizar el manifest ────────────────────────────────────────
EXCLUDED_DIRS = {'.venv', '__pycache__', '.git', 'build', 'dist', 'reportes', '.gemini', 'temp_restore', 'src_backup'}
EXCLUDED_EXTS = {'.pyc', '.pyo', '.db', '.log', '.csv'}

def calcular_checksum(path: str) -> str:
    try:
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        print(f"[UPDATER] Error calculando checksum para {path}: {e}")
        return ""

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

def generar_manifest(canal: str = "stable") -> dict:
    """Lee todos los .py del proyecto y genera el manifest con checksums."""
    modules = {}
    existing_manifest = {}
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, 'r', encoding='utf-8') as vf:
                existing_manifest = json.load(vf)
        except Exception as e:
            print(f"[UPDATER] Error leyendo manifest existente: {e}")

    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for fn in files:
            ext = os.path.splitext(fn)[1]
            if ext in EXCLUDED_EXTS:
                continue
            if ext not in ('.py',):
                continue
            abs_path = os.path.join(root, fn)
            rel_path = os.path.relpath(abs_path, BASE_DIR).replace(os.sep, '/')
            
            old_mod = existing_manifest.get("modules", {}).get(rel_path, {})
            existing_channel = old_mod.get("channel", "stable")
            existing_version = old_mod.get("version", "1.0.0")
            
            modules[rel_path] = {
                "version": existing_version,
                "checksum": calcular_checksum(abs_path),
                "channel": existing_channel,
                "size": os.path.getsize(abs_path)
            }
    
    manifest = {
        "app_version": _leer_version_app(),
        "channel": canal,
        "build_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "server_host": socket.gethostname(),
        "modules": modules
    }
    with open(VERSION_FILE, 'w') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    return manifest

def _leer_version_app() -> str:
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE) as f:
                return json.load(f).get("app_version", "2026.1.0")
        except:
            pass
    return "2026.1.0"


def _get_update_token() -> str:
    try:
        from src.config import config
        token = config.get("update_auth_token", "")
        if not token:
            token = config.get("server_password", "")
        return str(token or "").strip()
    except Exception:
        return ""


# ── HTTP Handler ─────────────────────────────────────────────────────────────
class UpdateHandler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        pass  # Silenciar logs de acceso HTTP

    def do_GET(self):
        path = unquote(self.path)
        
        if path == "/status":
            self._send_json({"ok": True, "host": socket.gethostname(),
                             "time": datetime.now().isoformat()})
        
        elif path == "/version.json":
            if not self._authorize_request():
                return
            if os.path.exists(VERSION_FILE):
                with open(VERSION_FILE, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self._send_error(404, "version.json no encontrado")
        
        elif path.startswith("/file/"):
            if not self._authorize_request():
                return
            rel_path = path[6:].lstrip("/")
            abs_path = os.path.normpath(os.path.join(BASE_DIR, rel_path))
            # Seguridad: no salir del directorio base
            if not abs_path.startswith(BASE_DIR):
                self._send_error(403, "Acceso denegado")
                return
            if os.path.isfile(abs_path):
                with open(abs_path, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self._send_error(404, f"Archivo no encontrado: {rel_path}")
        
        else:
            self._send_error(404, "Endpoint no existe")

    def _send_json(self, obj: dict):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_error(self, code: int, msg: str):
        data = json.dumps({"error": msg}, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _authorize_request(self) -> bool:
        expected = _get_update_token()
        if not expected:
            return True
        token = self.headers.get('X-Update-Token', '').strip()
        if token == expected:
            return True
        client_ip = self.client_address[0] if hasattr(self, 'client_address') else 'desconocido'
        print(f"[UPDATER SERVER] Acceso no autorizado desde {client_ip}; token recibido='{token}'")
        self._send_error(401, "Token de actualización inválido")
        return False


# ── Servidor en hilo ─────────────────────────────────────────────────────────
_server_thread = None
_httpd = None

def iniciar_servidor(canal: str = "stable") -> bool:
    """Inicia el servidor HTTP de actualizaciones en segundo plano."""
    global _server_thread, _httpd
    if _server_thread and _server_thread.is_alive():
        print("[UPDATER] El servidor de actualizaciones ya estaba corriendo.")
        return True  # Ya corriendo
    
    try:
        generar_manifest(canal)  # Actualizar manifest al iniciar
        _httpd = ThreadingHTTPServer(("0.0.0.0", UPDATE_PORT), UpdateHandler)
        _server_thread = threading.Thread(target=_httpd.serve_forever, daemon=True)
        _server_thread.start()
        print(f"[UPDATER] Servidor de actualizaciones activo en puerto {UPDATE_PORT} ({get_mi_ip()})")
        return True
    except OSError as e:
        print(f"[UPDATER] No se pudo iniciar el servidor: {e}")
        return False

def detener_servidor():
    global _httpd
    if _httpd:
        try:
            _httpd.shutdown()
            _httpd.server_close()
        except Exception as e:
            print(f"[UPDATER] Error deteniendo servidor: {e}")
        finally:
            _httpd = None

if __name__ == "__main__":
    iniciar_servidor()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[UPDATER] Servidor detenido por interrupción del usuario.")
        detener_servidor()


def get_mi_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"
