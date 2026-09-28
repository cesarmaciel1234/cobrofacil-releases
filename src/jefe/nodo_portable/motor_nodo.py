"""
Nodo Jefe portable — multi-dispositivo sin nube.

Carpeta (USB / OneDrive):
  CobroFacil_Nodo/
    nodo.json
    contabilidad_jefe.db
    nodo_negocio.db   copia de espejo/ (la copia de la tienda que esta PC refresca sola)

1ª vez: copiar_nodo_completo (0–100%)
Después: sincronizar_faltantes (refresca la copia local y la vuelca al pendrive)
Si cae el negocio: promover_nodo()
Clientes cargados afuera: los chupa la tienda sola (src/clientes_fiado/oficina/huella).
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import sqlite3
import time
from datetime import datetime
from typing import Callable

NODO_DIR_NAME = "CobroFacil_Nodo"
NODO_JSON = "nodo.json"
NODO_NEGOCIO = "nodo_negocio.db"
CONTABILIDAD = "contabilidad_jefe.db"

# Tablas espejo del negocio (orden: padres antes que hijos de detalle)
TABLAS_NEGOCIO = (
    "productos",
    "clientes",
    "ventas",
    "detalles_ventas",
    "movimientos_caja",
    "clientes_auditoria",
    "cuenta_corriente",
    "mp_pagos",
)

ProgressCb = Callable[[int, str], None]


def _cfg():
    from src.config import config

    return config


def get_nodo_path() -> str:
    try:
        p = str(_cfg().get("jefe_nodo_path", "") or "").strip()
        return p
    except Exception:
        return ""


def set_nodo_path(path: str) -> None:
    try:
        _cfg().set("jefe_nodo_path", path)
        _cfg().save()
    except Exception:
        pass


def _nodo_json_path(root: str) -> str:
    return os.path.join(root, NODO_JSON)


def _negocio_db_path(root: str) -> str:
    return os.path.join(root, NODO_NEGOCIO)


def _conta_path_in_nodo(root: str) -> str:
    return os.path.join(root, CONTABILIDAD)


def estado_nodo(path: str | None = None) -> str:
    """'none' | 'ready'."""
    root = (path or get_nodo_path() or "").strip()
    if not root or not os.path.isdir(root):
        return "none"
    if not os.path.isfile(_nodo_json_path(root)):
        return "none"
    if not os.path.isfile(_negocio_db_path(root)):
        return "none"
    return "ready"


def _emit(cb: ProgressCb | None, pct: int, msg: str) -> None:
    if cb:
        try:
            cb(max(0, min(100, int(pct))), msg)
        except Exception:
            pass



def _sync_catalogos_dir(progress_cb, root_nodo: str, upload: bool = True):
    try:
        from src.carteleria.assets_paths import catalogos_dir
        import shutil
        local_cat = catalogos_dir()
        nodo_cat = os.path.join(root_nodo, "Catalogos")

        src, dst = (local_cat, nodo_cat) if upload else (nodo_cat, local_cat)
        if not os.path.isdir(src):
            return

        os.makedirs(dst, exist_ok=True)
        _emit(progress_cb, 95, "Sincronizando imágenes (PNGs)...")
        for root_dir, _, files in os.walk(src):
            rel = os.path.relpath(root_dir, src)
            target_dir = dst if rel in (".", "") else os.path.join(dst, rel)
            os.makedirs(target_dir, exist_ok=True)
            for file in files:
                if not file.lower().endswith((".png", ".jpg", ".jpeg", ".svg", ".webp")): continue
                sf = os.path.join(root_dir, file)
                df = os.path.join(target_dir, file)
                if not os.path.exists(df) or os.path.getmtime(sf) > os.path.getmtime(df):
                    try: shutil.copy2(sf, df)
                    except Exception: pass
    except Exception:
        pass

def _load_meta(root: str) -> dict:
    try:
        with open(_nodo_json_path(root), encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_meta(root: str, meta: dict) -> None:
    os.makedirs(root, exist_ok=True)
    with open(_nodo_json_path(root), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False, default=str)


def _origen_host() -> str:
    try:
        return socket.gethostname() or ""
    except Exception:
        return ""


def _contabilidad_origen() -> str:
    from src.utils.paths import get_base_path

    try:
        p = str(_cfg().get("jefe_db_path", "") or "").strip()
        if p and os.path.isfile(p):
            return p
    except Exception:
        pass
    return os.path.join(get_base_path(), "data", CONTABILIDAD)


def _ensure_negocio_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY,
            nombre TEXT,
            precio REAL,
            stock REAL DEFAULT 0,
            categoria TEXT DEFAULT 'GENERAL',
            unidad TEXT DEFAULT 'UN',
            costo REAL DEFAULT 0,
            cant_mayoreo REAL DEFAULT 0,
            precio_mayoreo REAL DEFAULT 0,
            stock_minimo REAL DEFAULT 0,
            stock_maximo REAL DEFAULT 0,
            codigo TEXT,
            departamento TEXT,
            es_pesable INTEGER DEFAULT 0,
            cant_oferta REAL DEFAULT 0,
            precio_oferta REAL DEFAULT 0,
            tipo_unidad_oferta TEXT DEFAULT 'Unidades'
        );
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY,
            nombre TEXT,
            telefono TEXT,
            email TEXT,
            dni TEXT,
            direccion TEXT,
            deuda_actual REAL DEFAULT 0,
            limite_credito REAL DEFAULT 0,
            tipo_cliente TEXT DEFAULT 'regular'
        );
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY,
            fecha TEXT,
            total REAL,
            pago_con REAL,
            cambio REAL,
            pago_efectivo REAL DEFAULT 0,
            pago_otro REAL DEFAULT 0,
            usuario TEXT,
            estado TEXT DEFAULT 'COMPLETADA',
            metodo_pago TEXT DEFAULT 'Efectivo',
            caja_id INTEGER DEFAULT 1,
            descuento REAL DEFAULT 0,
            recargo REAL DEFAULT 0,
            cliente_nombre TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS detalles_ventas (
            id INTEGER PRIMARY KEY,
            id_venta INTEGER,
            id_producto TEXT,
            nombre_producto TEXT,
            cantidad REAL,
            precio_unitario REAL,
            subtotal REAL
        );
        CREATE TABLE IF NOT EXISTS movimientos_caja (
            id INTEGER PRIMARY KEY,
            fecha TEXT,
            tipo TEXT,
            monto REAL,
            descripcion TEXT,
            usuario TEXT,
            caja_id INTEGER DEFAULT 1
        );
        """
    )
    from src.clientes_fiado.oficina.huella.tabla import COLUMNAS_CLIENTE, DDL_EVENTOS

    cur.execute(DDL_EVENTOS)
    tiene = {r[1] for r in cur.execute("PRAGMA table_info(clientes)").fetchall()}
    for col, tipo in COLUMNAS_CLIENTE:
        if col not in tiene:
            cur.execute(f"ALTER TABLE clientes ADD COLUMN {col} {tipo}")
    conn.commit()


def _hay_tienda() -> bool:
    from src.clientes_fiado.oficina.huella.tabla import es_tienda

    return es_tienda()


def _chupar_antes(neg_path: str) -> dict:
    """Antes de pisar el pendrive, la tienda toma los eventos de clientes que trajo. Sin tienda, nada."""
    if not _hay_tienda():
        return {}
    try:
        from src.clientes_fiado.oficina.huella.absorber import aplicar, leer_eventos

        return aplicar(leer_eventos(neg_path), "NODO")
    except Exception:
        return {}


def _devolver_eventos(neg_path: str, eventos: list[dict]) -> None:
    """Los eventos hechos sin red que traía el pendrive siguen viajando en la copia nueva."""
    if not eventos:
        return
    from src.clientes_fiado.oficina.huella.tabla import COLUMNAS_EVENTO, DDL_EVENTOS

    conn = sqlite3.connect(neg_path, timeout=10)
    try:
        conn.execute(DDL_EVENTOS)
        conn.executemany(
            f"INSERT OR IGNORE INTO clientes_auditoria ({', '.join(COLUMNAS_EVENTO)}) "
            f"VALUES ({', '.join('?' * len(COLUMNAS_EVENTO))})",
            [tuple(ev.get(c) for c in COLUMNAS_EVENTO) for ev in eventos],
        )
        conn.commit()
    finally:
        conn.close()


def _copia_al_dia(progress_cb: ProgressCb | None) -> dict:
    """Con maestra, refresca la copia de esta PC. Sin maestra (o tienda con error) va la última buena."""
    from src.jefe.nodo_portable import espejo

    _emit(progress_cb, 15, "Actualizando la copia de la tienda en esta PC…")
    res = espejo.refrescar()
    for _ in range(180):
        if res.get("estado") != "ocupado":
            break
        time.sleep(1)
        res = espejo.refrescar()
    if not espejo.existe():
        raise RuntimeError(
            "Esta PC todavía no tiene copia de la tienda.\n\n"
            "Conectate una vez a la maestra (Servidor LAN) y volvé a intentar."
        )
    return res


def _llevar_al_pendrive(root: str, progress_cb: ProgressCb | None) -> dict:
    from src.jefe.nodo_portable import espejo

    neg_path = _negocio_db_path(root)
    tomados, sueltos = {}, []
    if os.path.isfile(neg_path):
        _emit(progress_cb, 45, "Tomando clientes cargados afuera…")
        tomados = _chupar_antes(neg_path)
        try:
            from src.clientes_fiado.oficina.huella.absorber import leer_eventos

            sueltos = leer_eventos(neg_path)
        except Exception:
            sueltos = []
    _emit(progress_cb, 60, "Copiando al pendrive…")
    espejo.volcar_a(neg_path)
    conn = sqlite3.connect(neg_path, timeout=10)
    try:
        _ensure_negocio_schema(conn)
    finally:
        conn.close()
    _devolver_eventos(neg_path, sueltos)
    try:
        from src.clientes_fiado.oficina.huella.absorber import llevar_al_nodo

        llevar_al_nodo(neg_path)
    except Exception:
        pass
    return tomados


def _copiar_contabilidad(root: str, progress_cb: ProgressCb | None, siempre: bool) -> str:
    src_conta = _contabilidad_origen()
    dst_conta = _conta_path_in_nodo(root)
    try:
        if os.path.isfile(src_conta):
            if siempre or not os.path.isfile(dst_conta) or os.path.getmtime(src_conta) >= os.path.getmtime(dst_conta):
                _emit(progress_cb, 8, "Copiando contabilidad del jefe…")
                shutil.copy2(src_conta, dst_conta)
        elif not os.path.isfile(dst_conta):
            sqlite3.connect(dst_conta).close()
    except Exception:
        pass
    return dst_conta


def _resumen(res: dict, tomados: dict) -> dict:
    from src.jefe.nodo_portable import espejo

    m = espejo.estado()
    stats = {
        "copia_de": m.get("ultima_copia", ""),
        "clientes_tomados": int((tomados or {}).get("aplicado", 0)),
    }
    if res.get("estado") == "sin_tienda":
        stats["aviso"] = "Sin maestra: se llevó la última copia de esta PC."
    elif res.get("estado") == "error":
        stats["aviso"] = f"La tienda dio error al leer; se llevó la última copia buena. ({res.get('detalle', '')[:160]})"
    return stats


def _ensure_nodo_root(dest_folder: str) -> str:
    """Si el usuario elige una carpeta, usa/crea CobroFacil_Nodo dentro."""
    dest_folder = os.path.abspath(dest_folder)
    if os.path.basename(dest_folder).lower() == NODO_DIR_NAME.lower():
        root = dest_folder
    elif os.path.isfile(os.path.join(dest_folder, NODO_JSON)):
        root = dest_folder
    else:
        root = os.path.join(dest_folder, NODO_DIR_NAME)
    os.makedirs(root, exist_ok=True)
    return root


def copiar_nodo_completo(dest_folder: str, progress_cb: ProgressCb | None = None) -> str:
    """Primera copia (o Reemplazar): contabilidad + copia de la tienda de esta PC. Devuelve la ruta del nodo."""
    root = _ensure_nodo_root(dest_folder)
    _emit(progress_cb, 2, "Preparando carpeta del nodo…")
    dst_conta = _copiar_contabilidad(root, progress_cb, siempre=True)
    res = _copia_al_dia(progress_cb)
    tomados = _llevar_al_pendrive(root, progress_cb)
    _sync_catalogos_dir(progress_cb, root, upload=True)

    ahora = datetime.now().isoformat(timespec="seconds")
    meta = {
        "version": 2,
        "created_at": ahora,
        "last_full": ahora,
        "last_sync": ahora,
        "last_sync_stats": _resumen(res, tomados),
        "source_host": _origen_host(),
        "path": root,
    }
    _save_meta(root, meta)
    set_nodo_path(root)
    try:
        _cfg().set("jefe_db_path", dst_conta)
        _cfg().save()
    except Exception:
        pass

    _emit(progress_cb, 100, "Nodo listo al 100%")
    return root


def sincronizar_faltantes(progress_cb: ProgressCb | None = None, path: str | None = None) -> dict:
    """
    Pendrive = copia de la tienda de esta PC, para auditar. Con maestra la refresca antes;
    sin maestra lleva la última. La tienda toma antes los eventos de clientes que traía el pendrive.
    """
    root = (path or get_nodo_path() or "").strip()
    if estado_nodo(root) != "ready":
        raise RuntimeError("No hay nodo configurado. Primero copiá el nodo completo.")

    _copiar_contabilidad(root, progress_cb, siempre=False)
    res = _copia_al_dia(progress_cb)
    tomados = _llevar_al_pendrive(root, progress_cb)
    _sync_catalogos_dir(progress_cb, root, upload=True)
    stats = _resumen(res, tomados)

    meta = _load_meta(root)
    meta["last_sync"] = datetime.now().isoformat(timespec="seconds")
    meta["last_sync_stats"] = stats
    meta["source_host"] = _origen_host()
    _save_meta(root, meta)
    _emit(progress_cb, 100, "Sincronización completa")
    return stats


def promover_nodo(progress_cb=None, path: str | None = None) -> str:
    """
    Si cae la PC del negocio: usa el nodo en esta notebook.
    - Apunta contabilidad al nodo
    - Importa faltantes de nodo_negocio.db a la DB local conectada
    """
    root = (path or get_nodo_path() or "").strip()
    if estado_nodo(root) != "ready":
        raise RuntimeError("Nodo no válido para promover.")

    conta = _conta_path_in_nodo(root)
    if os.path.isfile(conta):
        try:
            _cfg().set("jefe_db_path", conta)
            set_nodo_path(root)
            _cfg().save()
        except Exception:
            pass

    from src.base_de_datos.database import db_manager

    src = sqlite3.connect(_negocio_db_path(root))
    src.row_factory = sqlite3.Row
    imported = 0
    _emit(progress_cb, 5, "Conectando al Nodo...")
    try:
        total = len(TABLAS_NEGOCIO)
        for i, table in enumerate(TABLAS_NEGOCIO):
            base_pct = 10 + int((i / max(total, 1)) * 80)
            next_pct = 10 + int(((i + 1) / max(total, 1)) * 80)

            _emit(progress_cb, base_pct, f"Promoviendo tabla: {table}...")
            try:
                cur = src.cursor()
                cur.execute(f"SELECT * FROM {table}")
                rows = [dict(r) for r in cur.fetchall()]
            except Exception:
                continue

            total_rows = len(rows)
            for row_idx, row in enumerate(rows):
                # Emitir progreso interno cada 100 filas para que la barra se mueva fluidamente
                if row_idx % 100 == 0 and total_rows > 0:
                    current_pct = base_pct + int((row_idx / total_rows) * (next_pct - base_pct))
                    _emit(progress_cb, current_pct, f"Promoviendo tabla: {table} ({row_idx}/{total_rows})...")

                rid = row.get("id")
                if rid is None:
                    continue
                try:
                    existing = db_manager.execute_query(
                        f"SELECT id FROM {table} WHERE id = ? LIMIT 1", (rid,)
                    )
                except Exception:
                    if table == "detalles_ventas":
                        try:
                            existing = db_manager.execute_query(
                                "SELECT id FROM detalle_ventas WHERE id = ? LIMIT 1", (rid,)
                            )
                        except Exception:
                            existing = None
                    else:
                        existing = None
                if existing:
                    continue
                # Insert best-effort via raw connection
                try:
                    conn = db_manager.get_connection()
                    c = conn.cursor()
                    keys = [k for k in row.keys() if row.get(k) is not None or k == "id"]
                    if not keys:
                        conn.close()
                        continue
                    cols = ",".join(keys)
                    ph = ",".join(["?"] * len(keys))
                    c.execute(
                        f"INSERT INTO {table} ({cols}) VALUES ({ph})",
                        tuple(row.get(k) for k in keys),
                    )
                    conn.commit()
                    conn.close()
                    imported += 1
                except Exception:
                    try:
                        conn.close()
                    except Exception:
                        pass
    finally:
        src.close()

    meta = _load_meta(root)
    meta["promoted_at"] = datetime.now().isoformat(timespec="seconds")
    _sync_catalogos_dir(progress_cb, root, upload=False)
    meta["promoted_imported"] = imported
    _save_meta(root, meta)
    _emit(progress_cb, 100, "¡Restauración exitosa!")
    return root
