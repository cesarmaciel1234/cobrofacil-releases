"""
La tienda chupa los eventos de clientes hechos sin red (en casa o en una notebook).

No copia fichas ni saldos: aplica eventos. Cada evento entra una sola vez porque su ID es
la clave de `clientes_auditoria`. Si dos PCs lo intentan a la vez, la segunda choca y no aplica.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from pathlib import Path

from src.clientes_fiado.oficina.huella import pc as huella_pc
from src.clientes_fiado.oficina.huella import tabla
from src.clientes_fiado.oficina.huella.eventos import CAMPOS_FICHA, _dic, _insert_sql, limpio, valores

_despertar = threading.Event()
_hilo: threading.Thread | None = None
_estado: dict = {}


def _db():
    from src.base_de_datos.database import db_manager

    return db_manager


def _logger():
    from src.logger import logger

    return logger


# ── Leer eventos de un archivo SQLite (nodo o punpro.db) ──────────────────────

def leer_eventos(path: str, solo_pc: str | None = None) -> list[dict]:
    """Eventos hechos sin red (`base = 'LOCAL'`), por fecha. [] si el archivo no tiene el libro."""
    if not path or not os.path.isfile(path):
        return []
    try:
        conn = sqlite3.connect(Path(path).as_uri() + "?mode=ro", uri=True, timeout=5)
    except Exception:
        return []
    try:
        conn.row_factory = sqlite3.Row
        sql = "SELECT * FROM clientes_auditoria WHERE base = 'LOCAL'"
        params: tuple = ()
        if solo_pc:
            sql += " AND pc = ?"
            params = (solo_pc,)
        return [dict(r) for r in conn.execute(sql + " ORDER BY fecha, evento", params).fetchall()]
    except Exception:
        return []
    finally:
        conn.close()


# ── Aplicar en la tienda ──────────────────────────────────────────────────────

def _ya_estan(db, ids: list[str]) -> set[str]:
    hay: set[str] = set()
    for i in range(0, len(ids), 200):
        lote = ids[i:i + 200]
        filas = db.execute_query(
            f"SELECT evento FROM clientes_auditoria WHERE evento IN ({', '.join('?' * len(lote))})",
            tuple(lote),
        ) or []
        hay |= {str(_dic(f, ("evento",)).get("evento")) for f in filas}
    return hay


def _uno(cur, sql, params=()):
    cur.execute(sql, params)
    return cur.fetchone()


def _resolver(cur, uid) -> int | None:
    if not uid:
        return None
    fila = _uno(cur, "SELECT id FROM clientes WHERE uid = ?", (uid,))
    if fila:
        return _dic(fila, ("id",)).get("id")
    fila = _uno(
        cur,
        "SELECT cliente_id FROM clientes_auditoria WHERE accion = 'FUSION' AND cliente_uid = ?",
        (uid,),
    )
    return _dic(fila, ("cliente_id",)).get("cliente_id") if fila else None


def _dni(texto) -> str:
    d = "".join(c for c in str(texto or "") if c.isdigit())
    return d if len(d) >= 7 else ""


def _gemelo(cur, ficha: dict) -> int | None:
    """El mismo cliente ya cargado en la tienda: mismo DNI, o sin DNI y mismo nombre."""
    dni = _dni(ficha.get("dni"))
    if dni:
        fila = _uno(cur, "SELECT id FROM clientes WHERE dni = ?", (dni,))
        return _dic(fila, ("id",)).get("id") if fila else None
    nombre = limpio(ficha.get("nombre")).strip()
    if not nombre:
        return None
    fila = _uno(cur, "SELECT id FROM clientes WHERE nombre = ? AND (dni IS NULL OR dni = '')", (nombre,))
    return _dic(fila, ("id",)).get("id") if fila else None


def _deuda(cur, cid) -> float:
    fila = _uno(cur, "SELECT deuda_actual FROM clientes WHERE id = ?", (cid,))
    try:
        return float(_dic(fila, ("deuda_actual",)).get("deuda_actual") or 0)
    except (TypeError, ValueError):
        return 0.0


def _es_duplicado(e: Exception) -> bool:
    """El evento ya estaba (clave repetida). Otro error no es 'repetido': se reintenta en la próxima vuelta."""
    args = getattr(e, "args", ()) or ()
    texto = str(e)
    return (bool(args) and args[0] == 1062) or "Duplicate entry" in texto or "UNIQUE constraint" in texto


def _firma(ev: dict) -> str:
    return f"cargado en {ev.get('pc')} por {ev.get('usuario')} el {ev.get('fecha')}"


def _movimiento(cur, ev: dict, cid: int, det: dict) -> None:
    monto = float(det.get("monto") or 0)
    if monto <= 0:
        return
    deuda = _deuda(cur, cid)
    if ev["accion"] == "CARGO":
        tipo, saldo = "CARGO", deuda + monto
    else:
        tipo, saldo = "ABONO", max(0.0, deuda - monto)
    cur.execute("UPDATE clientes SET deuda_actual = ? WHERE id = ?", (saldo, cid))
    desc = limpio(f"{det.get('descripcion') or tipo.title()} · {_firma(ev)}", 250)
    cur.execute(
        "INSERT INTO cuenta_corriente (cliente_id, tipo, monto, saldo_resultante, descripcion) VALUES (?, ?, ?, ?, ?)",
        (cid, tipo, monto, saldo, desc),
    )


def _ficha_vieja(cur, cid, fecha_evento) -> bool:
    """True si la tienda editó la ficha después del evento: gana la tienda."""
    fila = _uno(cur, "SELECT actualizado_en FROM clientes WHERE id = ?", (cid,))
    actual = str(_dic(fila, ("actualizado_en",)).get("actualizado_en") or "")
    return bool(actual) and actual > str(fecha_evento or "")


def _alta(cur, ev: dict, det: dict) -> tuple[int | None, str]:
    ficha = det.get("ficha") or {}
    uid = ev.get("cliente_uid")
    gemelo = _gemelo(cur, ficha)
    if gemelo:
        fusion = dict(ev, evento=f"FUS-{uid}"[:80], accion="FUSION", cliente_id=gemelo, base="TIENDA",
                      llego_en=huella_pc.ahora(), llego_via="MOTOR",
                      detalle=json.dumps({"uid_origen": uid, "motivo": "mismo DNI o nombre"}, ensure_ascii=True))
        cur.execute(_insert_sql(), valores(fusion))
        return gemelo, "FUSION"
    datos = {k: ficha.get(k) for k in CAMPOS_FICHA + ("limite_credito",) if k in ficha}
    datos["nombre"] = limpio(datos.get("nombre")) or "Sin nombre"
    datos.update(deuda_actual=0, uid=uid, origen_pc=ev.get("pc"), creado_por=ev.get("usuario"),
                 creado_en=ev.get("fecha"), actualizado_en=ev.get("fecha"))
    cols = list(datos.keys())
    cur.execute(
        f"INSERT INTO clientes ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
        tuple(datos[c] for c in cols),
    )
    return _resolver(cur, uid), ""


def aplicar_evento(ev: dict, via: str, db=None) -> str:
    """
    'aplicado' | 'repetido' | 'pendiente' (el cliente todavía no llegó) | 'error'.
    Todo en una transacción: el evento y su efecto entran juntos o no entra nada.
    """
    db = db or _db()
    conn = None
    try:
        conn = db.get_connection()
        cur = conn.cursor()
        fila = dict(ev, llego_en=huella_pc.ahora(), llego_via=via)
        try:
            cur.execute(_insert_sql(), valores(fila))
        except Exception as e:
            conn.rollback()
            if _es_duplicado(e):
                return "repetido"
            raise
        try:
            det = json.loads(ev.get("detalle") or "{}")
        except Exception:
            det = {}
        accion = str(ev.get("accion") or "").upper()
        cid = _resolver(cur, ev.get("cliente_uid"))
        nota = ""
        if accion == "ALTA":
            if not cid:
                cid, nota = _alta(cur, ev, det)
        elif not cid:
            conn.rollback()
            return "pendiente"
        elif accion in ("EDICION", "LIMITE"):
            if _ficha_vieja(cur, cid, ev.get("fecha")):
                nota = "TIENDA_MAS_NUEVA"
            else:
                permitidos = CAMPOS_FICHA + ("limite_credito",)
                cambios = {k: v for k, v in (det.get("despues") or {}).items() if k in permitidos}
                if "nombre" in cambios:
                    cambios["nombre"] = limpio(cambios["nombre"])
                if cambios:
                    cambios["actualizado_en"] = ev.get("fecha")
                    sets = ", ".join(f"{k} = ?" for k in cambios)
                    cur.execute(f"UPDATE clientes SET {sets} WHERE id = ?", tuple(cambios.values()) + (cid,))
        elif accion in ("CARGO", "ABONO"):
            _movimiento(cur, ev, cid, det)
        cur.execute(
            "UPDATE clientes_auditoria SET cliente_id = ?, llego_via = ? WHERE evento = ?",
            (cid, f"{via}:{nota}" if nota else via, ev["evento"]),
        )
        conn.commit()
        return "aplicado"
    except Exception as e:
        try:
            if conn:
                conn.rollback()
        except Exception:
            pass
        try:
            _logger().warning(f"[huella] evento {ev.get('evento')} no entró: {e}")
        except Exception:
            pass
        return "error"
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


def aplicar(eventos: list[dict], via: str, db=None) -> dict:
    db = db or _db()
    cuenta = {"aplicado": 0, "repetido": 0, "pendiente": 0, "error": 0}
    if not eventos or not tabla.asegurar(db):
        return cuenta
    ya = _ya_estan(db, [str(e.get("evento")) for e in eventos])
    for ev in eventos:
        if str(ev.get("evento")) in ya:
            cuenta["repetido"] += 1
            continue
        cuenta[aplicar_evento(ev, via, db)] += 1
    return cuenta


# ── Fuentes ───────────────────────────────────────────────────────────────────

def _punpro_local() -> str:
    try:
        from src.utils.paths import get_base_path

        return os.path.join(get_base_path(), "punpro.db")
    except Exception:
        return ""


def _nodo_db() -> str:
    try:
        from src.jefe.nodo_portable.motor_nodo import _negocio_db_path, estado_nodo, get_nodo_path

        root = get_nodo_path()
        return _negocio_db_path(root) if root and estado_nodo(root) == "ready" else ""
    except Exception:
        return ""


def llevar_al_nodo(nodo_db: str, db=None) -> int:
    """Sin red: copia al pendrive los eventos hechos en esta PC. El nodo los lleva a la tienda."""
    db = db or _db()
    if not nodo_db or not os.path.isfile(nodo_db) or tabla.es_tienda(db):
        return 0
    filas = db.execute_query("SELECT * FROM clientes_auditoria WHERE base = 'LOCAL'") or []
    if not filas:
        return 0
    conn = sqlite3.connect(nodo_db, timeout=10)
    try:
        conn.execute(tabla.DDL_EVENTOS)
        cols = tabla.COLUMNAS_EVENTO
        antes = conn.total_changes
        conn.executemany(
            f"INSERT OR IGNORE INTO clientes_auditoria ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
            [tuple(_dic(f).get(c) for c in cols) for f in filas],
        )
        conn.commit()
        return conn.total_changes - antes
    finally:
        conn.close()


def turno() -> dict:
    """Con red: la tienda chupa de esta PC y del nodo. Sin red: esta PC deja sus eventos en el nodo."""
    db = _db()
    res: dict = {"hora": huella_pc.ahora(), "pc": huella_pc.pc_id()}
    if tabla.es_tienda(db):
        try:
            from src.jefe.nodo_portable.espejo.copia import tienda_rota

            rota = tienda_rota()
        except Exception:
            rota = ""
        if rota:
            res["error"] = f"tienda con tablas dañadas: {rota}"
            _estado.clear()
            _estado.update(res)
            return res
        if not tabla.asegurar(db):
            res["error"] = "sin columnas de huella en la tienda"
            return res
        tabla.completar_uids(db)
        res["local"] = aplicar(leer_eventos(_punpro_local(), solo_pc=huella_pc.pc_id()), "LOCAL", db)
        nodo = _nodo_db()
        if nodo:
            res["nodo"] = aplicar(leer_eventos(nodo), "NODO", db)
    else:
        tabla.asegurar(db)
        nodo = _nodo_db()
        if nodo:
            res["al_nodo"] = llevar_al_nodo(nodo, db)
    _estado.clear()
    _estado.update(res)
    return res


def estado() -> dict:
    return dict(_estado)


def despertar() -> None:
    _despertar.set()


def arrancar(pausa: int = 120) -> None:
    """Un hilo por proceso. Primera vuelta a los 30 s; después cada `pausa` segundos o al despertar."""
    global _hilo
    if _hilo and _hilo.is_alive():
        return

    def _vuelta():
        time.sleep(30)
        while True:
            try:
                res = turno()
                movidos = sum(
                    (res.get(k) or {}).get("aplicado", 0) for k in ("local", "nodo")
                ) + int(res.get("al_nodo") or 0)
                if movidos:
                    _logger().info(f"[huella] clientes: {res}")
            except Exception as e:
                try:
                    _logger().warning(f"[huella] turno falló: {e}")
                except Exception:
                    pass
            _despertar.wait(pausa)
            _despertar.clear()

    _hilo = threading.Thread(target=_vuelta, name="huella_clientes", daemon=True)
    _hilo.start()
