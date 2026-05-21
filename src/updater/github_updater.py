"""
github_updater.py — Actualización por GitHub (internet)
========================================================
No requiere servidor LAN. Descarga actualizaciones directamente
desde el repositorio privado de GitHub.

Uso desde admin15:
    from src.updater.github_updater import verificar_actualizaciones_github
"""

import os
import json
import hashlib
import shutil
import ssl
import urllib.request
from datetime import datetime

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VERSION_FILE = os.path.join(BASE_DIR, "version.json")
BACKUP_DIR   = os.path.join(BASE_DIR, "reportes", "backups_actualizacion")

GITHUB_REPO   = "cesarmaciel1234/cajafacil-pro"
GITHUB_BRANCH = "main"
GITHUB_RAW    = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"


def _md5(path: str) -> str:
    try:
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return ""


def _leer_local() -> dict:
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"app_version": "0.0.0", "modules": {}}


def _fetch(url: str, timeout: int = 10) -> bytes:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(url, timeout=timeout, context=ctx) as r:
        return r.read()


class ResultadoGitHub:
    def __init__(self):
        self.actualizados: list = []
        self.errores:      list = []
        self.version_local:  str = ""
        self.version_nueva:  str = ""
        self.necesita_reinicio: bool = False

    @property
    def hay_cambios(self) -> bool:
        return bool(self.actualizados)


def verificar_actualizaciones_github(
    dry_run: bool = False,
    callback_progreso=None
) -> ResultadoGitHub:
    """
    Compara version.json de GitHub con el local.
    Descarga solo los archivos que cambiaron.

    dry_run=True → solo reporta diferencias, no descarga nada.
    """
    res = ResultadoGitHub()

    def prog(pct, msg):
        if callback_progreso:
            callback_progreso(pct, msg)

    prog(5, "Conectando a GitHub...")

    # 1. Descargar manifest remoto
    try:
        data = _fetch(f"{GITHUB_RAW}/version.json")
        manifest_remoto = json.loads(data.decode('utf-8'))
    except Exception as e:
        res.errores.append(f"Sin conexión a GitHub: {e}")
        return res

    res.version_nueva = manifest_remoto.get("app_version", "")
    prog(15, f"GitHub: v{res.version_nueva}")

    # 2. Leer local
    manifest_local = _leer_local()
    res.version_local = manifest_local.get("app_version", "0.0.0")
    modulos_remotos = manifest_remoto.get("modules", {})

    # 3. Detectar diferencias
    prog(25, "Comparando archivos...")
    a_actualizar = []
    for rel_path, info in modulos_remotos.items():
        abs_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
        chk_remoto = info.get("checksum", "")
        chk_local  = _md5(abs_path) if os.path.exists(abs_path) else ""
        if chk_remoto and chk_remoto != chk_local:
            a_actualizar.append((rel_path, info))

    if not a_actualizar:
        prog(100, f"Ya tenes la ultima version ({res.version_local})")
        return res

    if dry_run:
        res.actualizados = [m[0] for m in a_actualizar]
        prog(100, f"Se encontraron {len(a_actualizar)} archivos para actualizar")
        return res

    # 4. Backup + descarga
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bk_dir = os.path.join(BACKUP_DIR, f"backup_github_{ts}")
    os.makedirs(bk_dir, exist_ok=True)

    total = len(a_actualizar)
    for idx, (rel_path, info) in enumerate(a_actualizar):
        pct = 30 + int(60 * idx / total)
        prog(pct, f"Descargando {os.path.basename(rel_path)}...")

        abs_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))

        # Backup del archivo viejo
        if os.path.exists(abs_path):
            try:
                shutil.copy2(abs_path, os.path.join(bk_dir, rel_path.replace("/", "_")))
            except:
                pass

        # Descargar desde GitHub
        try:
            contenido = _fetch(f"{GITHUB_RAW}/{rel_path}", timeout=20)
        except Exception as e:
            res.errores.append(f"Error descargando {rel_path}: {e}")
            continue

        # Verificar integridad
        if hashlib.md5(contenido).hexdigest() != info.get("checksum", ""):
            res.errores.append(f"Checksum invalido: {rel_path}")
            continue

        # Escribir
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        try:
            with open(abs_path, 'wb') as f:
                f.write(contenido)
            res.actualizados.append(rel_path)
        except Exception as e:
            res.errores.append(f"Error escribiendo {rel_path}: {e}")

        if any(rel_path.startswith(m) for m in ['main.py', 'src/main_window.py']):
            res.necesita_reinicio = True

    # 5. Actualizar version.json local
    if res.actualizados:
        manifest_local["app_version"] = res.version_nueva
        for rp, info in modulos_remotos.items():
            if rp in res.actualizados:
                manifest_local.setdefault("modules", {})[rp] = info
        try:
            with open(VERSION_FILE, 'w', encoding='utf-8') as f:
                json.dump(manifest_local, f, indent=2, ensure_ascii=False)
        except:
            pass

    prog(100, f"{len(res.actualizados)} archivos actualizados desde GitHub")
    return res
