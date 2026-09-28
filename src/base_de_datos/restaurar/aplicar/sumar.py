"""Suma una copia SQLite a la tienda: agrega lo que falta, no borra ni pisa lo que ya está."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from src.logger import logger

LOTE = 500
COL_VENTA = ("id_venta", "venta_id")
PRIMERO = (
    "productos",
    "clientes",
    "ventas",
    "detalles_ventas",
    "movimientos_caja",
    "clientes_auditoria",
    "cuenta_corriente",
    "mp_pagos",
)
NO_SUMAR = ("espejo_meta", "terminales_activos", "sqlite_sequence")


class _Tienda:
    """Lo mínimo que la suma necesita de la base destino, igual para MariaDB y SQLite."""

    def __init__(self, conn, motor: str):
        self.conn = conn
        self.maria = motor == "mariadb"
        self.ph = "%s" if self.maria else "?"
        self.ignorar = "INSERT IGNORE INTO" if self.maria else "INSERT OR IGNORE INTO"
        self.cur = conn.cursor()
        if self.maria:
            self.cur.execute("SET FOREIGN_KEY_CHECKS = 0")

    def q(self, nombre: str) -> str:
        return f"`{nombre}`" if self.maria else f'"{nombre}"'

    def _filas(self, sql: str, params=()) -> list:
        self.cur.execute(sql, params)
        return list(self.cur.fetchall() or [])

    def columnas(self, tabla: str) -> list[str]:
        if self.maria:
            return [
                r[0]
                for r in self._filas(
                    "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s ORDER BY ORDINAL_POSITION",
                    (tabla,),
                )
            ]
        return [r[1] for r in self._filas(f'PRAGMA table_info("{tabla}")')]

    def clave(self, tabla: str) -> list[str]:
        if self.maria:
            return [
                r[0]
                for r in self._filas(
                    "SELECT COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE "
                    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND CONSTRAINT_NAME = 'PRIMARY' "
                    "ORDER BY ORDINAL_POSITION",
                    (tabla,),
                )
            ]
        info = sorted((r[5], r[1]) for r in self._filas(f'PRAGMA table_info("{tabla}")') if r[5])
        return [c for _, c in info]

    def vacia(self, tabla: str) -> bool:
        return not self._filas(f"SELECT 1 FROM {self.q(tabla)} LIMIT 1")

    def mapa(self, tabla: str, clave: str, valor: str | None, claves: list) -> dict:
        """clave → valor (o True) de las filas de la tienda con esas claves."""
        out = {}
        sel = f"{self.q(clave)}, {self.q(valor)}" if valor else self.q(clave)
        for i in range(0, len(claves), LOTE):
            parte = claves[i : i + LOTE]
            marcas = ", ".join([self.ph] * len(parte))
            for r in self._filas(f"SELECT {sel} FROM {self.q(tabla)} WHERE {self.q(clave)} IN ({marcas})", tuple(parte)):
                out[r[0]] = r[1] if valor else True
        return out

    def insertar(self, tabla: str, cols: list[str], filas: list[dict], ignorar: bool = True) -> int:
        if not filas:
            return 0
        verbo = self.ignorar if ignorar else "INSERT INTO"
        sql = (
            f"{verbo} {self.q(tabla)} ({', '.join(self.q(c) for c in cols)}) "
            f"VALUES ({', '.join([self.ph] * len(cols))})"
        )
        total = 0
        for i in range(0, len(filas), LOTE):
            self.cur.executemany(sql, [tuple(f.get(c) for c in cols) for f in filas[i : i + LOTE]])
            total += max(self.cur.rowcount or 0, 0)
        return total

    def insertar_una(self, tabla: str, cols: list[str], fila: dict) -> int:
        self.cur.execute(
            f"INSERT INTO {self.q(tabla)} ({', '.join(self.q(c) for c in cols)}) "
            f"VALUES ({', '.join([self.ph] * len(cols))})",
            tuple(fila.get(c) for c in cols),
        )
        return int(self.cur.lastrowid or 0)


def _orden(tablas: list[str]) -> list[str]:
    primero = [t for t in PRIMERO if t in tablas]
    return primero + sorted(t for t in tablas if t not in primero)


def _sumar_ventas(tienda: _Tienda, cols: list[str], filas: list[dict], pk: list[str], renumeradas: dict) -> tuple[int, int]:
    """Mismo request_id = misma venta. Mismo número con otro request_id = otra venta: entra con número nuevo."""
    if pk != ["id"] or "id" not in cols:
        return _sumar_tabla(tienda, "ventas", cols, filas, pk, renumeradas)
    con_rid = "request_id" in cols
    ids = [f["id"] for f in filas if f.get("id") is not None]
    en_tienda = tienda.mapa("ventas", "id", "request_id" if con_rid else None, ids)
    rids = [f["request_id"] for f in filas if con_rid and f.get("request_id")]
    rids_tienda = set(tienda.mapa("ventas", "request_id", None, rids)) if rids else set()
    nuevas, otras, ya = [], [], 0
    for f in filas:
        rid = f.get("request_id") if con_rid else None
        if rid and rid in rids_tienda:
            ya += 1
        elif f.get("id") in en_tienda:
            suyo = en_tienda[f["id"]]
            if rid and suyo not in (True, None, "") and suyo != rid:
                otras.append(f)
            else:
                ya += 1
        else:
            nuevas.append(f)
    sumadas = tienda.insertar("ventas", cols, nuevas)
    ya += len(nuevas) - sumadas
    sin_id = [c for c in cols if c != "id"]
    for f in otras:
        renumeradas[f["id"]] = tienda.insertar_una("ventas", sin_id, f)
    return sumadas + len(otras), ya


def _sumar_tabla(tienda: _Tienda, tabla: str, cols: list[str], filas: list[dict], pk: list[str], renumeradas: dict) -> tuple[int, int]:
    if not pk:
        if not tienda.vacia(tabla):
            return 0, len(filas)
        return tienda.insertar(tabla, cols, filas, ignorar=False), 0
    col_v = next((c for c in COL_VENTA if c in cols), None)
    movidas = []
    if col_v and renumeradas:
        movidas = [f for f in filas if f.get(col_v) in renumeradas]
        filas = [f for f in filas if f.get(col_v) not in renumeradas]
    sumadas = tienda.insertar(tabla, cols, filas)
    if movidas:
        sin_id = [c for c in cols if c != "id"] if pk == ["id"] else cols
        for f in movidas:
            tienda.insertar(tabla, sin_id, [{**f, col_v: renumeradas[f[col_v]]}], ignorar=pk != ["id"])
    return sumadas + len(movidas), len(filas) - sumadas


def sumar(origen: str, destino, progreso=None) -> dict:
    """Todas las tablas de la copia que la tienda también tiene. Todo o nada: si una falla, no queda nada a medias."""
    src = sqlite3.connect(Path(origen).as_uri() + "?mode=ro", uri=True, timeout=10)
    src.row_factory = sqlite3.Row
    conn = destino.conectar()
    tienda = _Tienda(conn, destino.motor)
    res = {"tablas": {}, "sin_lugar": [], "renumeradas": 0}
    renumeradas: dict = {}
    try:
        tablas = [
            r[0]
            for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")
            if r[0] not in NO_SUMAR and not r[0].startswith("sqlite_")
        ]
        orden = _orden(tablas)
        for i, tabla in enumerate(orden):
            if progreso:
                progreso(int(100 * i / max(len(orden), 1)), f"Sumando {tabla}…")
            suyas = tienda.columnas(tabla)
            cols = [r[1] for r in src.execute(f'PRAGMA table_info("{tabla}")') if r[1] in suyas]
            if not cols:
                res["sin_lugar"].append(tabla)
                continue
            lista = ", ".join(f'"{c}"' for c in cols)
            filas = [dict(r) for r in src.execute(f'SELECT {lista} FROM "{tabla}"')]
            pk = tienda.clave(tabla)
            if tabla == "ventas":
                sumadas, ya = _sumar_ventas(tienda, cols, filas, pk, renumeradas)
            else:
                sumadas, ya = _sumar_tabla(tienda, tabla, cols, filas, pk, renumeradas)
            res["tablas"][tabla] = {"sumadas": sumadas, "ya_estaban": ya}
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            conn.close()
        finally:
            src.close()
    res["renumeradas"] = len(renumeradas)
    logger.info(
        f"Restaurar (suma) desde {origen}: "
        + ", ".join(f"{t} +{v['sumadas']}" for t, v in res["tablas"].items() if v["sumadas"])
        + (f"; {res['renumeradas']} ventas con número nuevo" if renumeradas else "")
    )
    return res
