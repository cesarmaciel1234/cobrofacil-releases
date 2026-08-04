"""
Nodo Jefe portable — multi-dispositivo sin nube.

Carpeta (USB / OneDrive):
  CobroFacil_Nodo/
    nodo.json
    contabilidad_jefe.db
    nodo_negocio.db   (ventas, detalles, productos, clientes, movimientos_caja)

1ª vez: copiar_nodo_completo (0–100%)
Después: sincronizar_faltantes (solo ids nuevos)
Si cae el negocio: promover_nodo()
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import sqlite3
from datetime import datetime
from typing import Any, Callable

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
    conn.commit()


def _row_to_dict(row: Any) -> dict:
    if isinstance(row, dict):
        return dict(row)
    try:
        return dict(row)
    except Exception:
        return {}


def _fetch_table(table: str) -> list[dict]:
    from src.base_de_datos.database import db_manager

    try:
        rows = db_manager.execute_query(f"SELECT * FROM {table}")
        if not rows:
            return []
        return [_row_to_dict(r) for r in rows]
    except Exception:
        # detalles_ventas vs detalle_ventas
        if table == "detalles_ventas":
            try:
                rows = db_manager.execute_query("SELECT * FROM detalle_ventas")
                return [_row_to_dict(r) for r in (rows or [])]
            except Exception:
                return []
        return []


def _table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    return [r[1] for r in cur.fetchall()]


def _upsert_rows(conn: sqlite3.Connection, table: str, rows: list[dict], only_missing: bool = False) -> int:
    if not rows:
        return 0
    cols = _table_columns(conn, table)
    if not cols:
        return 0
    cur = conn.cursor()
    written = 0
    for row in rows:
        data = {k: row.get(k) for k in cols if k in row}
        if not data:
            continue
        rid = data.get("id")
        if only_missing and rid is not None:
            cur.execute(f"SELECT 1 FROM {table} WHERE id = ? LIMIT 1", (rid,))
            if cur.fetchone():
                continue
        keys = list(data.keys())
        placeholders = ",".join("?" * len(keys))
        col_sql = ",".join(keys)
        if only_missing:
            sql = f"INSERT OR IGNORE INTO {table} ({col_sql}) VALUES ({placeholders})"
        else:
            sql = f"INSERT OR REPLACE INTO {table} ({col_sql}) VALUES ({placeholders})"
        try:
            cur.execute(sql, tuple(data[k] for k in keys))
            written += 1
        except Exception:
            pass
    conn.commit()
    return written


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
    """
    Copia completa 0–100%. Devuelve ruta del nodo.
    Incluye contabilidad + espejo negocio desde la DB conectada (maestra vía esclava).
    """
    root = _ensure_nodo_root(dest_folder)
    _emit(progress_cb, 2, "Preparando carpeta del nodo…")

    # 1) Contabilidad
    _emit(progress_cb, 8, "Copiando contabilidad del jefe…")
    src_conta = _contabilidad_origen()
    dst_conta = _conta_path_in_nodo(root)
    if os.path.isfile(src_conta):
        shutil.copy2(src_conta, dst_conta)
    else:
        # Crear vacío usable
        os.makedirs(os.path.dirname(dst_conta) or root, exist_ok=True)
        sqlite3.connect(dst_conta).close()

    # 2) Espejo negocio
    _emit(progress_cb, 15, "Creando espejo del negocio…")
    neg_path = _negocio_db_path(root)
    if os.path.isfile(neg_path):
        try:
            os.remove(neg_path)
        except OSError:
            pass
    conn = sqlite3.connect(neg_path)
    try:
        _ensure_negocio_schema(conn)
        n_tables = len(TABLAS_NEGOCIO)
        for i, table in enumerate(TABLAS_NEGOCIO):
            pct = 20 + int((i / max(n_tables, 1)) * 70)
            _emit(progress_cb, pct, f"Exportando {table}…")
            rows = _fetch_table(table)
            _upsert_rows(conn, table, rows, only_missing=False)
        # Diario AppData como refuerzo de ventas
        _emit(progress_cb, 92, "Integrando diario externo…")
        _merge_diario_into_nodo(conn)
    finally:
        conn.close()

    meta = {
        "version": 1,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "last_full": datetime.now().isoformat(timespec="seconds"),
        "last_sync": datetime.now().isoformat(timespec="seconds"),
        "source_host": _origen_host(),
        "path": root,
    }
    try:
        from src.base_de_datos.database import db_manager

        meta["source_engine"] = getattr(db_manager, "db_engine_type", "")
        meta["source_is_master"] = bool(getattr(db_manager, "is_master", False))
    except Exception:
        pass

    _save_meta(root, meta)
    set_nodo_path(root)
    try:
        _cfg().set("jefe_db_path", dst_conta)
        _cfg().save()
    except Exception:
        pass

    _emit(progress_cb, 100, "Nodo listo al 100%")
    return root


def _merge_diario_into_nodo(conn: sqlite3.Connection) -> int:
    """Suma ventas del diario AppData que falten en el nodo."""
    try:
        from src.base_de_datos.diario_ventas_externo import _iter_payloads

        payloads = _iter_payloads(max_archivos=2000)
    except Exception:
        return 0
    n = 0
    for p in payloads:
        vid = p.get("id")
        if vid is None:
            continue
        venta = {
            "id": vid,
            "fecha": p.get("fecha"),
            "total": p.get("total"),
            "pago_con": p.get("pago_con"),
            "cambio": p.get("cambio"),
            "pago_efectivo": p.get("pago_efectivo"),
            "pago_otro": p.get("pago_otro"),
            "usuario": p.get("usuario"),
            "estado": p.get("estado") or "COMPLETADA",
            "metodo_pago": p.get("metodo_pago"),
            "caja_id": p.get("caja_id") or 1,
            "descuento": p.get("descuento") or 0,
            "recargo": p.get("recargo") or 0,
            "cliente_nombre": p.get("cliente_nombre") or "",
        }
        n += _upsert_rows(conn, "ventas", [venta], only_missing=True)
        detalles = []
        for it in p.get("items") or []:
            detalles.append(
                {
                    "id_venta": vid,
                    "id_producto": it.get("id"),
                    "nombre_producto": it.get("nombre") or "",
                    "cantidad": it.get("cant") or 0,
                    "precio_unitario": it.get("precio") or 0,
                    "subtotal": it.get("subtotal") or 0,
                }
            )
        if detalles:
            # detalles sin id propio: insert ignore por no tener PK estable → usar REPLACE suelto
            cur = conn.cursor()
            for d in detalles:
                try:
                    cur.execute(
                        "SELECT 1 FROM detalles_ventas WHERE id_venta=? AND id_producto=? AND cantidad=? LIMIT 1",
                        (d["id_venta"], d["id_producto"], d["cantidad"]),
                    )
                    if cur.fetchone():
                        continue
                    cur.execute(
                        """
                        INSERT INTO detalles_ventas
                        (id_venta, id_producto, nombre_producto, cantidad, precio_unitario, subtotal)
                        VALUES (?,?,?,?,?,?)
                        """,
                        (
                            d["id_venta"],
                            d["id_producto"],
                            d["nombre_producto"],
                            d["cantidad"],
                            d["precio_unitario"],
                            d["subtotal"],
                        ),
                    )
                    n += 1
                except Exception:
                    pass
            conn.commit()
    return n


def sincronizar_faltantes(progress_cb: ProgressCb | None = None, path: str | None = None) -> dict:
    """Solo inserta filas cuyo id no está en el nodo. Devuelve contadores."""
    root = (path or get_nodo_path() or "").strip()
    if estado_nodo(root) != "ready":
        raise RuntimeError("No hay nodo configurado. Primero copiá el nodo completo.")

    _emit(progress_cb, 5, "Abriendo nodo…")
    # Contabilidad: si la local es más nueva, copiar; si no, dejar
    src_conta = _contabilidad_origen()
    dst_conta = _conta_path_in_nodo(root)
    if os.path.isfile(src_conta):
        try:
            if (not os.path.isfile(dst_conta)) or (
                os.path.getmtime(src_conta) >= os.path.getmtime(dst_conta)
            ):
                _emit(progress_cb, 12, "Actualizando contabilidad…")
                shutil.copy2(src_conta, dst_conta)
        except Exception:
            pass

    conn = sqlite3.connect(_negocio_db_path(root))
    stats = {t: 0 for t in TABLAS_NEGOCIO}
    try:
        _ensure_negocio_schema(conn)
        n_tables = len(TABLAS_NEGOCIO)
        for i, table in enumerate(TABLAS_NEGOCIO):
            pct = 15 + int((i / max(n_tables, 1)) * 70)
            _emit(progress_cb, pct, f"Sincronizando faltantes: {table}…")
            rows = _fetch_table(table)
            stats[table] = _upsert_rows(conn, table, rows, only_missing=True)
        _emit(progress_cb, 90, "Diario externo…")
        stats["diario"] = _merge_diario_into_nodo(conn)
    finally:
        conn.close()

    meta = _load_meta(root)
    meta["last_sync"] = datetime.now().isoformat(timespec="seconds")
    meta["last_sync_stats"] = stats
    meta["source_host"] = _origen_host()
    _save_meta(root, meta)
    _emit(progress_cb, 100, "Sincronización completa")
    return stats


def promover_nodo(path: str | None = None) -> str:
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
    try:
        for table in TABLAS_NEGOCIO:
            try:
                cur = src.cursor()
                cur.execute(f"SELECT * FROM {table}")
                rows = [dict(r) for r in cur.fetchall()]
            except Exception:
                continue
            for row in rows:
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
    meta["promoted_imported"] = imported
    _save_meta(root, meta)
    return root
