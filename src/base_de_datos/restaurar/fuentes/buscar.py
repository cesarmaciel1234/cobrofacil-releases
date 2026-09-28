"""Busca copias para restaurar: respaldos del admin (.sql, .zip, .db) y copias del jefe (espejo, pendrive)."""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sqlite3
import zipfile
from dataclasses import dataclass

PROFUNDIDAD = 3
MAX_ARCHIVOS = 400
MIN_SQL = 5000
MIN_ZIP = 50000
SALTEAR = {"$recycle.bin", "system volume information", "catalogos", ".git", "node_modules", "__pycache__"}
PREFIJOS_ZIP = ("backup_", "pre_restore_", "respaldo_")
_FECHA = re.compile(r"(20\d{2})-?(\d{2})-?(\d{2})(?:[_-](\d{2})(\d{2})(\d{2}))?")
ETIQUETAS = {
    "sql": "Respaldo MariaDB (.sql)",
    "zip": "Respaldo físico MariaDB (.zip)",
    "sqlite": "Respaldo SQLite (.db)",
    "copia": "Copia del jefe",
}


@dataclass
class Fuente:
    ruta: str
    tipo: str  # sql | zip | sqlite | copia
    fecha: _dt.datetime
    completa: bool
    tablas: int = 0
    servidor: str = ""
    detalle: str = ""

    @property
    def nombre(self) -> str:
        return os.path.basename(self.ruta)

    @property
    def etiqueta(self) -> str:
        return ETIQUETAS.get(self.tipo, self.tipo)


def _fecha_nombre(nombre: str) -> _dt.datetime | None:
    m = _FECHA.search(nombre)
    if not m or not m.group(4):
        return None
    try:
        return _dt.datetime(*(int(g) for g in m.groups()))
    except ValueError:
        return None


def _fecha_archivo(path: str) -> _dt.datetime:
    return _fecha_nombre(os.path.basename(path)) or _dt.datetime.fromtimestamp(os.path.getmtime(path))


def _fecha_texto(texto) -> _dt.datetime | None:
    s = str(texto or "").strip().replace("T", " ")
    for largo, fmt in ((19, "%Y-%m-%d %H:%M:%S"), (16, "%Y-%m-%d %H:%M"), (10, "%Y-%m-%d")):
        try:
            return _dt.datetime.strptime(s[:largo], fmt)
        except ValueError:
            continue
    return None


def _es_sqlite(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(16) == b"SQLite format 3\x00"
    except OSError:
        return False


def _mirar_sqlite(path: str) -> tuple[set, dict] | None:
    """Tablas y meta de un SQLite, sin escribirlo. None si no se puede abrir."""
    from pathlib import Path

    try:
        conn = sqlite3.connect(Path(path).as_uri() + "?mode=ro", uri=True, timeout=3)
    except sqlite3.Error:
        return None
    try:
        tablas = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        meta = {}
        if "espejo_meta" in tablas:
            meta = {str(k): v for k, v in conn.execute("SELECT clave, valor FROM espejo_meta")}
        return tablas, meta
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def _nodo_json(carpeta: str) -> dict:
    try:
        with open(os.path.join(carpeta, "nodo.json"), encoding="utf-8") as f:
            return json.load(f) or {}
    except (OSError, ValueError):
        return {}


def _sql_valido(path: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            cabeza = f.read(4096)
    except OSError:
        return False
    return any(k in cabeza for k in ("MariaDB dump", "MySQL dump", "CREATE TABLE", "INSERT INTO"))


def _zip_valido(path: str) -> bool:
    if not os.path.basename(path).lower().startswith(PREFIJOS_ZIP):
        return False
    try:
        with zipfile.ZipFile(path) as z:
            return any(n.replace("\\", "/").startswith("punpro_db/") for n in z.namelist()[:5000])
    except (OSError, zipfile.BadZipFile):
        return False


def analizar(path: str) -> Fuente | None:
    """Una copia usable, o None si el archivo no es de la tienda."""
    nombre = os.path.basename(path).lower()
    if ".bad_" in nombre or nombre.endswith((".tmp", ".nuevo")):
        return None
    try:
        tam = os.path.getsize(path)
    except OSError:
        return None
    if nombre.endswith(".sql"):
        if tam < MIN_SQL or not _sql_valido(path):
            return None
        parcial = "_ventas" in nombre
        return Fuente(path, "sql", _fecha_archivo(path), not parcial, detalle="solo ventas y caja" if parcial else "")
    if nombre.endswith(".zip"):
        if tam < MIN_ZIP or not _zip_valido(path):
            return None
        return Fuente(path, "zip", _fecha_archivo(path), True)
    if not nombre.endswith(".db") or not _es_sqlite(path):
        return None
    visto = _mirar_sqlite(path)
    if not visto:
        return None
    tablas, meta = visto
    if "ventas" not in tablas:
        return None
    propias = [t for t in tablas if t != "espejo_meta" and not t.startswith("sqlite_")]
    if "espejo_meta" in tablas or nombre == "nodo_negocio.db":
        nodo = _nodo_json(os.path.dirname(path))
        fecha = (
            _fecha_texto(meta.get("ultima_copia"))
            or _fecha_texto(nodo.get("last_sync"))
            or _dt.datetime.fromtimestamp(os.path.getmtime(path))
        )
        return Fuente(
            path,
            "copia",
            fecha,
            str(meta.get("completa", "")) == "1",
            tablas=int(meta.get("tablas") or 0) or len(propias),
            servidor=str(meta.get("servidor") or ""),
            detalle="pendrive" if nombre == "nodo_negocio.db" else "copia de una PC",
        )
    return Fuente(path, "sqlite", _fecha_archivo(path), True, tablas=len(propias))


def _archivos(raiz: str):
    base = raiz.rstrip("\\/").count(os.sep)
    vistos = 0
    for carpeta, dirs, archivos in os.walk(raiz):
        nivel = carpeta.rstrip("\\/").count(os.sep) - base
        dirs[:] = [d for d in dirs if d.lower() not in SALTEAR and nivel < PROFUNDIDAD]
        for a in archivos:
            if a.lower().endswith((".sql", ".zip", ".db")):
                vistos += 1
                if vistos > MAX_ARCHIVOS:
                    return
                yield os.path.join(carpeta, a)


def buscar(*rutas: str) -> list[Fuente]:
    """Copias usables en esas carpetas o archivos, de la más nueva a la más vieja."""
    encontradas: dict[str, Fuente] = {}
    for ruta in rutas:
        if not ruta or not os.path.exists(ruta):
            continue
        candidatos = [ruta] if os.path.isfile(ruta) else _archivos(ruta)
        for path in candidatos:
            clave = os.path.normcase(os.path.realpath(path))
            if clave in encontradas:
                continue
            fuente = analizar(path)
            if fuente:
                encontradas[clave] = fuente
    # La maestra guarda cada respaldo en dos carpetas: mismo nombre y tamaño = la misma copia
    unicas: dict[tuple, Fuente] = {}
    for f in encontradas.values():
        try:
            gemelo = (f.nombre.lower(), os.path.getsize(f.ruta))
        except OSError:
            continue
        unicas.setdefault(gemelo, f)
    return sorted(unicas.values(), key=lambda f: (f.fecha, f.completa), reverse=True)


def lugares_de_esta_pc() -> list[str]:
    """Donde esta PC guarda copias: respaldos del admin, copia local del jefe y el pendrive configurado."""
    lugares = []
    try:
        from src.base_de_datos.autoblindaje_db import AutoBlindajeDB

        lugares.extend(AutoBlindajeDB.get_backup_directories())
    except Exception:
        pass
    try:
        from src.jefe.nodo_portable.espejo import copia

        lugares.append(copia.carpeta())
    except Exception:
        pass
    try:
        from src.config import config

        nodo = str(config.get("jefe_nodo_path", "") or "").strip()
        if nodo:
            lugares.append(nodo)
    except Exception:
        pass
    return lugares
