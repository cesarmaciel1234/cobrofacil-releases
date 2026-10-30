"""La planilla es de este motor. No es la tabla productos."""

import logging
from datetime import datetime

from src.base_de_datos.database import db_manager

logger = logging.getLogger("planilla_reposicion")

TABLA = "planilla_reposicion"
BORRADOR = "planilla_reposicion_borrador"
_lista = False


def _es_maria() -> bool:
    return getattr(db_manager, "db_engine_type", "") == "mariadb"


def _dict(row) -> dict:
    if isinstance(row, dict):
        crudo = row
    elif hasattr(row, "keys"):
        crudo = {k: row[k] for k in row.keys()}
    else:
        return {}
    return {str(k).lower(): v for k, v in crudo.items()}


def _crear(nombre: str) -> str:
    if _es_maria():
        return f"""
            CREATE TABLE IF NOT EXISTS {nombre} (
                producto_id VARCHAR(64) NOT NULL PRIMARY KEY,
                codigo VARCHAR(64) NOT NULL DEFAULT '',
                nombre VARCHAR(255) NOT NULL DEFAULT '',
                departamento VARCHAR(255) NOT NULL DEFAULT '',
                stock DOUBLE NOT NULL DEFAULT 0,
                stock_minimo DOUBLE NOT NULL DEFAULT 0,
                stock_maximo DOUBLE NOT NULL DEFAULT 0,
                costo DOUBLE NOT NULL DEFAULT 0,
                motivo VARCHAR(32) NOT NULL DEFAULT '',
                cantidad_sugerida DOUBLE NOT NULL DEFAULT 1,
                actualizado VARCHAR(32) NOT NULL DEFAULT ''
            )
        """
    return f"""
        CREATE TABLE IF NOT EXISTS {nombre} (
                producto_id TEXT PRIMARY KEY,
                codigo TEXT DEFAULT '',
                nombre TEXT DEFAULT '',
                departamento TEXT DEFAULT '',
                stock REAL DEFAULT 0,
                stock_minimo REAL DEFAULT 0,
                stock_maximo REAL DEFAULT 0,
                costo REAL DEFAULT 0,
                motivo TEXT DEFAULT '',
                cantidad_sugerida REAL DEFAULT 1,
                actualizado TEXT DEFAULT ''
            )
        """


def _ancho_id() -> None:
    """El id puede ser un código de barras o formula:Pollo. BIGINT no entra el texto."""
    if not _es_maria():
        return
    for nombre in (TABLA, BORRADOR):
        db_manager.execute_non_query(
            f"ALTER TABLE {nombre} MODIFY producto_id VARCHAR(64) NOT NULL"
        )


def asegurar():
    global _lista
    if _lista:
        return
    for nombre in (TABLA, BORRADOR):
        if not db_manager.execute_non_query(_crear(nombre)):
            raise RuntimeError(f"No se pudo preparar {nombre}")
    _ancho_id()
    _lista = True


def _params(filas: list[dict], ahora: str) -> list[tuple]:
    return [
        (
            str(r.get("id") if r.get("id") is not None else ""),
            r.get("codigo") or "",
            r.get("nombre") or "",
            r.get("departamento") or "",
            float(r.get("stock") or 0),
            float(r.get("stock_minimo") or 0),
            float(r.get("stock_maximo") or 0),
            float(r.get("costo") or 0),
            r.get("motivo") or "",
            float(r.get("cantidad_sugerida") or 0),
            ahora,
        )
        for r in filas
    ]


def reemplazar(filas: list[dict]) -> None:
    """Publica la lista en un lote. No toca productos."""
    asegurar()
    if not db_manager.execute_non_query(f"DELETE FROM {BORRADOR}"):
        raise RuntimeError("No se pudo vaciar el borrador")
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    params = _params(filas or [], ahora)
    if params:
        verbo = "REPLACE INTO" if _es_maria() else "INSERT OR REPLACE INTO"
        columnas = (
            "producto_id, codigo, nombre, departamento, stock, stock_minimo, "
            "stock_maximo, costo, motivo, cantidad_sugerida, actualizado"
        )
        marcas = ", ".join("?" for _ in range(11))
        sql = f"{verbo} {{tabla}} ({columnas}) VALUES ({marcas})"
        if not db_manager.execute_many(sql.format(tabla=BORRADOR), params):
            raise RuntimeError("No se pudo escribir el borrador")
        if not db_manager.execute_many(sql.format(tabla=TABLA), params):
            raise RuntimeError("No se pudo publicar la planilla")
    if filas:
        ids = tuple(str(r.get("id") if r.get("id") is not None else "") for r in filas)
        marcas = ", ".join("?" for _ in ids)
        ok = db_manager.execute_non_query(
            f"DELETE FROM {TABLA} WHERE producto_id NOT IN ({marcas})",
            ids,
        )
    else:
        ok = db_manager.execute_non_query(f"DELETE FROM {TABLA}")
    if not ok:
        raise RuntimeError("No se pudo publicar la planilla")


def leer() -> list[dict]:
    asegurar()
    filas = db_manager.execute_query(
        f"SELECT producto_id, codigo, nombre, departamento, stock, stock_minimo, "
        f"stock_maximo, costo, motivo, cantidad_sugerida FROM {TABLA} "
        f"ORDER BY departamento ASC, nombre ASC"
    ) or []
    salida = []
    for cruda in filas:
        r = _dict(cruda)
        if not r:
            continue
        salida.append({
            "id": r.get("producto_id"),
            "codigo": r.get("codigo") or "",
            "nombre": r.get("nombre") or "",
            "departamento": r.get("departamento") or "GENERAL",
            "stock": float(r.get("stock") or 0),
            "stock_minimo": float(r.get("stock_minimo") or 0),
            "stock_maximo": float(r.get("stock_maximo") or 0),
            "costo": float(r.get("costo") or 0),
            "motivo": r.get("motivo") or "",
            "cantidad_sugerida": float(r.get("cantidad_sugerida") or 0),
        })
    return salida
