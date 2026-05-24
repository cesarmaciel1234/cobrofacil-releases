"""
update_client.py  — Cliente de Actualizaciones LAN / WiFi
==========================================================
Corre en las PCs CLIENTE al arrancar la aplicación.
Busca al servidor maestro en la red, compara versiones y descarga
solo los archivos que cambiaron.

Estrategia:
  1. Usar IP del servidor guardada en config.json ("update_server_ip")
  2. Si no hay, hacer broadcast UDP para descubrir al servidor automáticamente
  3. Comparar checksums con version.json local
  4. Descargar solo archivos modificados
  5. Reemplazar y reiniciar si es necesario
"""

import os
import json
import hashlib
import socket
import shutil
from datetime import datetime
from typing import Optional

UPDATE_PORT     = 38001
DISCOVER_PORT   = 38002      # Puerto UDP para descubrimiento
TIMEOUT_SEG     = 3
BASE_DIR        = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VERSION_FILE    = os.path.join(BASE_DIR, "version.json")
BACKUP_DIR      = os.path.join(BASE_DIR, "reportes", "backups_actualizacion")

# ── Utilidades ───────────────────────────────────────────────────────────────
def calcular_checksum(path: str) -> str:
    try:
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return ""

def leer_version_local() -> dict:
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"app_version": "0.0.0", "modules": {}}

# ── Descubrimiento del servidor ───────────────────────────────────────────────
def descubrir_servidor() -> Optional[str]:
    """Busca el servidor maestro via UDP broadcast en la red local."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(TIMEOUT_SEG)
        sock.sendto(b"PUNPRO_UPDATE_DISCOVER", ("<broadcast>", DISCOVER_PORT))
        data, addr = sock.recvfrom(1024)
        resp = json.loads(data.decode())
        if resp.get("update_server"):
            return addr[0]
    except:
        pass
    return None

def get_update_token() -> str:
    try:
        from src.config import config
        token = config.get("update_auth_token", "")
        if not token:
            token = config.get("server_password", "")
        return str(token or "").strip()
    except Exception:
        return ""


def _build_request(url: str):
    import urllib.request
    req = urllib.request.Request(url, headers={'User-Agent': 'CajaFacil-Updater'})
    token = get_update_token()
    if token:
        req.add_header('X-Update-Token', token)
    return req


def fetch_json(ip: str, path: str) -> Optional[dict]:
    """Descarga y parsea un JSON del servidor."""
    try:
        import urllib.request
        url = f"http://{ip}:{UPDATE_PORT}{path}"
        req = _build_request(url)
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEG) as r:
            return json.loads(r.read().decode('utf-8'))
    except:
        return None


def fetch_bytes(ip: str, rel_path: str) -> Optional[bytes]:
    """Descarga el contenido binario de un archivo del servidor."""
    try:
        import urllib.request
        url = f"http://{ip}:{UPDATE_PORT}/file/{rel_path}"
        req = _build_request(url)
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read()
    except:
        return None

def ping_servidor(ip: str) -> bool:
    try:
        resp = fetch_json(ip, "/status")
        return resp is not None and resp.get("ok", False)
    except:
        return False


# ── Lógica principal de actualización ────────────────────────────────────────
class ResultadoActualizacion:
    def __init__(self):
        self.actualizados: list  = []   # rutas de archivos actualizados
        self.errores: list       = []
        self.necesita_reinicio: bool = False
        self.version_nueva: str  = ""
        self.version_local: str  = ""
        self.canal: str          = "stable"
    
    @property
    def hay_cambios(self) -> bool:
        return bool(self.actualizados)


def verificar_actualizaciones(
    server_ip: str = "",
    canal_filtro: str = "stable",
    solo_modulos: list = None,
    dry_run: bool = False,
    callback_progreso=None
) -> ResultadoActualizacion:
    """
    Parámetros:
      server_ip      → IP del servidor maestro (vacío = autodescubrimiento)
      canal_filtro   → "stable" o "beta"
      solo_modulos   → lista de rutas relativas para actualizar solo esos módulos
                       ej: ["src/cajero/paso5_terminal.py"]
                       None = todos
      dry_run        → True = solo reportar diferencias, no descargar nada
      callback_progreso → función(porcentaje, mensaje) para actualizar UI
    """
    res = ResultadoActualizacion()
    
    def progreso(pct, msg):
        if callback_progreso:
            callback_progreso(pct, msg)
    
    # 1. Resolver IP del servidor
    progreso(5, "Buscando servidor de actualizaciones...")
    if not server_ip:
        try:
            from src.config import config
            server_ip = config.get("update_server_ip", "")
        except:
            pass
    
    if not server_ip or not ping_servidor(server_ip):
        ip_descubierta = descubrir_servidor()
        if ip_descubierta and ping_servidor(ip_descubierta):
            server_ip = ip_descubierta
        else:
            res.errores.append("No se encontró el servidor de actualizaciones en la red.")
            return res
    
    progreso(15, f"Conectado al servidor {server_ip}")
    
    # 2. Descargar manifest remoto
    progreso(20, "Descargando manifest de versiones...")
    manifest_remoto = fetch_json(server_ip, "/version.json")
    if not manifest_remoto:
        res.errores.append("No se pudo descargar el manifest del servidor.")
        return res
    
    res.version_nueva = manifest_remoto.get("app_version", "")
    res.canal = manifest_remoto.get("channel", "stable")
    
    # 3. Leer versiones locales
    manifest_local = leer_version_local()
    res.version_local = manifest_local.get("app_version", "0.0.0")
    modulos_locales = manifest_local.get("modules", {})
    modulos_remotos = manifest_remoto.get("modules", {})
    
    # 4. Detectar diferencias
    progreso(30, "Comparando versiones de módulos...")
    modulos_a_actualizar = []
    
    for rel_path, info_remota in modulos_remotos.items():
        # Filtro por canal
        canal_modulo = info_remota.get("channel", "stable")
        if canal_filtro == "stable" and canal_modulo == "beta":
            continue  # Saltar betas en canal estable
        
        # Filtro por módulo específico
        if solo_modulos and rel_path not in solo_modulos:
            continue
        
        # Comparar checksum
        abs_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
        chk_local = modulos_locales.get(rel_path, {}).get("checksum", "")
        chk_local_real = calcular_checksum(abs_path) if os.path.exists(abs_path) else ""
        chk_remoto = info_remota.get("checksum", "")
        
        if chk_remoto and chk_remoto != chk_local_real:
            modulos_a_actualizar.append((rel_path, info_remota))
    
    if not modulos_a_actualizar:
        progreso(100, "✅ Ya estás en la última versión.")
        return res
    
    if dry_run:
        res.actualizados = [m[0] for m in modulos_a_actualizar]
        return res
    
    # 5. Hacer backup de archivos a reemplazar
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"backup_{ts}")
    os.makedirs(backup_path, exist_ok=True)
    
    total = len(modulos_a_actualizar)
    for idx, (rel_path, info_remota) in enumerate(modulos_a_actualizar):
        pct = 30 + int(60 * idx / total)
        progreso(pct, f"Actualizando {os.path.basename(rel_path)}...")
        
        abs_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
        
        # Backup del archivo existente
        if os.path.exists(abs_path):
            bk = os.path.join(backup_path, rel_path.replace("/", "_"))
            try:
                shutil.copy2(abs_path, bk)
            except:
                pass
        
        # Descargar nuevo archivo
        contenido = fetch_bytes(server_ip, rel_path)
        if contenido is None:
            res.errores.append(f"No se pudo descargar: {rel_path}")
            continue
        
        # Verificar checksum del archivo descargado
        chk_descargado = hashlib.md5(contenido).hexdigest()
        if chk_descargado != info_remota.get("checksum", ""):
            res.errores.append(f"Checksum inválido: {rel_path}")
            continue
        
        # Escribir archivo
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        try:
            with open(abs_path, 'wb') as f:
                f.write(contenido)
            res.actualizados.append(rel_path)
        except Exception as e:
            res.errores.append(f"Error escribiendo {rel_path}: {e}")
        
        # Determinar si necesita reinicio (módulos del core)
        MODULOS_CORE = ['main.py', 'src/main_window.py', 'src/config.py']
        if any(rel_path.startswith(m) for m in MODULOS_CORE):
            res.necesita_reinicio = True
    
    # 6. Actualizar version.json local
    if res.actualizados:
        manifest_local["app_version"] = res.version_nueva
        manifest_local.setdefault("modules", {})
        for rel_path, info in modulos_remotos.items():
            if rel_path in res.actualizados:
                manifest_local["modules"][rel_path] = info
        try:
            with open(VERSION_FILE, 'w') as f:
                json.dump(manifest_local, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    progreso(100, f"✅ {len(res.actualizados)} módulos actualizados.")
    return res
