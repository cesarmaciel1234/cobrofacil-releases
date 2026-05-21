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
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
from urllib.parse import unquote

UPDATE_PORT = 38001
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VERSION_FILE = os.path.join(BASE_DIR, "version.json")

# ── Generar / actualizar el manifest ────────────────────────────────────────
EXCLUDED_DIRS = {
    '.venv', '__pycache__', '.git', 'build', 'dist',
    'reportes', '.gemini', 'scratch', 'backups',
    'Instalador_Final', 'utilidades_hardware',
    'ia planificacion', 'data', 'docs'
}
EXCLUDED_EXTS = {'.pyc', '.pyo', '.db', '.log', '.csv', '.zip', '.exe', '.bat', '.ps1'}

def calcular_checksum(path: str) -> str:
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def generar_manifest(canal: str = "stable") -> dict:
    """Lee todos los .py del proyecto y genera el manifest con checksums."""
    modules = {}
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
            
            # Leer canal de ese módulo del manifest existente (si existe)
            existing_channel = "stable"
            existing_version = "1.0.0"
            if os.path.exists(VERSION_FILE):
                try:
                    with open(VERSION_FILE) as vf:
                        old = json.load(vf)
                    old_mod = old.get("modules", {}).get(rel_path, {})
                    existing_channel = old_mod.get("channel", "stable")
                    existing_version = old_mod.get("version", "1.0.0")
                except:
                    pass
            
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
    with open(VERSION_FILE, 'w', encoding='utf-8') as f:
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
        data = json.dumps({"error": msg}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


# ── Servidor en hilo ─────────────────────────────────────────────────────────
_server_thread = None
_httpd = None

def iniciar_servidor(canal: str = "stable") -> bool:
    """Inicia el servidor HTTP de actualizaciones en segundo plano."""
    global _server_thread, _httpd
    if _server_thread and _server_thread.is_alive():
        return True  # Ya corriendo
    
    try:
        generar_manifest(canal)  # Actualizar manifest al iniciar
        _httpd = HTTPServer(("0.0.0.0", UPDATE_PORT), UpdateHandler)
        _server_thread = threading.Thread(target=_httpd.serve_forever, daemon=True)
        _server_thread.start()
        print(f"[UPDATER] Servidor de actualizaciones activo en puerto {UPDATE_PORT}")
        return True
    except OSError as e:
        print(f"[UPDATER] No se pudo iniciar el servidor: {e}")
        return False

def detener_servidor():
    global _httpd
    if _httpd:
        _httpd.shutdown()

def get_mi_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"
