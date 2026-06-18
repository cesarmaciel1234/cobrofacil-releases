"""Cliente de actualizaciones LAN para CobroFacil POS."""
import hashlib
import json
import os
import shutil
import socket
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VERSION_FILE = os.path.join(BASE_DIR, "version.json")
BACKUP_DIR = os.path.join(BASE_DIR, "reportes", "backups_actualizacion")
UPDATE_PORT = 38001
UPDATE_DISCOVERY_PORT = 38002
MODULOS_CORE = ['main.py', 'src/main_window.py', 'src/config.py']


@dataclass
class ResultadoActualizacion:
    hay_cambios: bool = False
    actualizados: list = field(default_factory=list)
    errores: list = field(default_factory=list)
    version_local: str = ""
    version_nueva: str = ""
    canal: str = "stable"
    necesita_reinicio: bool = False


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def calcular_checksum(path: str) -> str:
    try:
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""


def leer_version_local() -> dict:
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"app_version": "0.0.0", "modules": {}}


def _get_update_token() -> str:
    try:
        from src.config import config
        token = config.get("update_auth_token", "")
        if not token:
            token = config.get("server_password", "")
        return str(token or "").strip()
    except Exception:
        return ""


def _descubrir_servidor_update() -> str:
    from src.config import config
    ip_cfg = config.get("update_server_ip", "").strip()
    if ip_cfg:
        return ip_cfg

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(2.0)
    try:
        sock.sendto(b"PUNPRO_UPDATE_DISCOVER", ('255.255.255.255', UPDATE_DISCOVERY_PORT))
        data, _addr = sock.recvfrom(1024)
        info = json.loads(data.decode('utf-8'))
        if info.get('update_server'):
            return info.get('server_ip', _addr[0])
    except Exception:
        pass
    finally:
        sock.close()
    return ""


def verificar_actualizaciones(dry_run=False, callback_progreso=None):
    res = ResultadoActualizacion()

    def progreso(pct, msg):
        if callback_progreso:
            callback_progreso(pct, msg)

    progreso(10, "Buscando servidor de actualizaciones en la red...")
    server_ip = _descubrir_servidor_update()
    if not server_ip:
        res.errores.append("No se encontró servidor de actualizaciones en la LAN.")
        return res

    progreso(20, f"Conectando a {server_ip}:{UPDATE_PORT}...")
    token = _get_update_token()
    headers = {'User-Agent': 'CobroFacil-Updater'}
    if token:
        headers['X-Update-Token'] = token

    try:
        req = urllib.request.Request(
            f"http://{server_ip}:{UPDATE_PORT}/version.json",
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            manifest_remoto = json.loads(r.read().decode('utf-8'))
    except Exception as e:
        res.errores.append(f"No se pudo descargar version.json: {e}")
        return res

    manifest_local = leer_version_local()
    res.version_local = manifest_local.get("app_version", "0.0.0")
    res.version_nueva = manifest_remoto.get("app_version", "")
    res.canal = manifest_remoto.get("channel", "stable")

    modulos_remotos = manifest_remoto.get("modules", {})
    progreso(40, "Comparando archivos...")
    modulos_a_actualizar = []
    for rel_path, info_remota in modulos_remotos.items():
        abs_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
        chk_local = calcular_checksum(abs_path) if os.path.exists(abs_path) else ""
        chk_remoto = info_remota.get("checksum", "")
        if chk_remoto and chk_remoto != chk_local:
            modulos_a_actualizar.append((rel_path, info_remota))

    if not modulos_a_actualizar:
        progreso(100, "Ya estás en la última versión.")
        return res

    res.hay_cambios = True
    if dry_run:
        res.actualizados = [m[0] for m in modulos_a_actualizar]
        return res

    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"backup_{ts}")
    os.makedirs(backup_path, exist_ok=True)

    total = len(modulos_a_actualizar)
    for idx, (rel_path, info_remota) in enumerate(modulos_a_actualizar):
        pct = 40 + int(50 * idx / total)
        progreso(pct, f"Descargando: {os.path.basename(rel_path)}...")

        abs_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
        if os.path.exists(abs_path):
            bk = os.path.join(backup_path, rel_path.replace("/", "_"))
            try:
                shutil.copy2(abs_path, bk)
            except Exception:
                pass

        try:
            req_file = urllib.request.Request(
                f"http://{server_ip}:{UPDATE_PORT}/file/{rel_path}",
                headers=headers
            )
            with urllib.request.urlopen(req_file, timeout=15) as r:
                contenido = r.read()
        except Exception as e:
            res.errores.append(f"No se pudo descargar {rel_path}: {e}")
            continue

        chk_descargado = hashlib.md5(contenido).hexdigest()
        if chk_descargado != info_remota.get("checksum", ""):
            res.errores.append(f"Checksum inválido para {rel_path}")
            continue

        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        try:
            with open(abs_path, 'wb') as f:
                f.write(contenido)
            res.actualizados.append(rel_path)
        except Exception as e:
            res.errores.append(f"Error escribiendo {rel_path}: {e}")
            continue

        if any(rel_path.startswith(m) for m in MODULOS_CORE):
            res.necesita_reinicio = True

    if res.actualizados:
        manifest_local["app_version"] = res.version_nueva
        manifest_local.setdefault("modules", {})
        for rel_path, info in modulos_remotos.items():
            if rel_path in res.actualizados:
                manifest_local["modules"][rel_path] = info
        try:
            with open(VERSION_FILE, 'w', encoding='utf-8') as f:
                json.dump(manifest_local, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    progreso(100, f"{len(res.actualizados)} módulos actualizados desde la LAN.")
    return res
