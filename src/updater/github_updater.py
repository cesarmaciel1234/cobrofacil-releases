"""
github_updater.py — Fachada de actualizaciones vía GitHub

- EXE congelado: delega en silent_auto_updater (ZIP de Releases).
- Modo desarrollo: sync por archivos desde el repo fuente (cobrofacil-pro).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import ssl
import sys
import urllib.request
from datetime import datetime

from src.utils.paths import get_base_path

BASE_DIR = get_base_path()
VERSION_FILE = os.path.join(BASE_DIR, "version.json")
BACKUP_DIR = os.path.join(BASE_DIR, "reportes", "backups_actualizacion")
RAW_BASE_URL = "https://raw.githubusercontent.com/cesarmaciel1234/cobrofacil-pro/main"
MODULOS_CORE = ("main.py", "src/main_window.py", "src/config.py")


def get_local_version():
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("app_version", "0.0.0")
        except Exception:
            pass
    return "0.0.0"


def set_local_version(version_tag):
    data = {}
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
        except Exception:
            data = {}
    data["app_version"] = version_tag
    try:
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _calcular_checksum(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""


def _leer_version_local() -> dict:
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"app_version": "0.0.0", "modules": {}}


class ResultadoGitHub:
    def __init__(self):
        self.actualizados = []
        self.errores = []
        self.necesita_reinicio = False
        self.version_nueva = ""
        self.version_local = ""
        self.canal = "stable"

    @property
    def hay_cambios(self):
        return bool(self.actualizados)


def verificar_actualizaciones_github(dry_run=False, callback_progreso=None):
    """Punto de entrada usado por banner admin / diálogo de actualizaciones."""
    if getattr(sys, "frozen", False):
        from src.updater.silent_auto_updater import (
            is_update_available,
            is_update_staged,
            download_and_stage_update,
        )

        res = ResultadoGitHub()
        if is_update_staged():
            pending_path = os.path.join(get_base_path(), "_update_cache", "pending.json")
            try:
                with open(pending_path, encoding="utf-8") as f:
                    pending = json.load(f)
                res.version_nueva = pending.get("remote_version", "")
            except Exception:
                pass
            res.version_local = get_local_version()
            res.actualizados = ["CobroFacil_POS_Release.zip"]
            res.necesita_reinicio = True
            return res

        available, local, remote = is_update_available()
        res.version_local = local
        res.version_nueva = remote
        if not available:
            return res
        res.actualizados = ["CobroFacil_POS_Release.zip"]
        if dry_run:
            return res
        if download_and_stage_update(
            progress_callback=lambda m: callback_progreso(50, m) if callback_progreso else None
        ):
            res.necesita_reinicio = True
        else:
            res.errores.append("No se pudo descargar la actualización desde GitHub.")
        return res

    return _verificar_modulos_dev(dry_run=dry_run, callback_progreso=callback_progreso)


def _verificar_modulos_dev(dry_run=False, callback_progreso=None):
    """Sync por checksums en entorno de desarrollo (no congelado)."""
    res = ResultadoGitHub()

    def progreso(pct, msg):
        if callback_progreso:
            callback_progreso(pct, msg)

    progreso(10, "Verificando actualizaciones en GitHub...")

    ctx = ssl.create_default_context()
    try:
        req = urllib.request.Request(
            f"{RAW_BASE_URL}/version.json",
            headers={"User-Agent": "CobroFacil-Updater"},
        )
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            manifest_remoto = json.loads(r.read().decode("utf-8-sig"))
    except Exception as e:
        res.errores.append(f"No se pudo descargar version.json desde GitHub: {e}")
        return res

    res.version_nueva = manifest_remoto.get("app_version", "")
    res.canal = manifest_remoto.get("channel", "stable")

    manifest_local = _leer_version_local()
    res.version_local = manifest_local.get("app_version", "0.0.0")
    modulos_remotos = manifest_remoto.get("modules", {}) or {}

    progreso(30, "Comparando archivos con GitHub...")
    modulos_a_actualizar = []
    for rel_path, info_remota in modulos_remotos.items():
        abs_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
        chk_local = _calcular_checksum(abs_path) if os.path.exists(abs_path) else ""
        chk_remoto = (info_remota or {}).get("checksum", "")
        if chk_remoto and chk_remoto != chk_local:
            modulos_a_actualizar.append((rel_path, info_remota))

    if not modulos_a_actualizar:
        progreso(100, "Ya estás en la última versión de GitHub.")
        return res

    if dry_run:
        res.actualizados = [m[0] for m in modulos_a_actualizar]
        return res

    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"backup_{ts}")
    os.makedirs(backup_path, exist_ok=True)

    total = len(modulos_a_actualizar)
    for idx, (rel_path, info_remota) in enumerate(modulos_a_actualizar):
        pct = 30 + int(60 * idx / max(total, 1))
        progreso(pct, f"Descargando de GitHub: {os.path.basename(rel_path)}...")

        abs_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
        if os.path.exists(abs_path):
            bk = os.path.join(backup_path, rel_path.replace("/", "_"))
            try:
                shutil.copy2(abs_path, bk)
            except Exception:
                pass

        try:
            req_file = urllib.request.Request(
                f"{RAW_BASE_URL}/{rel_path.replace(os.sep, '/')}",
                headers={"User-Agent": "CobroFacil-Updater"},
            )
            with urllib.request.urlopen(req_file, timeout=20, context=ctx) as r:
                contenido = r.read()
        except Exception as e:
            res.errores.append(f"No se pudo descargar {rel_path}: {e}")
            continue

        if hashlib.md5(contenido).hexdigest() != (info_remota or {}).get("checksum", ""):
            res.errores.append(f"Checksum inválido para {rel_path}")
            continue

        os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)
        try:
            with open(abs_path, "wb") as f:
                f.write(contenido)
            res.actualizados.append(rel_path)
        except Exception as e:
            res.errores.append(f"Error escribiendo {rel_path}: {e}")

        if any(rel_path.startswith(m) for m in MODULOS_CORE):
            res.necesita_reinicio = True

    if res.actualizados:
        manifest_local["app_version"] = res.version_nueva
        manifest_local.setdefault("modules", {})
        for rel_path, info in modulos_remotos.items():
            if rel_path in res.actualizados:
                manifest_local["modules"][rel_path] = info
        try:
            with open(VERSION_FILE, "w", encoding="utf-8") as f:
                json.dump(manifest_local, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    progreso(100, f"{len(res.actualizados)} módulos actualizados desde GitHub.")
    return res
